from django import template
from django.contrib.sites.models import Site


register = template.Library()


@register.simple_tag(takes_context=True)
def site_url_prefix(context):
    return '%s://%s' % (context['request'].scheme, Site.objects.get_current().domain)
