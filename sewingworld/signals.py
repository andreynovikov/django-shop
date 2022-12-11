import logging

from celery import states
from celery.signals import before_task_publish, task_received

from django_celery_results.models import TaskResult


logger = logging.getLogger("django")


@before_task_publish.connect
def create_task_result_on_publish(sender=None, headers=None, body=None, **kwargs):
    if "task" not in headers:
        return

    TaskResult.objects.store_result(
        "application/json",
        "utf-8",
        headers["id"],
        None,
        states.PENDING,
        task_name=headers["task"],
        task_args=headers["argsrepr"],
        task_kwargs=headers["kwargsrepr"],
    )


@task_received.connect
def create_task_on_received(request, **kwargs):
    TaskResult.objects.store_result(
        request.content_type,
        "utf-8",
        request.task_id,
        None,
        states.RECEIVED,
        task_name=request.task_name,
        task_args=request.argsrepr,
        task_kwargs=request.kwargsrepr,
    )
