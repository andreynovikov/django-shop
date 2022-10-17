from django.db.models.signals import post_save
from django.dispatch import receiver

from shop.models import Integration, Product, Order

from .tasks import notify_product_stocks


@receiver(post_save, sender=Product, dispatch_uid='product_saved_ozon_receiver')
def product_saved(sender, **kwargs):
    product = kwargs['instance']
    integration = Integration.objects.get(utm_source='ozon')
    if integration in product.integrations.all():
        notify_product_stocks.delay(product.id)


@receiver(post_save, sender=Order, dispatch_uid='order_saved_ozon_receiver')
def order_saved(sender, **kwargs):
    order = kwargs['instance']

    if order.tracker.has_changed('status'):
        if not order.status:  # new order
            integration = Integration.objects.get(utm_source='ozon')
            for item in order.items.all():
                if integration in item.product.integrations.all():
                    notify_product_stocks.delay(item.product.id)

