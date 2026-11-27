USE_BLANK_CHOICE_DASH = True
DATA_UPLOAD_MAX_NUMBER_FIELDS = 6000

IMPORT_EXPORT_SKIP_ADMIN_LOG = True

MAX_TAG_LENGTH = 255

TWO_FACTOR_PATCH_ADMIN = True
TWO_FACTOR_SMS_GATEWAY = 'sewingworld.two_factor.Gateway'

SHOP_IMPORT_DIRECTORY = '/www/www.sewing-world.ru/import'

# The file manager browses MEDIA_ROOT. These folders hold the files of FileFields (their upload_to) and are
# read-only in it.
FILEMANAGER_PROTECTED = [
    'actions', 'blog', 'categories', 'contractors', 'logos', 'news', 'posters', 'products', 'stores',
]
# Apps and models whose text fields "where used" doesn't search: big tables without links.
FILEMANAGER_USAGE_EXCLUDE = ['admin', 'django_celery_beat', 'django_celery_results', 'errors', 'sessions']
