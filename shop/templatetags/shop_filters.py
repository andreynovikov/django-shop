from django import template
from django.template.defaultfilters import stringfilter
from django.utils.safestring import mark_safe
#from django.contrib.staticfiles import finders
from django.core.files.storage import default_storage

from shop.models import ShopUserManager, Currency


register = template.Library()

@register.filter
@stringfilter
def format_phone(value):
    result = ShopUserManager.format_phone(value)
    return mark_safe(result)


@register.filter
def file_exists(filepath):
    return default_storage.exists(filepath)
    #return finders.find(filepath)


@register.filter
def convert_price(value, arg):
    currency = Currency.objects.get(code=arg)
    return value / currency.rate
