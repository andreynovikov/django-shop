"""
Settings for tests, they fill in what a checkout without local setup lacks:

    python manage.py test tests --settings=tests.settings

Give the label, without it test discovery also walks into the libraries cloned to the project root.

Tests need a PostgreSQL role that can create databases. DATABASE_URL is taken from the environment, then .env,
and defaults to the current user on the local server, which can be allowed with ALTER ROLE <user> CREATEDB.
"""
import os
import sys
import types

import environ

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(TESTS_DIR)

environ.Env.read_env(os.path.join(PROJECT_DIR, '.env'))
for key, value in {
    'SECRET_KEY': 'tests',
    'DATABASE_URL': 'postgres:///shop',
    'CACHE_URL': 'locmemcache://',
    'ALLOWED_HOSTS': '*',
    'ALLOWED_ORIGINS': 'https://shop.test',
    'ROOT_URLCONF': 'sewingworld.urls',
    'CELERY_BROKER_URL': 'memory://',
    'ADMINS': 'admin:admin@shop.test',
    'LOGIN_URL': '/login/',
    'LOGIN_REDIRECT_URL': '/',
    'LOGOUT_URL': '/logout/',
    'DEFAULT_FROM_EMAIL': 'shop@shop.test',
    'SERVER_EMAIL': 'shop@shop.test',
    'CSRF_COOKIE_SAMESITE': 'Lax',
    'SESSION_COOKIE_SAMESITE': 'Lax',
}.items():
    os.environ.setdefault(key, value)

if not os.path.exists(os.path.join(PROJECT_DIR, 'sewingworld', 'settings', 'integrations.py')):
    sys.modules['sewingworld.settings.integrations'] = types.ModuleType('sewingworld.settings.integrations')

from sewingworld.settings import *  # noqa F401,F403,E402

LOGGING = {'version': 1, 'disable_existing_loggers': False}  # file handlers need logs/

SILENCED_SYSTEM_CHECKS = ['models.E034']  # shop_order_item_serial_number_idx is too long
