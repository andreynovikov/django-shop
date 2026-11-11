import os

import environ

env = environ.Env(
    # set casting, default value
    ADMIN=(bool, False),
    DEBUG=(bool, False),
    SITE_ID=(int, 1)
)

# Set the project base directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

# Take environment variables from .env file
env.read_env(os.path.join(BASE_DIR, '.env'))
IS_ADMIN_SITE = env('ADMIN')
if IS_ADMIN_SITE:
    env.read_env(os.path.join(BASE_DIR, '.env.admin'), overwrite=True)

SITE_ID = env('SITE_ID')

DEBUG = env('DEBUG')

SECRET_KEY = env('SECRET_KEY')

BLOCKED_IPS = []

DATABASES = {
    'default': {
        **env.db(engine='django_prometheus.db.backends.postgresql'),
        'CONN_MAX_AGE': 600,
    },
}
# The DBaaS server has lock_timeout = 1 ms, so that any wait for a row lock fails, and its settings are out of reach.
# Each connection sets its own, after any options of DATABASE_URL. backup_db passes it to pg_dump as PGOPTIONS.
_db_options = DATABASES['default'].setdefault('OPTIONS', {})
_db_options['options'] = ' '.join(filter(None, [_db_options.get('options'), '-c lock_timeout=5s']))

# python manage.py shell -c "from django.db import connection; c = connection.cursor(); c.execute('SHOW lock_timeout'); print(c.fetchone())"

CACHES = {
    'default': {
        **env.cache(backend='django_prometheus.cache.backends.memcached.PyLibMCCache'),
        'KEY_PREFIX': 'SW',
    },
    'files': {  # used for sitemap
        'BACKEND': 'django_prometheus.cache.backends.filebased.FileBasedCache',  # django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': os.path.join(BASE_DIR, '.cache'),
    },
}

CONN_MAX_AGE = 600
X_FRAME_OPTIONS = 'DENY'

INTERNAL_IPS = ['127.0.0.1', '::1']

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS')

ROOT_URLCONF = env('ROOT_URLCONF')

WSGI_APPLICATION = 'sewingworld.wsgi.application'

LANGUAGE_CODE = 'ru'
TIME_ZONE = 'Europe/Moscow'
USE_I18N = True
USE_THOUSAND_SEPARATOR = False
USE_TZ = True

from django.conf.locale.ru import formats as ru_formats  # noqa F402
ru_formats.DATETIME_FORMAT = "d.m.y H:i"
TIME_INPUT_FORMATS = [
    '%H:%M',        # '14:30'
    '%H:%M:%S',     # '14:30:59'
    '%H:%M:%S.%f',  # '14:30:59.000200'
]

STATIC_ROOT = os.path.join(BASE_DIR, 'static')
STATIC_URL = '/static/'
STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'staticfiles'),
)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates'),],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.media',
                'shop.context_processors.shop_info'
            ]
        }
    }
]
TEMPLATES[0]['OPTIONS']['debug'] = DEBUG

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
)

AUTH_USER_MODEL = 'shop.ShopUser'
# Length only: no rules on what a password consists of. Login keeps accepting older, shorter passwords.
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 8},
    },
]
LOGIN_REDIRECT_URL = env('LOGIN_REDIRECT_URL')
LOGIN_URL = env('LOGIN_URL')
LOGOUT_URL = env('LOGOUT_URL')

DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL')
SERVER_EMAIL = env('SERVER_EMAIL')

ADMINS = [x.split(':') for x in env.list('ADMINS')]
MANAGERS = ADMINS

# Origins of the storefronts, whose proxies forward the browser's Origin. Browsers never call the API host
# cross-origin, so there are no CORS settings.
CSRF_TRUSTED_ORIGINS = env.list('ALLOWED_ORIGINS')
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_AGE = 2419200  # 4 weeks
# __Host-sessionid and __Host-csrftoken keep pages on other subdomains from setting these cookies. Switch to them
# only when every storefront proxy reads the new CSRF cookie name; CookieRenameMiddleware moves visitors over.
SESSION_COOKIE_NAME = env('SESSION_COOKIE_NAME', default='sessionid')
CSRF_COOKIE_NAME = env('CSRF_COOKIE_NAME', default='csrftoken')

CELERY_BROKER_URL = env('CELERY_BROKER_URL')

MPTT_ROOT = 'sewing.world'

SERIALIZATION_MODULES = {
    'xml':    'django_tagulous.serializers.xml_serializer',
    'json':   'django_tagulous.serializers.json',
    'python': 'django_tagulous.serializers.python',
    'yaml':   'django_tagulous.serializers.pyyaml',
}

from .apps import *  # noqa F401
from .admin import *  # noqa F401
from .backup import *  # noqa F401
from .celery import *  # noqa F401
from .constance import *  # noqa F401
from .middleware import *  # noqa F401
from .prometheus import *  # noqa F401
from .drf import *  # noqa F401
from .reviews import *  # noqa F401
from .shop import *  # noqa F401
from .integrations import *  # noqa F401
from .logging import *  # noqa F401
