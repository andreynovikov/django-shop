from celery import shared_task

from shop import health


@shared_task(name='shop.tasks.heartbeat', ignore_result=True)
def heartbeat(queue):
    """
    Sent through each Celery queue by the check_health command (see shop/health.py): taking it is the queue's success.
    It stores no result, and sewingworld/signals.py records no PENDING or RECEIVED row for it either.
    """
    health.record_success(None, f'celery.{queue}')
