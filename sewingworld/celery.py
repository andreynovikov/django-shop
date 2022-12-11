from __future__ import absolute_import

import os
from celery import Celery
from django.conf import settings


PRIORITY_HIGHEST = 0
PRIORITY_HIGH = 2
PRIORITY_NORMAL = 4
PRIORITY_LOW = 6
PRIORITY_IDLE = 9

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sewingworld.settings.production')

app = Celery('sewingworld')

settings.CONN_MAX_AGE = 0
settings.DATABASES['default']['CONN_MAX_AGE'] = 0
# Using a string here means the worker will not have to
# pickle the object when using Windows.
app.config_from_object('django.conf:settings', namespace='CELERY')
app.conf.task_track_started = True
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
