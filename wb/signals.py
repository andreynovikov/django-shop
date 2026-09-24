import logging

from django.contrib.sites.models import Site
from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver

from sewingworld.tasks import PRIORITY_IDLE

from shop.models import Product, ProductIntegration, Integration

from .tasks import notify_product_stocks

logger = logging.getLogger('wb')


@receiver(post_save, sender=Product, dispatch_uid='product_saved_wb_receiver')
def product_saved(sender, **kwargs):
    product = kwargs['instance']
    if product.num >= 0:  # report new stock only if stock is reset (this disables double renew on stocks import)
        return

    for integration in product.integrations.filter(pk__in=Site.objects.get(domain='wildberries.ru').integrations.all()):
        if integration.settings.get('warehouse_id', 0) != 0:
            try:
                product_integration = ProductIntegration.objects.get(product=product, integration=integration)
                product_integration.notify_stock = True
                product_integration.save()
            except:
                pass


@receiver(m2m_changed, sender=Product.integrations.through, dispatch_uid='product_integration_changed_wb_receiver')
def product_integration_changed(sender, **kwargs):  # used to clean remote warehouse if product is removed from integration
    product = kwargs.get('instance', None)
    if product is None:
        return
    if kwargs.get('action', None) == 'post_remove':
        for integration in Integration.objects.filter(pk__in=kwargs.get('pk_set', []), site__domain='wildberries.ru'):
            if integration.settings.get('warehouse_id', '') != '':
                notify_product_stocks.s([product.id], integration.utm_source, True).apply_async(priority=PRIORITY_IDLE)
