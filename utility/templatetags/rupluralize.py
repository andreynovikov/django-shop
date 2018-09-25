from django import template
from django.template.defaultfilters import stringfilter


register=template.Library()

# pluralize for russian language
# {{someval|rupluralize:"товар,товара,товаров"}}
@register.filter(is_safe = False)
@stringfilter
def rupluralize(value, arg):
    bits = arg.split(u',')
    try:
        value = str( 0 if not value or int(value) <= 0 else value )[-1:]
        return bits[ 0 if value=='1' else (1 if value in '234' else 2) ]
    except:
        raise template.TemplateSyntaxError
    return ''
