# Database backups made by `manage.py backup_db` into a restic repository, see "Database backups" in DEPLOYMENT.rst.
# The repository and its password come from restic's own variables in .env (RESTIC_REPOSITORY, RESTIC_PASSWORD_FILE),
# which settings/__init__.py loads into the environment that restic inherits.
DB_BACKUP = {
    # restic --host of database snapshots, the database name by default. Run the timer in one deployment per database.
    'HOST': None,
    # An hourly run makes a full dump at this local hour, or later if that run was missed, otherwise a hot one.
    'FULL_HOUR': 3,
    # A full dump is also made when the last one is older than this, or the migrations changed since.
    'FULL_MAX_AGE_HOURS': 25,
    # Hot dumps hold only these models' rows, their auto-created many-to-many tables included.
    'HOT_MODELS': ['shop.Order', 'shop.OrderItem', 'shop.Box', 'shop.ShopUser', 'shop.Serial', 'shop.Favorites'],
    # Full dumps keep the schema of these apps but skip their rows.
    'EXCLUDE_DATA_APPS': ['errors', 'django_celery_results'],
    # pg_dump patterns for tables outside the Django registry whose rows are skipped too.
    'EXCLUDE_DATA_TABLES': [],
    'PG_DUMP': 'pg_dump',
    'RESTIC': 'restic',
    # Files with secrets saved with every full dump or by --kind config, relative to BASE_DIR. Missing ones are skipped.
    'CONFIG_FILES': ['.env', '.env.admin', 'sewingworld/settings/integrations.py'],
    # restic --host of config snapshots, the project directory name by default, so that each deployment has its own.
    'CONFIG_HOST': None,
}
