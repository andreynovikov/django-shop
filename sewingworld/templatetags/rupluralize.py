from django import template
from django.template.defaultfilters import stringfilter


register = template.Library()

# pluralize for russian language
# {{someval|rupluralize:"товар,товара,товаров"}}
@register.filter(is_safe=False)
@stringfilter
def rupluralize(value, endings):
    try:
        endings = endings.split(',')
        value = int(value)
        if value % 100 in (11, 12, 13, 14):
            return endings[2]
        if value % 10 == 1:
            return endings[0]
        if value % 10 in (2, 3, 4):
            return endings[1]
        else:
            return endings[2]
    except Exception as e:
        raise template.TemplateSyntaxError(str(e))
