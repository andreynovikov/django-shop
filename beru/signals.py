from django.contrib.sites.models import Site
from django.db.models.signals import post_save
from django.dispatch import receiver

from shop.models import Order

from .tasks import notify_beru_order_status


@receiver(post_save, sender=Order, dispatch_uid='order_saved_beru_receiver')
def order_saved(sender, **kwargs):
    order = kwargs['instance']
    print("Post save emited for", order)

    if order.site != Site.objects.get(domain='beru.ru'):
        return

    if order.tracker.has_changed('status'):
        if order.status == Order.STATUS_COLLECTED:
            notify_beru_order_status.delay(order.id, 'PROCESSING', 'READY_TO_SHIP')
        if order.status == Order.STATUS_SENT:
            notify_beru_order_status.delay(order.id, 'PROCESSING', 'SHIPPED')
