from django.conf import settings
from django import template

from shop.models import Order


register = template.Library()


@register.assignment_tag(takes_context=True)
def get_unpaid_order(context):
    """
    Находит последний собранный и неоплаченный заказ, который можно
    оплатить онлайн.
    """
    if context.request.user.is_authenticated():
        orders = Order.objects.order_by('-id').filter(user=context.request.user.id)
        for order in orders:
            if order.status == Order.STATUS_COLLECTED and not order.paid and \
                    (order.payment in [Order.PAYMENT_CARD, Order.PAYMENT_TRANSFER, Order.PAYMENT_CREDIT]):
                return order
    return None
