from django.core import management

from celery import shared_task


@shared_task
def django_clearsessions():
    """Cleanup expired sessions by using Django management command."""
    management.call_command("clearsessions", verbosity=1)


# Task priorities are switched off: apply_async(priority=None) leaves the priority to Celery's default.
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
