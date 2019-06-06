from django import template
from django.template.defaultfilters import stringfilter


register=template.Library()

# remove substring from string
@register.filter(is_safe = False)
@stringfilter
def remove(value, arg):
    return value.replace(arg, '')
