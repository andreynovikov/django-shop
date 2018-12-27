from django.conf import settings
from django import template
from django.db.models.query import QuerySet
from django.contrib.sites.models import Site

from shop.models import Category


register = template.Library()


@register.simple_tag(takes_context=True)
def site_url_prefix(context):
    return '%s://%s' % (context['request'].scheme, Site.objects.get_current().domain)


@register.simple_tag
def get_categories_root():
    try:
        return Category.objects.get(slug=settings.MPTT_ROOT)
    except Category.DoesNotExist:
        return None


@register.simple_tag
def get_class_name(ref):
    return ref.__class__.__name__


@register.filter
def filter_qs(queryset, field):
    if isinstance(queryset, QuerySet):
        kwargs = {field: True}
        return queryset.filter(**kwargs)
    else:
        return None


@register.filter
def get_dict_item(dictionary, key):
    return dictionary.get(key)
