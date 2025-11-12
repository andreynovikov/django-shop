import logging

from django.contrib.sites.models import Site
from django.db.models.signals import post_save
from django.dispatch import receiver

from shop.models import Product, ProductIntegration, Integration


logger = logging.getLogger('ozon')
SITE_OZON = Site.objects.get(domain='ozon.ru')


@receiver(post_save, sender=Product, dispatch_uid='product_saved_ozon_receiver')
def product_saved(sender, **kwargs):
    product = kwargs['instance']
    if product.num >= 0:  # report new stock only if stock is reset (this disables double renew on stocks import)
        return

    for integration in product.integrations.filter(pk__in=SITE_OZON.integrations.all()):
        try:
            product_integration = ProductIntegration.objects.get(product=product, integration=integration)
            product_integration.notify_stock = True
            product_integration.save()
        except:
            pass
