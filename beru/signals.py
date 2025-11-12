import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from sewingworld.tasks import PRIORITY_IDLE

from shop.models import Product, ProductIntegration, Order

from .tasks import notify_beru_order_status

logger = logging.getLogger('beru')


@receiver(post_save, sender=Product, dispatch_uid='product_saved_beru_receiver')
def product_saved(sender, **kwargs):
    product = kwargs['instance']
    if product.num >= 0:  # report new stock only if stock is reset (this disables double renew on stocks import)
        return

    for integration in product.integrations.filter(settings__has_key='ym_campaign'):
        if integration.settings.get('warehouse_id', '') != '':
            logger.info('### ' + integration.settings.get('warehouse_id', '') + " " + product.article + " " + str(product.num))
            try:
                product_integration = ProductIntegration.objects.get(product=product, integration=integration)
                product_integration.notify_stock = True
                product_integration.save()
            except:
                pass

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
