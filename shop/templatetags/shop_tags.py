import re
import barcode as bc

from django import template
from django.utils.safestring import mark_safe

from shop.models import Order


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


@register.simple_tag
def barcode(number, fmt='code128', width=0.5, height=15):
    """
    Генерирует SVG с штрихкодом из числа.
    """
    if fmt == 'ean13':
        number = '{:012d}'.format(number)
    CODE = bc.get_barcode_class(fmt)
    code = CODE(str(number)).render(writer_options={'module_width': width, 'module_height': height, 'compress': True}).decode()
    code = re.sub(r'^.*(?=<svg)', '', code)
    return mark_safe(code)
