import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from sewingworld.celery import PRIORITY_IDLE

from shop.models import Integration, Product, OrderItem

from .tasks import notify_product_stocks


logger = logging.getLogger('ozon')


@receiver(post_save, sender=Product, dispatch_uid='product_saved_ozon_receiver')
def product_saved(sender, **kwargs):
    product = kwargs['instance']
    if product.num >= 0:  # report new stock only if stock is reset (this disables double renew on stocks import)
        return

    integration = Integration.objects.get(utm_source='ozon')
    if integration in product.integrations.all():
        notify_product_stocks.s(product.id).apply_async(priority=PRIORITY_IDLE)


@receiver(post_save, sender=OrderItem, dispatch_uid='order_item_saved_ozon_receiver')
def order_item_saved(sender, **kwargs):
    """ This is redundant as product stock is reset on quantity change """
    order_item = kwargs['instance']
    if order_item.tracker.has_changed('quantity'):
        integration = Integration.objects.get(utm_source='ozon')
        if integration in order_item.product.integrations.all():
            notify_product_stocks.s(order_item.product.id).apply_async(priority=PRIORITY_IDLE)
