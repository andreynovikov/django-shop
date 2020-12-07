from django import template

from shop.models import Order, Favorites


register = template.Library()


@register.simple_tag(takes_context=True)
def get_unpaid_order(context):
    """
    Находит последний собранный и неоплаченный заказ, который можно
    оплатить онлайн.
    """
    if hasattr(context, 'request') and context.request.user.is_authenticated:
        orders = Order.objects.order_by('-id').filter(user=context.request.user.id)
        for order in orders:
            if order.status == Order.STATUS_COLLECTED and not order.paid and \
                    (order.payment in [Order.PAYMENT_CARD, Order.PAYMENT_TRANSFER, Order.PAYMENT_CREDIT]):
                return order
    return None


@register.simple_tag(takes_context=True)
def get_order_count(context):
    if hasattr(context, 'request') and context.request.user.is_authenticated:
        return Order.objects.filter(user=context.request.user.id).count()
    return 0


@register.simple_tag(takes_context=True)
def get_favorites_count(context):
    if hasattr(context, 'request') and context.request.user.is_authenticated:
        return Favorites.objects.filter(user=context.request.user.id).count()
    return 0
