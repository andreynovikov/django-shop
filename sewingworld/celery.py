from __future__ import absolute_import

import os
import __main__ as main
from celery import Celery
from django.conf import settings

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sewingworld.settings.production')

app = Celery('sewingworld')

# modify settings only if executing celery worker
if hasattr(main, '__file__') and 'celery' in main.__file__:
    settings.CONN_MAX_AGE = 0
    settings.DATABASES['default']['CONN_MAX_AGE'] = 0
    settings.PROMETHEUS_METRICS_EXPORT_PORT = None
    settings.PROMETHEUS_METRICS_EXPORT_PORT_RANGE = None

# Using a string here means the worker will not have to
# pickle the object when using Windows.
app.config_from_object('django.conf:settings', namespace='CELERY')
app.conf.task_track_started = True
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
