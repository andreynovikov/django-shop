from django.contrib.sites.models import Site
from django.db.models.signals import post_save
from django.dispatch import receiver

from shop.models import Order

from .tasks import confirm_sber_order, reject_sber_order, \
    notify_sber_order_packed, notify_sber_order_shipped, \
    get_sber_order_details


SITE_SBER = Site.objects.get(domain='sbermegamarket.ru')


@receiver(post_save, sender=Order, dispatch_uid='order_saved_sber_receiver')
def order_saved(sender, **kwargs):
    order = kwargs['instance']

    if order.site != SITE_SBER:
        return

    if order.tracker.has_changed('status'):
        if order.status == Order.STATUS_ACCEPTED:
            confirm_sber_order.delay(order.id)
            get_sber_order_details.delay(order.id)  # дату доставки можно получить только из расширенной информации о заказе
        if order.status == Order.STATUS_CANCELED:
            reject_sber_order.delay(order.id)
        if order.status == Order.STATUS_COLLECTED:
            notify_sber_order_packed.delay(order.id)
        if order.status == Order.STATUS_SENT:
            notify_sber_order_shipped.delay(order.id)
