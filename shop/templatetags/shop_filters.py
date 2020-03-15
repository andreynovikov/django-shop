from django import template
from django.template.defaultfilters import stringfilter
from django.utils.safestring import mark_safe
from django.contrib.staticfiles import finders
from django.core.files.storage import default_storage

from shop.models import ShopUserManager, Order


register = template.Library()


@register.filter
@stringfilter
def format_phone(value):
    result = ShopUserManager.format_phone(value)
    return mark_safe(result)


@register.filter
def file_exists(filepath):
    return default_storage.exists(filepath)


@register.filter
def static_file_exists(filepath):
    return finders.find(filepath) is not None


@register.filter
def order_color(status):
    # badge colors from https://demo.createx.studio/cartzilla/components/badge.html
    # 'danger' is currently unused
    if status == Order.STATUS_NEW:
        return 'info'
    elif status in (Order.STATUS_ACCEPTED, Order.STATUS_COLLECTING, Order.STATUS_COLLECTED, Order.STATUS_OTHERSHOP, Order.STATUS_SENT, Order.STATUS_DELIVERED_STORE):
        return 'accent'
    elif status in (Order.STATUS_DELIVERED, Order.STATUS_DELIVERED_SHOP):
        return 'primary'
    elif status in (Order.STATUS_DONE, Order.STATUS_FINISHED):
        return 'success'
    elif status in (Order.STATUS_PROBLEM, Order.STATUS_UNCLAIMED, Order.STATUS_SERVICE):
        return 'warning'
    elif status in (Order.STATUS_FROZEN, Order.STATUS_CONSULTATION, Order.STATUS_RETURNING):
        return 'dark'
    elif status == Order.STATUS_CANCELED:
        return 'secondary'
    else:
        return 'light'
