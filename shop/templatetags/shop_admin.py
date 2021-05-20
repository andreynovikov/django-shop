from django import template

from shop.admin.product import product_stock_view
from shop.models import Order

register = template.Library()


@register.simple_tag
def product_stock(product, order=None):
    return product_stock_view(product, order)


@register.simple_tag
def get_alert_orders():
    return Order.objects.filter(alert__gt='').order_by('-id')
