from django.db.models.signals import post_save
from django.dispatch import receiver

from sewingworld.tasks import PRIORITY_IDLE

from shop.models import Product, Order, OrderItem

from .tasks import notify_beru_order_status, notify_beru_product_stocks


@receiver(post_save, sender=Product, dispatch_uid='product_saved_beru_receiver')
def product_saved(sender, **kwargs):
    product = kwargs['instance']
    if product.num >= 0:  # report new stock only if stock is reset (this disables double renew on stocks import)
        return

    for integration in product.integrations.filter(settings__has_key='ym_campaign'):
        if integration.settings.get('warehouse_id', '') != '':
            notify_beru_product_stocks.s([product.id], integration.utm_source).apply_async(priority=PRIORITY_IDLE, countdown=900)  # wait 15 minutes for import to finish


@receiver(post_save, sender=OrderItem, dispatch_uid='order_item_saved_beru_receiver')
def order_item_saved(sender, **kwargs):
    """ This is redundant as product stock is reset on quantity change """
    order_item = kwargs['instance']
    if order_item.tracker.has_changed('quantity'):
        for integration in order_item.product.integrations.filter(settings__has_key='ym_campaign'):
            if integration.settings.get('warehouse_id', '') != '':
                notify_beru_product_stocks.s([order_item.product.id], integration.utm_source).apply_async(priority=PRIORITY_IDLE, countdown=900)


@receiver(post_save, sender=Order, dispatch_uid='order_saved_beru_receiver')
def order_saved(sender, **kwargs):
    order = kwargs['instance']

    if not order.integration or not order.integration.uses_api or \
       not order.integration.settings or order.integration.settings.get('ym_campaign', None) is None:
        return

    if order.tracker.has_changed('status'):
        if order.status == Order.STATUS_COLLECTED:
            notify_beru_order_status.delay(order.id, 'PROCESSING', 'READY_TO_SHIP')
        if order.status == Order.STATUS_SENT:
            notify_beru_order_status.delay(order.id, 'PROCESSING', 'SHIPPED')
