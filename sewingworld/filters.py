"""
Parameters of the product list in the API, and the facets that the storefronts show: a category names the filters
of its page in Category.filters, and the list of its products brings their choices and ranges.
"""
import math
import re
from dataclasses import dataclass
from decimal import Decimal
from typing import Callable

from django import forms
from django.contrib.postgres.search import SearchQuery, SearchRank
from django.db import models
from django.db.models import F, Max, Min, Q
from django.utils.text import capfirst

import django_filters
from django_filters import rest_framework as filters
from django_filters.widgets import QueryArrayWidget

from drf_spectacular.utils import extend_schema_field

from shop.models import Category, Manufacturer, Product

BOOLEAN_FIELDS = [field.name for field in Product._meta.fields if isinstance(field, models.BooleanField)]

SHUTTLE_TYPES = (
    ('горизонтальный', 'Горизонтальный вращающийся'),
    ('качающийся', 'Вертикальный качающийся (колеблющийся)'),
    ('двойного', 'Вертикальный вращающийся'),
)


class TypedFilter:
    """ A filter of this type in the API schema, described there by its label as other filters are """
    schema = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        extend_schema_field({**self.schema, 'description': kwargs.get('label')})(self)


class NumberListField(forms.Field):
    """ Whole numbers of a repeated parameter, id=1&id=2 """
    widget = QueryArrayWidget

    def to_python(self, value):
        try:
            return [int(item) for item in value or []]
        except ValueError:
            raise forms.ValidationError('Not a number', code='invalid')


class NumberListFilter(TypedFilter, django_filters.Filter):
    """ Products with any of the values """
    field_class = NumberListField
    schema = {'type': 'array', 'items': {'type': 'integer'}}

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('lookup_expr', 'in')
        super().__init__(*args, **kwargs)


class IntegerFilter(TypedFilter, django_filters.NumberFilter):
    field_class = forms.IntegerField
    schema = {'type': 'integer'}


class RangeField(forms.CharField):
    """ Bounds of a range as the storefronts send them, price=1000-5000 """
    def to_python(self, value):
        value = super().to_python(value)
        if not value:
            return None
        match = re.fullmatch(r'(\d+(?:\.\d+)?)-(\d+(?:\.\d+)?)', value)
        if match is None:
            raise forms.ValidationError('Not a range', code='invalid')
        return Decimal(match[1]), Decimal(match[2])


class RangeFilter(TypedFilter, django_filters.Filter):
    field_class = RangeField
    schema = {'type': 'string', 'pattern': r'^\d+(\.\d+)?-\d+(\.\d+)?$', 'example': '1000-5000'}

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('lookup_expr', 'range')
        super().__init__(*args, **kwargs)


class ExactCharField(forms.CharField):
    """ Tells an empty value from a missing one """
    def to_python(self, value):
        return None if value is None else super().to_python(value)


class ExactCharFilter(django_filters.CharFilter):
    """ Unlike other filters, an empty value filters too: variations= finds the products without variations """
    field_class = ExactCharField

    def filter(self, qs, value):
        if value is None:
            return qs
        return qs.filter(**{f'{self.field_name}__{self.lookup_expr}': value})


class ProductFilterSet(filters.FilterSet):
    """ The parameters that the product list takes, any other is ignored """
    id = NumberListFilter(field_name='pk')
    text = django_filters.CharFilter(method='search', label='Full text search: the best matches first, with their rank')
    title = django_filters.CharFilter(lookup_expr='icontains', label='Part of the title')
    instock = IntegerFilter(method='filter_instock', label='1 for products in stock, 0 for those out of stock')
    categories = IntegerFilter(field_name='categories', label='Products right in the category; the list brings the facets of its filters')
    in_category = NumberListFilter(method='filter_in_categories', label='Products in the categories or in their active subcategories')
    kind = NumberListFilter(method='filter_kinds')
    manufacturer = NumberListFilter()
    variations = ExactCharFilter(label='Variations of the product, empty for products without them')
    price = RangeFilter(label='Lowest and highest price')
    sm_power = django_filters.NumberFilter(lookup_expr='gt')
    sm_stitchquantity = IntegerFilter(lookup_expr='gt')
    sm_shuttletype = django_filters.ChoiceFilter(choices=SHUTTLE_TYPES, lookup_expr='icontains')

    class Meta:
        model = Product
        fields = BOOLEAN_FIELDS

    def search(self, queryset, name, value):
        query = SearchQuery(value, config='russian')
        rank = SearchRank(F('fts_vector'), query, weights=[0.1, 0.2, 0.4, 1.0])
        return queryset.annotate(rank=rank).filter(fts_vector=query, rank__gte=0.001).order_by('-enabled', '-rank')

    def filter_instock(self, queryset, name, value):
        return queryset.filter(num__gt=0) if value > 0 else queryset.filter(num=0)

    def filter_in_categories(self, queryset, name, value):
        # categories asked for, even inactive ones, and their active descendants; unknown ones find no products
        categories = Category.objects.filter(pk__in=value)
        categories = Category.objects.get_queryset_descendants(categories, include_self=True).filter(Q(active=True) | Q(pk__in=value))
        # a subquery: a join repeats the products that are in several of the categories
        in_categories = Product.categories.through.objects.filter(category__in=categories)
        return queryset.filter(pk__in=in_categories.values('product_id'))

    def filter_kinds(self, queryset, name, value):
        of_kinds = Product.kind.through.objects.filter(productkind__in=value)
        return queryset.filter(pk__in=of_kinds.values('product_id'))

    def facets(self):
        """
        Choices and ranges of the filters that the category asked for shows, or of those of a search, in the products
        that the other parameters find: the filters picked do not narrow what they offer.
        """
        data = self.form.cleaned_data
        names = []
        if data.get('categories') is not None:
            category = Category.objects.filter(pk=data['categories']).only('filters').first()
            if category is not None:
                names = category_filter_names(category)
        if not names and data.get('text'):
            names = SEARCH_FACETS
        if not names:
            return None

        products = self.queryset.all()
        for name, value in data.items():
            if name not in names:
                products = self.filters[name].filter(products, value)
        return {name: FACETS.get(name, BOOLEAN_FACET).values(name, products) for name in names}


def manufacturer_choices(products):
    # order_by(): the ordering of a product search would add its columns to the subquery
    manufacturers = Manufacturer.objects.filter(pk__in=products.order_by().values('manufacturer_id'))
    return sorted(((manufacturer.pk, str(manufacturer)) for manufacturer in manufacturers), key=lambda choice: choice[1])


PRICE_STEP = 5000


def price_range(products):
    """ Lowest and highest price of the products in whole steps of the slider, as wide as it gets when there are none """
    prices = products.aggregate(low=Min('price'), high=Max('price'))
    low, high = (0, 1000000) if prices['low'] is None else (prices['low'], prices['high'])
    return {
        'step': PRICE_STEP,
        'min_value': PRICE_STEP * math.floor(low / PRICE_STEP),
        'max_value': PRICE_STEP * math.ceil(high / PRICE_STEP),
    }


@dataclass(frozen=True)
class Facet:
    """
    A filter as the storefronts show it. They pick its control by `field_class`, or by `widget` for the sliders:
    names of the Django form fields and widgets that the filters were once rendered with. A comma in the label
    is followed by the unit.
    """
    field_class: str
    widget: str
    label: str | None = None  # verbose name of the field when None
    choices: Callable | None = None  # of the products
    attrs: Callable | None = None  # of the products, the bounds and step of a slider

    def describe(self, name):
        label, _, unit = (self.label or capfirst(Product._meta.get_field(name).verbose_name)).partition(',')
        description = {'name': name, 'id': f'id_{name}', 'class': self.field_class, 'label': label, 'widget': self.widget}
        if unit:
            description['unit'] = unit.strip()
        return description

    def values(self, name, products):
        values = {'id': f'id_{name}'}
        if self.choices is not None:
            values['choices'] = self.choices(products)
        if self.attrs is not None:
            values['attrs'] = self.attrs(products)
        return values


def slider(step, min_value, max_value):
    return lambda products: {'step': step, 'min_value': min_value, 'max_value': max_value}


# What Category.filters may name, besides the boolean fields of Product
FACETS = {
    'manufacturer': Facet('MultipleChoiceField', 'SelectMultiple', choices=manufacturer_choices),
    'sm_shuttletype': Facet('ChoiceField', 'Select', choices=lambda products: [('', '- - не важно - -'), *SHUTTLE_TYPES]),
    'price': Facet('RangeField', 'ShopRangeWidget', attrs=price_range),
    'sm_power': Facet('DecimalField', 'ShopSliderWidget', 'Потребляемая мощность больше, Вт', attrs=slider(10, 20, 100)),
    'sm_stitchquantity': Facet('DecimalField', 'ShopSliderWidget', 'Количество строчек больше', attrs=slider(10, 0, 250)),
}
BOOLEAN_FACET = Facet('NullBooleanField', 'ShopBooleanWidget')
SEARCH_FACETS = ['manufacturer', 'price']


def category_filter_names(category):
    """ Filters of the category's page; storefronts pick enabled products themselves, unknown names are skipped """
    names = [name.strip() for name in category.filters.split(',')]
    return [name for name in names if name in FACETS or (name in BOOLEAN_FIELDS and name != 'enabled')]


def category_filters(category):
    """ What the storefronts show for each filter of the category's page, None when it has none """
    return [FACETS.get(name, BOOLEAN_FACET).describe(name) for name in category_filter_names(category)] or None
