import re
import barcode as bc

from django import template
from django.utils.safestring import mark_safe

from shop import health
from shop.models import Favorites, ImportRun, Order


register = template.Library()


@register.simple_tag(takes_context=True)
def get_unpaid_order(context):
    """
    Find the latest packed, unpaid order that can be paid online.
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


@register.simple_tag
def barcode(number, fmt='code128', width=0.5, height=15):
    """
    Render a number as an SVG barcode.
    """
    if fmt == 'ean13':
        number = '{:012d}'.format(number)
    CODE = bc.get_barcode_class(fmt)
    code = CODE(str(number)).render(writer_options={'module_width': width, 'module_height': height, 'compress': True}).decode()
    code = re.sub(r'^.*(?=<svg)', '', code)
    return mark_safe(code)


@register.simple_tag
def import_status():
    """ The 1C import's state for the admin's top bar, see ImportRun.status() """
    return ImportRun.status()


@register.simple_tag(takes_context=True)
def health_status(context):
    """
    The indicators of the admin's top bar by group, with their names, see health.summary(); None for those who may
    not see them
    """
    request = context.get('request')
    user = getattr(request, 'user', None)
    if user is None or not user.has_perm('shop.view_healthcheck'):
        return None
    return [{'group': group, 'name': name, **health.summary(group)} for group, name in health.GROUPS.items()]
