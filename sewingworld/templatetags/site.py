from django.conf import settings
from django import template
from django.db.models.query import QuerySet
from django.contrib.sites.models import Site
from django.utils.text import capfirst

from shop.models import Category


register = template.Library()


@register.simple_tag(takes_context=True)
def site_url_prefix(context):
    return '%s://%s' % (context['request'].scheme, Site.objects.get_current().domain)


@register.simple_tag
def get_object(model_name, pk):
    from django.apps import apps
    app, name = model_name.split('.', 1)
    model = apps.get_model(app_label=app, model_name=name)
    return model.objects.get(pk=int(pk))


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
        criteria = True
        if field[0] == '!':
            criteria = False
            field = field[1:]
        kwargs = {field: criteria}
        return queryset.filter(**kwargs)
    else:
        return None


@register.filter
def filter_qs_by_pk(queryset, ids):
    if isinstance(queryset, QuerySet):
        exclude = False
        if ids[0] == '!':
            exclude = True
            ids = ids[1:]
        kwargs = {'pk__in': ids.split(',')}
        if exclude:
            return queryset.exclude(**kwargs)
        else:
            return queryset.filter(**kwargs)
    else:
        return None


@register.filter
def get_unique_mapped_list(queryset, dictionary):
    return set(filter(lambda pk: pk is not None, [dictionary.get(o.pk, None) for o in queryset]))


@register.filter
def get_dict_item(dictionary, key):
    return dictionary.get(key)


@register.filter
def get_list_item(dictionary, idx):
    return dictionary[idx]


@register.filter
def get_field(object, key):
    return getattr(object, key)


@register.filter
def get_field_name(object, key):
    field = object._meta.get_field(key)
    return capfirst(field.verbose_name) if hasattr(field, 'verbose_name') else capfirst(field.name)


@register.filter
def parse_field_name(name):
    parts = name.split(',')
    if len(parts) == 1:
        return parts[0], ''
    return parts


@register.filter
def fields_with_values(fields, object):
    for field in fields:
        value = get_field(object, field)
        if value:
            yield field, value


@register.filter
def prettify(value):
    if isinstance(value, float):
        if value % 1 == 0:
            return int(value)
        return value
    if isinstance(value, str):
        return value.strip()
    return value


@register.simple_tag
def query_transform(request, **kwargs):
    updated = request.GET.copy()
    for k, v in kwargs.items():
        updated[k] = v
    return updated.urlencode()


@register.filter
def rebootstrap(value):
    if not isinstance(value, str):
        return value
    value = value.replace('col-md-8', 'col-md-4')
    value = value.replace('col-md-10', 'col-md-5')
    value = value.replace('col-md-12', 'col-md-6')
    value = value.replace('<h3>', '<h5>')
    value = value.replace('</h3>', '</h5>')
    value = value.replace('<h4>', '<h6>')
    value = value.replace('</h4>', '</h6>')
    return value


@register.filter
def from_months(value):
    if value == 0:
        return 'нет'
    if value == 1:
        return '1 месяц'
    if value < 5:
        return '{} месяца'.format(value)
    if value < 12:
        return '{} месяцев'.format(value)

    months = ''
    if value % 12 != 0:
        months = ' {}'.format(from_months(value % 12))

    years = int(value / 12)

    year = 'лет'
    if years % 10 == 1:
        year = 'год'
    elif years % 10 in (2, 3, 4):
        year = 'года'
    else:
        year = 'лет'

    return '{} {}{}'.format(years, year, months)


@register.filter
def ya_days(value):
    years = int(value / 12)
    months = value % 12
    result = ['P']
    if years > 0:
        result.append('{}Y'.format(years))
    if months > 0:
        result.append('{}M'.format(months))
    return ''.join(result)
