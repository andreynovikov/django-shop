from django import template

from shop.admin import product_stock_view


register = template.Library()


@register.simple_tag
def product_stock(product, order=None):
    return product_stock_view(product, order)
