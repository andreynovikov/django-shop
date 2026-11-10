"""
Back up the database into a restic repository. A systemd timer runs it hourly, see "Database backups" in DEPLOYMENT.rst.

Each run saves one snapshot of pg_dump output in the custom format:

* full: the whole database with its schema, except the rows of DB_BACKUP EXCLUDE_DATA_APPS and EXCLUDE_DATA_TABLES;
* hot: only the rows of DB_BACKUP HOT_MODELS, which deploy/backup/restore.sh lays over the full dump made before.

--kind auto makes a full dump once a day at FULL_HOUR or the first run after it, when the last full one is older than
FULL_MAX_AGE_HOURS, or when the migrations changed since it, as hot rows only fit the schema of their full dump.
Otherwise it makes a hot one. A full run also saves DB_BACKUP CONFIG_FILES, and --kind config saves only them.

The repository is append-only for this server, so retention and pruning are done on the backup host by
deploy/backup/maintain.sh.
"""
import hashlib
import json
import logging
import os
import shlex
import subprocess
import tempfile
from contextlib import contextmanager
from datetime import timedelta

from django.apps import apps
from django.conf import settings
from django.core.mail import mail_admins
from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from django.db.migrations.recorder import MigrationRecorder
from django.utils import timezone
from django.utils.dateparse import parse_datetime

log = logging.getLogger('backup')

# libpq variables for the connection settings, the password goes to a passfile to keep it out of the environment
PG_ENV = {'HOST': 'PGHOST', 'PORT': 'PGPORT', 'USER': 'PGUSER', 'NAME': 'PGDATABASE'}
PG_OPTIONS_ENV = {
    'sslmode': 'PGSSLMODE',
    'sslrootcert': 'PGSSLROOTCERT',
    'sslcert': 'PGSSLCERT',
    'sslkey': 'PGSSLKEY',
    'sslcrl': 'PGSSLCRL',
    'connect_timeout': 'PGCONNECT_TIMEOUT',
    'target_session_attrs': 'PGTARGETSESSIONATTRS',
    'options': 'PGOPTIONS',
}
RESTIC_PASSWORD_VARS = ('RESTIC_PASSWORD', 'RESTIC_PASSWORD_FILE', 'RESTIC_PASSWORD_COMMAND')
# a run waits this long for the backup host to finish pruning, which locks the repository
RESTIC_RETRY_LOCK = '1h'


class ResticError(CommandError):
    def __init__(self, cmd, result):
        lines = result.stderr.strip().splitlines()[-30:]
        lines += [line for line in result.stdout.splitlines() if '"message_type":"error"' in line][-10:]
        super().__init__('%s exited with %d:\n%s' % (shlex.join(cmd), result.returncode, '\n'.join(lines)))


def unique(items):
    return list(dict.fromkeys(items))


def quote(table):
    """A pg_dump pattern that matches only this table name."""
    return '"%s"' % table.replace('"', '""')


def model_tables(model):
    """The tables with a model's rows: its own, its parents' and their auto-created many-to-many ones."""
    tables = []
    for model in [model, *model._meta.get_parent_list()]:
        tables.append(model._meta.db_table)
        tables += [
            field.remote_field.through._meta.db_table for field in model._meta.local_many_to_many
            if field.remote_field.through._meta.auto_created
        ]
    return tables


def hot_tables(labels):
    tables = []
    for label in labels:
        try:
            model = apps.get_model(label)
        except (LookupError, ValueError):
            raise CommandError('DB_BACKUP HOT_MODELS: there is no model %s' % label)
        tables += model_tables(model)
    return unique(tables)


def app_tables(labels):
    tables = []
    for label in labels:
        try:
            app = apps.get_app_config(label)
        except LookupError:
            raise CommandError('DB_BACKUP EXCLUDE_DATA_APPS: there is no app %s' % label)
        tables += [model._meta.db_table for model in app.get_models(include_auto_created=True) if not model._meta.proxy]
    return unique(tables)


def schema_tag():
    """A tag that changes with the applied migrations, so that a hot dump is laid only over a full one of its schema."""
    migrations = MigrationRecorder.Migration.objects.order_by('app', 'name').values_list('app', 'name')
    digest = hashlib.sha256('\n'.join('%s.%s' % migration for migration in migrations).encode()).hexdigest()
    return 'schema:' + digest[:12]


def snapshot_time(snapshot):
    taken = parse_datetime(snapshot['time'])
    if taken is None:
        raise CommandError('Cannot read the time of restic snapshot %s: %s' % (snapshot.get('id'), snapshot['time']))
    return taken


def choose_kind(last_full, schema, now, full_hour, max_age):
    """
    The kind of snapshot an automatic run makes and why. last_full is restic's latest full snapshot or None, schema
    the current schema_tag().
    """
    if last_full is None:
        return 'full', 'there is no full snapshot yet'
    if schema not in last_full.get('tags', []):
        return 'full', 'the migrations changed since the last full snapshot'
    taken = snapshot_time(last_full)
    if now - taken > max_age:
        return 'full', 'the last full snapshot is older than %s' % max_age
    now, taken = timezone.localtime(now), timezone.localtime(taken)
    if now.hour >= full_hour and taken.date() < now.date():
        return 'full', 'the daily full snapshot is due'
    return 'hot', 'the last full snapshot is from %s' % taken.strftime('%Y-%m-%d %H:%M')


def check_environment(env):
    missing = []
    if not (env.get('RESTIC_REPOSITORY') or env.get('RESTIC_REPOSITORY_FILE')):
        missing.append('RESTIC_REPOSITORY')
    if not any(env.get(name) for name in RESTIC_PASSWORD_VARS):
        missing.append('RESTIC_PASSWORD_FILE')
    if missing:
        raise CommandError('Set %s in .env, see "Database backups" in DEPLOYMENT.rst' % ' and '.join(missing))


@contextmanager
def pg_environment(db):
    """The environment for libpq tools to connect as Django does. The password is in a passfile, not in the command."""
    env = dict(os.environ)
    for key, name in PG_ENV.items():
        if db.get(key):
            env[name] = str(db[key])
    options = db.get('OPTIONS') or {}
    for key, name in PG_OPTIONS_ENV.items():
        if options.get(key) is not None:
            env[name] = str(options[key])
    if not db.get('PASSWORD'):
        yield env
        return
    with tempfile.NamedTemporaryFile('w', prefix='pgpass.') as passfile:  # created with mode 0600, as libpq wants
        passfile.write('*:*:*:*:%s\n' % db['PASSWORD'].replace('\\', '\\\\').replace(':', '\\:'))
        passfile.flush()
        env.pop('PGPASSWORD', None)
        env['PGPASSFILE'] = passfile.name
        yield env


def size(count):
    return '%.1f MiB' % (count / 2 ** 20)


class Command(BaseCommand):
    help = 'Back up the database into the restic repository, see "Database backups" in DEPLOYMENT.rst'

    def add_arguments(self, parser):
        parser.add_argument('--kind', choices=('auto', 'full', 'hot', 'config'), default='auto',
                            help='auto picks full or hot (default), config saves only DB_BACKUP CONFIG_FILES')
        parser.add_argument('--dry-run', action='store_true', help='print the commands to run and exit')

    def handle(self, *args, kind, dry_run, **options):
        self.conf = settings.DB_BACKUP
        self.dry_run = dry_run
        self.verbosity = options['verbosity']
        try:
            self.backup(kind)
        except Exception as e:
            if not dry_run:
                log.exception('Backup failed')
                mail_admins('Database backup failed', '%s\n\nSee logs/backup.log for details.' % e, fail_silently=True)
            if isinstance(e, CommandError):
                raise
            raise CommandError('Backup failed: %r' % e) from e

    def backup(self, kind):
        check_environment(os.environ)
        db = connection.settings_dict
        with pg_environment(db) as self.env:
            if kind != 'config':
                host = self.conf['HOST'] or db['NAME']
                schema = schema_tag()
                if kind == 'auto':
                    kind, reason = choose_kind(
                        self.last_full(host), schema, timezone.now(), self.conf['FULL_HOUR'],
                        timedelta(hours=self.conf['FULL_MAX_AGE_HOURS']),
                    )
                    self.report('%s snapshot: %s' % (kind, reason))
                self.dump(kind, host, schema)
            if kind in ('full', 'config'):
                self.save_config()

    def dump(self, kind, host, schema):
        pg_dump = [self.conf['PG_DUMP'], '--format=custom', '--compress=0']  # restic compresses, and deduplicates only plain data
        if kind == 'full':
            excluded = [quote(table) for table in app_tables(self.conf['EXCLUDE_DATA_APPS'])]
            pg_dump += ['--exclude-table-data=%s' % pattern for pattern in excluded + list(self.conf['EXCLUDE_DATA_TABLES'])]
        else:
            pg_dump += ['--data-only', '--strict-names']
            pg_dump += ['--table=%s' % quote(table) for table in hot_tables(self.conf['HOT_MODELS'])]
        # With --stdin-from-command restic saves no snapshot when pg_dump fails
        self.restic_backup(host, [kind, schema], ['--stdin-filename', '%s.pgdump' % kind, '--stdin-from-command', '--', *pg_dump])

    def save_config(self):
        base = os.path.abspath(settings.BASE_DIR)
        paths = [path for path in (os.path.join(base, name) for name in self.conf['CONFIG_FILES']) if os.path.exists(path)]
        if not paths:
            log.warning('None of DB_BACKUP CONFIG_FILES exists')
            self.stderr.write('None of DB_BACKUP CONFIG_FILES exists, config is not saved')
            return
        self.restic_backup(self.conf['CONFIG_HOST'] or os.path.basename(base), ['config'], ['--', *paths])

    def last_full(self, host):
        result = self.restic('snapshots', '--json', '--host', host, '--tag', 'full', '--latest', '1')
        snapshots = json.loads(result.stdout or '[]')
        return max(snapshots, key=snapshot_time) if snapshots else None

    def restic_backup(self, host, tags, args):
        cmd = ['backup', '--json', '--retry-lock', RESTIC_RETRY_LOCK, '--host', host, *('--tag=%s' % tag for tag in tags), *args]
        if self.dry_run:
            self.stdout.write(shlex.join([self.conf['RESTIC'], *cmd]))
            return
        summary = {}
        for line in self.restic(*cmd).stdout.splitlines():
            message = json.loads(line) if line.startswith('{') else {}
            if message.get('message_type') == 'summary':
                summary = message
        self.report('%s snapshot %s of %s saved in %.0f s, %s added' % (
            tags[0], summary.get('snapshot_id', '?')[:8], host, summary.get('total_duration', 0),
            size(summary.get('data_added', 0)),
        ))

    def restic(self, *args):
        cmd = [self.conf['RESTIC'], *args]
        result = subprocess.run(cmd, env=self.env, stdin=subprocess.DEVNULL, capture_output=True, text=True)
        if result.returncode:
            raise ResticError(cmd, result)
        return result

    def report(self, message):
        log.info(message)
        if self.verbosity:
            self.stdout.write(message)
