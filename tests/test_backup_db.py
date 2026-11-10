"""
The backup_db command and deploy/backup/restore.sh. See settings.py on how to run. RestoreTests need restic, jq and
the PostgreSQL client tools, and are skipped without them.
"""
import json
import os
import shutil
import stat
import subprocess
import tempfile
from datetime import datetime, timedelta
from io import StringIO
from unittest import mock, skipUnless
from zoneinfo import ZoneInfo

from django.conf import settings
from django.contrib.sites.models import Site
from django.core import mail
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import connection
from django.test import SimpleTestCase, TestCase, TransactionTestCase, override_settings
from django.utils import timezone

from sewingworld.management.commands.backup_db import (
    app_tables, choose_kind, hot_tables, pg_environment, quote, schema_tag,
)
from shop.models import Order, ShopUser

MSK = ZoneInfo('Europe/Moscow')
UTC = ZoneInfo('UTC')
RESTORE_SH = os.path.join(settings.BASE_DIR, 'deploy', 'backup', 'restore.sh')
RESTIC_ENV = {'RESTIC_REPOSITORY': '/backup/repo', 'RESTIC_PASSWORD': 'repo password'}


def restic_time(moment):
    """A snapshot time as restic writes it, with nanoseconds and the local offset."""
    return moment.astimezone(MSK).strftime('%Y-%m-%dT%H:%M:%S.123456789+03:00')


def snapshot(moment, schema='schema:abc'):
    return {'id': 'f' * 64, 'time': restic_time(moment), 'tags': ['full', schema]}


class TablesTests(SimpleTestCase):
    def test_hot_tables_add_auto_created_many_to_many(self):
        tables = hot_tables(['shop.ShopUser'])
        self.assertEqual(tables, ['shop_shopuser', 'shop_shopuser_groups', 'shop_shopuser_user_permissions'])

    def test_hot_tables_skip_explicit_through_models(self):
        tables = hot_tables(['shop.Product'])
        self.assertIn('shop_product_sites', tables)
        self.assertIn('shop_product_categories', tables)
        self.assertNotIn('shop_stock', tables)  # Product.stock goes through the Stock model, a table of its own

    def test_default_hot_models_exist(self):
        tables = hot_tables(settings.DB_BACKUP['HOT_MODELS'])
        self.assertIn('shop_order', tables)
        self.assertIn('shop_orderitem', tables)

    def test_unknown_model(self):
        for label in ('shop.Nothing', 'nothing'):
            with self.assertRaisesMessage(CommandError, 'no model %s' % label):
                hot_tables([label])

    def test_app_tables(self):
        self.assertEqual(app_tables(['errors']), ['errors_error', 'errors_errortrace'])
        with self.assertRaisesMessage(CommandError, 'no app nothing'):
            app_tables(['nothing'])

    def test_quote(self):
        self.assertEqual(quote('shop_order'), '"shop_order"')
        self.assertEqual(quote('odd"name'), '"odd""name"')


class ChooseKindTests(SimpleTestCase):
    max_age = timedelta(hours=25)

    def choose(self, last_full, now, schema='schema:abc'):
        return choose_kind(last_full, schema, now.astimezone(UTC), 3, self.max_age)[0]

    def test_first_run(self):
        self.assertEqual(self.choose(None, datetime(2026, 11, 10, 14, tzinfo=MSK)), 'full')

    def test_schema_changed(self):
        now = datetime(2026, 11, 10, 14, tzinfo=MSK)
        self.assertEqual(self.choose(snapshot(now - timedelta(hours=1)), now, schema='schema:new'), 'full')

    def test_too_old(self):
        now = datetime(2026, 11, 10, 2, tzinfo=MSK)
        self.assertEqual(self.choose(snapshot(now - timedelta(hours=26)), now), 'full')

    def test_daily(self):
        last_full = snapshot(datetime(2026, 11, 9, 3, 0, 5, tzinfo=MSK))
        self.assertEqual(self.choose(last_full, datetime(2026, 11, 10, 2, tzinfo=MSK)), 'hot')
        self.assertEqual(self.choose(last_full, datetime(2026, 11, 10, 3, tzinfo=MSK)), 'full')
        self.assertEqual(self.choose(last_full, datetime(2026, 11, 10, 4, tzinfo=MSK)), 'full')  # the 03:00 run failed

    def test_after_daily(self):
        last_full = snapshot(datetime(2026, 11, 10, 3, 0, 5, tzinfo=MSK))
        self.assertEqual(self.choose(last_full, datetime(2026, 11, 10, 4, tzinfo=MSK)), 'hot')
        self.assertEqual(self.choose(last_full, datetime(2026, 11, 10, 23, tzinfo=MSK)), 'hot')


class PgEnvironmentTests(SimpleTestCase):
    db = {'HOST': 'db.local', 'PORT': 5433, 'USER': 'shop', 'NAME': 'sworld', 'PASSWORD': '',
          'OPTIONS': {'sslmode': 'require', 'pool': True}}

    def test_connection(self):
        with pg_environment(self.db) as env:
            self.assertEqual(env['PGHOST'], 'db.local')
            self.assertEqual(env['PGPORT'], '5433')
            self.assertEqual(env['PGDATABASE'], 'sworld')
            self.assertEqual(env['PGSSLMODE'], 'require')
            self.assertNotIn('PGPASSFILE', env)

    def test_password_goes_to_passfile(self):
        with mock.patch.dict(os.environ, {'PGPASSWORD': 'stale'}):
            with pg_environment({**self.db, 'PASSWORD': r'pa:ss\word'}) as env:
                path = env['PGPASSFILE']
                with open(path) as passfile:
                    self.assertEqual(passfile.read(), '*:*:*:*:pa\\:ss\\\\word\n')
                self.assertEqual(stat.S_IMODE(os.stat(path).st_mode), 0o600)
                self.assertNotIn('PGPASSWORD', env)
                self.assertNotIn('pa:ss', ' '.join(env.values()))
        self.assertFalse(os.path.exists(path))


class FakeRestic:
    """Stands in for subprocess.run, answers restic as the command expects and remembers the calls."""

    def __init__(self, snapshots=(), fail=None):
        self.snapshots = list(snapshots)
        self.fail = fail
        self.calls = []

    def __call__(self, cmd, env, **kwargs):
        passfile = env.get('PGPASSFILE')
        with open(passfile) if passfile else StringIO() as f:
            self.calls.append({'cmd': cmd, 'env': env, 'passfile': f.read()})
        if cmd[1] == 'snapshots':
            return subprocess.CompletedProcess(cmd, 0, json.dumps(self.snapshots), '')
        if self.fail:
            return subprocess.CompletedProcess(cmd, 1, '', self.fail)
        summary = {'message_type': 'summary', 'snapshot_id': 'abcd1234' * 8, 'data_added': 3 * 2 ** 20, 'total_duration': 4.2}
        return subprocess.CompletedProcess(cmd, 0, '{"message_type":"status"}\n%s\n' % json.dumps(summary), '')

    def backups(self):
        return [call['cmd'] for call in self.calls if call['cmd'][1] == 'backup']


@mock.patch.dict(os.environ, RESTIC_ENV)
class CommandTests(TestCase):
    def setUp(self):
        config = tempfile.NamedTemporaryFile('w', suffix='.env')
        self.addCleanup(config.close)
        self.config = config.name
        conf = {**settings.DB_BACKUP, 'HOST': 'sworld', 'CONFIG_FILES': [self.config, 'no-such-file'], 'CONFIG_HOST': 'site'}
        patcher = override_settings(DB_BACKUP=conf)
        patcher.enable()
        self.addCleanup(patcher.disable)

    def run_command(self, restic, **options):
        out = StringIO()
        with mock.patch('sewingworld.management.commands.backup_db.subprocess.run', restic):
            call_command('backup_db', stdout=out, stderr=StringIO(), **options)
        return out.getvalue()

    def test_first_run_is_full_with_config(self):
        restic = FakeRestic()
        out = self.run_command(restic)
        full, config = restic.backups()
        self.assertEqual(full[full.index('--host') + 1], 'sworld')
        self.assertIn('--tag=full', full)
        self.assertIn('--tag=%s' % schema_tag(), full)
        self.assertEqual(full[full.index('--stdin-filename') + 1], 'full.pgdump')
        pg_dump = full[full.index('--') + 1:]
        self.assertEqual(pg_dump[:3], ['pg_dump', '--format=custom', '--compress=0'])
        self.assertIn('--exclude-table-data="errors_error"', pg_dump)
        self.assertIn('--exclude-table-data="django_celery_results_taskresult"', pg_dump)
        self.assertNotIn('--data-only', pg_dump)
        self.assertEqual(config[config.index('--host') + 1], 'site')
        self.assertIn('--tag=config', config)
        self.assertEqual(config[config.index('--') + 1:], [self.config])
        self.assertIn('full snapshot: there is no full snapshot yet', out)
        self.assertIn('full snapshot abcd1234 of sworld saved in 4 s, 3.0 MiB added', out)

    def test_fresh_full_makes_hot(self):
        restic = FakeRestic([snapshot(timezone.now(), schema_tag())])
        self.run_command(restic)
        [hot] = restic.backups()
        self.assertIn('--tag=hot', hot)
        pg_dump = hot[hot.index('--') + 1:]
        self.assertIn('--data-only', pg_dump)
        self.assertIn('--strict-names', pg_dump)
        self.assertIn('--table="shop_order"', pg_dump)
        self.assertIn('--table="shop_shopuser_groups"', pg_dump)
        snapshots = restic.calls[0]['cmd']
        self.assertEqual(snapshots[1:], ['snapshots', '--json', '--host', 'sworld', '--tag', 'full', '--latest', '1'])

    def test_config_only(self):
        restic = FakeRestic()
        self.run_command(restic, kind='config')
        [config] = [call['cmd'] for call in restic.calls]
        self.assertIn('--tag=config', config)

    def test_password_stays_out_of_the_command(self):
        restic = FakeRestic()
        with mock.patch.dict(connection.settings_dict, {'PASSWORD': 's3cr:et'}):
            self.run_command(restic, kind='full')
        for call in restic.calls:
            self.assertNotIn('s3cr', ' '.join(call['cmd']))
            self.assertEqual(call['passfile'], '*:*:*:*:s3cr\\:et\n')
            self.assertEqual(call['env']['RESTIC_REPOSITORY'], '/backup/repo')

    def test_dry_run(self):
        restic = FakeRestic()
        out = self.run_command(restic, kind='full', dry_run=True)
        self.assertEqual(restic.calls, [])
        self.assertIn('--stdin-from-command -- pg_dump --format=custom', out)
        self.assertEqual(mail.outbox, [])

    def test_failure_is_mailed(self):
        restic = FakeRestic(fail='pg_dump: error: connection to server failed\nFatal: command failed')
        with self.assertRaisesMessage(CommandError, 'connection to server failed'), self.assertLogs('backup', 'ERROR'):
            self.run_command(restic, kind='hot')
        [message] = mail.outbox
        self.assertIn('Database backup failed', message.subject)
        self.assertIn('connection to server failed', message.body)

    def test_missing_repository(self):
        with mock.patch.dict(os.environ):
            del os.environ['RESTIC_REPOSITORY']
            with self.assertRaisesMessage(CommandError, 'Set RESTIC_REPOSITORY in .env'), self.assertLogs('backup', 'ERROR'):
                self.run_command(FakeRestic())
        self.assertEqual(len(mail.outbox), 1)


@skipUnless(all(shutil.which(tool) for tool in ('restic', 'jq', 'pg_dump', 'pg_restore', 'createdb')),
            'needs restic, jq and the PostgreSQL client tools')
class RestoreTests(TransactionTestCase):
    """A full and a hot snapshot into a real repository, restored by restore.sh into a database next to the test one."""
    serialized_rollback = True

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = tmp.name
        self.config = os.path.join(self.tmp, 'integrations.py')
        with open(self.config, 'w') as f:
            f.write('SECRET = "kept"\n')
        env = {'RESTIC_REPOSITORY': os.path.join(self.tmp, 'repo'), 'RESTIC_PASSWORD': 'test', 'RESTIC_CACHE_DIR': os.path.join(self.tmp, 'cache')}
        environment = mock.patch.dict(os.environ, env)
        environment.start()
        self.addCleanup(environment.stop)
        conf = override_settings(DB_BACKUP={**settings.DB_BACKUP, 'HOST': 'test', 'CONFIG_FILES': [self.config], 'CONFIG_HOST': 'site'})
        conf.enable()
        self.addCleanup(conf.disable)
        subprocess.run(['restic', 'init'], check=True, capture_output=True)

    def backup(self, kind):
        call_command('backup_db', kind=kind, stdout=StringIO())

    def restore(self, target, *options):
        self.addCleanup(self.drop, target)
        with pg_environment(connection.settings_dict) as env:
            result = subprocess.run([RESTORE_SH, '--host', 'test', '--target', target, *options], env=env, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stderr

    def drop(self, database):
        with pg_environment(connection.settings_dict) as env:
            subprocess.run(['dropdb', '--if-exists', database], env=env, capture_output=True)

    def query(self, database, sql):
        with pg_environment({**connection.settings_dict, 'NAME': database}) as env:
            return subprocess.run(['psql', '-X', '-At', '-c', sql], env=env, capture_output=True, text=True, check=True).stdout

    def test_restore_lays_hot_rows_over_full_dump(self):
        site = Site.objects.get_current()
        first = Order.objects.create(user=ShopUser.objects.create(phone='+79161234567'), site=site)
        self.backup('full')
        Order.objects.filter(pk=first.pk).update(status=Order.STATUS_ACCEPTED)
        second = Order.objects.create(user=ShopUser.objects.create(phone='+79161234568'), site=site)
        self.backup('hot')

        target = connection.settings_dict['NAME'] + '_restore'
        log = self.restore(target)
        self.assertIn('== hot data', log)
        self.assertEqual(self.query(target, 'SELECT id, status FROM shop_order ORDER BY id'),
                         '%d|%d\n%d|%d\n' % (first.pk, Order.STATUS_ACCEPTED, second.pk, Order.STATUS_NEW))
        self.assertEqual(self.query(target, "SELECT last_value FROM shop_order_id_seq"), '%d\n' % second.pk)

        log = self.restore(connection.settings_dict['NAME'] + '_verify', '--verify')
        self.assertIn('public.shop_order: 2 rows', log)

        config = subprocess.run(['restic', 'dump', '--host', 'site', '--tag', 'config', 'latest', self.config],
                                capture_output=True, text=True, check=True)
        self.assertEqual(config.stdout, 'SECRET = "kept"\n')
