from __future__ import absolute_import

from django.core import management

from celery import shared_task


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


@shared_task
def haystack_update_index():
    management.call_command("update_index", verbosity=1)
