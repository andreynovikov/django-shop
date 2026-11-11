from django.db.models.signals import post_save
from django.dispatch import receiver

from shop.models import Order

from .tasks import confirm_sber_order, reject_sber_order, \
    notify_sber_order_packed, notify_sber_order_shipped, \
    get_sber_order_details


@receiver(post_save, sender=Order, dispatch_uid='order_saved_sber_receiver')
def order_saved(sender, **kwargs):
    """ Tasks wait for the commit: the admin saves the items and boxes after the order, in save_related() """
    order = kwargs['instance']

    if order.site.domain != 'sbermegamarket.ru':
        return

    if order.tracker.has_changed('status'):
        if order.status == Order.STATUS_ACCEPTED:
            confirm_sber_order.delay_on_commit(order.id)
            get_sber_order_details.delay_on_commit(order.id)  # дату доставки можно получить только из расширенной информации о заказе
        if order.status == Order.STATUS_CANCELED:
            reject_sber_order.delay_on_commit(order.id)
        if order.status == Order.STATUS_COLLECTED:
            notify_sber_order_packed.delay_on_commit(order.id)
        if order.status == Order.STATUS_SENT:
            notify_sber_order_shipped.delay_on_commit(order.id)
