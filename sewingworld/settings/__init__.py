import os

import environ

from django.conf import global_settings

env = environ.Env(
    # set casting, default value
    DEBUG=(bool, False),
    SITE_ID=(int, 1)
)

# Set the project base directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

# Take environment variables from .env file
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

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
SESSION_COOKIE_AGE = 2419200  # 4 weeks
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

INTERNAL_IPS = ['127.0.0.1', '::1']

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS')

ROOT_URLCONF = env('ROOT_URLCONF')

WSGI_APPLICATION = 'sewingworld.wsgi.application'

DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

LANGUAGE_CODE = 'ru'
TIME_ZONE = 'Europe/Moscow'
USE_I18N = True
USE_L10N = True
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

STAFF_REQUIRED_URLS = (
    r'/wiki/(.*)$',
)

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
                'sekizai.context_processors.sekizai',
                'djconfig.context_processors.config',
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
LOGIN_REDIRECT_URL = env('LOGIN_REDIRECT_URL')
LOGIN_URL = env('LOGIN_URL')
LOGOUT_URL = env('LOGOUT_URL')

DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL')
SERVER_EMAIL = env('SERVER_EMAIL')

ADMINS = [x.split(':') for x in env.list('ADMINS')]
MANAGERS = ADMINS

from corsheaders.defaults import default_headers  # noqa F402

CORS_ALLOW_HEADERS = [
    *default_headers,
    'x-session',
]
CORS_EXPOSE_HEADERS = [
    'x-csrftoken',
    'x-session'
]
CORS_ALLOWED_ORIGINS = env.list('ALLOWED_ORIGINS')
CORS_ALLOW_CREDENTIALS = True
CSRF_TRUSTED_ORIGINS = CORS_ALLOWED_ORIGINS
CSRF_COOKIE_SAMESITE = env('CSRF_COOKIE_SAMESITE')
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SAMESITE = env('SESSION_COOKIE_SAMESITE')
SESSION_COOKIE_SECURE = True

CELERY_BROKER_URL = env('CELERY_BROKER_URL')

MPTT_ROOT = 'sewing.world'

WIKI_ACCOUNT_HANDLING = False
THUMBNAIL_KVSTORE = 'sorl.thumbnail.kvstores.redis_kvstore.KVStore'
THUMBNAIL_REDIS_DB = 0

SERIALIZATION_MODULES = {
    'xml':    'tagulous.serializers.xml_serializer',
    'json':   'tagulous.serializers.json',
    'python': 'tagulous.serializers.python',
    'yaml':   'tagulous.serializers.pyyaml',
}

from .apps import *  # noqa F401
from .admin import *  # noqa F401
from .celery import *  # noqa F401
from .filters import *  # noqa F401
from .middleware import *  # noqa F401
from .prometheus import *  # noqa F401
from .drf import *  # noqa F401
from .reviews import *  # noqa F401
from .shop import *  # noqa F401
from .integrations import *  # noqa F401
from .logging import *  # noqa F401
