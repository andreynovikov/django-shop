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

DATABASES = {
    'default': env.db()
}

CACHES = {
    'default': {
        **env.cache(),
        'KEY_PREFIX': 'SW'
    },
    # read os.environ['REDIS_URL']
    # 'redis': env.cache_url('REDIS_URL')
}

CONN_MAX_AGE = 600
X_FRAME_OPTIONS = 'DENY'
SESSION_COOKIE_AGE = 2419200 # 4 weeks
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

from django.conf.locale.ru import formats as ru_formats
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
        'DIRS': [os.path.join(BASE_DIR,  'templates'),],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.media',
                # 'sekizai.context_processors.sekizai',
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

DEFAULT_FROM_EMAIL = env('LOGOUT_URL')
SERVER_EMAIL = env('LOGOUT_URL')

ADMINS = [x.split(':') for x in env.list('ADMINS')]
MANAGERS = ADMINS

from corsheaders.defaults import default_headers

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
THUMBNAIL_REDIS_DB = env.int('THUMBNAIL_REDIS_DB')

from .apps import *
from .middleware import *
from .celery import *
from .admin import *
from .filters import *
from .reviews import *
from .shop import *
from .unisender import *
from .logging import *
