import sys

from django.core.signals import got_request_exception
from django.dispatch import receiver

from .middleware import remember_exception
from .recorder import record_task

try:
    from celery.signals import task_failure
except ImportError:  # Celery is optional
    task_failure = None


@receiver(got_request_exception)
def exception_raised(sender, request=None, **kwargs):
    """
    Django sends it for every exception it turns into a 500, inside the except block. process_exception of
    ErrorCaptureMiddleware sees only the exceptions of views, this one also those of middlewares.
    """
    if request is not None:
        remember_exception(request, sys.exc_info()[1], replace=False)


def task_failed(sender=None, task_id=None, exception=None, traceback=None, **kwargs):
    """
    Sent when a task fails for good, not when it is retried. Celery clears the traceback right after it, so the
    frames are read here.
    """
    if sender is not None and exception is not None:
        record_task(sender, task_id, exception, traceback)


if task_failure is not None:
    task_failure.connect(task_failed, weak=False, dispatch_uid='errors.task_failed')
