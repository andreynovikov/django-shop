from __future__ import absolute_import

import functools

from django.core import management
from django.core.cache import cache

from celery import shared_task


def single_instance_task(timeout):
    def task_exc(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            lock_id = "celery-single-instance-" + func.__name__
            if cache.add(lock_id, "true", timeout):
                try:
                    return func(*args, **kwargs)
                finally:
                    cache.delete(lock_id)
        return wrapper
    return task_exc


@shared_task
def django_clearsessions():
    """Cleanup expired sessions by using Django management command."""
    management.call_command("clearsessions", verbosity=1)


@shared_task
def zinnia_count_discussions():
    management.call_command("count_discussions", verbosity=1)


@shared_task
def zinnia_spam_cleanup():
    management.call_command("spam_cleanup", verbosity=1)


# PRIORITY_HIGHEST = 0
# PRIORITY_HIGH = 2
# PRIORITY_NORMAL = 4
# PRIORITY_LOW = 6
# PRIORITY_IDLE = 9
PRIORITY_HIGHEST = None
PRIORITY_HIGH = None
PRIORITY_NORMAL = None
PRIORITY_LOW = None
PRIORITY_IDLE = None
