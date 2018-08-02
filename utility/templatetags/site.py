from django.conf import settings
from django import template
from django.contrib.sites.models import Site

from shop.models import Category


register = template.Library()


@register.simple_tag(takes_context=True)
def site_url_prefix(context):
    return '%s://%s' % (context['request'].scheme, Site.objects.get_current().domain)


@register.assignment_tag
def get_categories_root():
    return Category.objects.get(slug=settings.MPTT_ROOT)


@register.assignment_tag
def get_class_name(ref):
    return ref.__class__.__name__


@register.filter
def get_dict_item(dictionary, key):
    return dictionary.get(key)
