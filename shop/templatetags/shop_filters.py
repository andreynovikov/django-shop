from django import template
from django.template.defaultfilters import stringfilter
from django.utils.safestring import mark_safe
from django.contrib.staticfiles import finders
from django.core.files.storage import default_storage

from shop.models import ShopUserManager


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
