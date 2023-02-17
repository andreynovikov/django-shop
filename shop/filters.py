import math
from collections import OrderedDict

from django import forms
from django.conf import settings
from django.db import models

import django_filters
from django_filters.widgets import SuffixedMultiWidget

from shop.models import Product, Category, Manufacturer


class ShopBooleanWidget(forms.CheckboxInput):
    def value_from_datadict(self, data, files, name):
        if name not in data:
            return None
        value = data.get(name)
        # Translate true and false strings to boolean values.
        values = {'true': True, 'false': False, '1': True, '0': False}
        if isinstance(value, str):
            value = values.get(value.lower(), value)
        return bool(value)

    def value_omitted_from_data(self, data, files, name):
        return None


def num(s):
    if s is None or s == '':
        return None
    try:
        return int(s)
    except ValueError:
        try:
            return float(s)
        except ValueError:
            return None


class ShopSliderWidget(forms.TextInput):
    template_name = 'shop/widgets/sliderwidget.html'

    # def value_from_datadict(self, data, files, name):
    #     return [
    #         num(widget.value_from_datadict(data, files, self.suffixed(name, suffix)))
    #         for widget, suffix in zip(self.widgets, self.suffixes)
    #         ]
    # def value_from_datadict(self, data, files, name):
    #     print("vfd %s" % str(data), file=sys.stderr)
    #     return super().value_from_datadict(data, files, name)

    def setRange(self, min_value, max_value):
        step = self.attrs.get('step', 1)
        self.attrs.update({
                'min_value': step * math.floor(min_value / step),
                'max_value': step * math.ceil(max_value / step)
                })


class ShopRangeWidget(SuffixedMultiWidget):
    template_name = 'shop/widgets/rangewidget.html'
    suffixes = ['min', 'max']

    def __init__(self, attrs=None):
        widgets = (forms.TextInput, forms.TextInput)
        super(ShopRangeWidget, self).__init__(widgets, attrs)

    def value_from_datadict(self, data, files, name):
        return [
            num(widget.value_from_datadict(data, files, self.suffixed(name, suffix)))
            for widget, suffix in zip(self.widgets, self.suffixes)
        ]

    # def value_from_datadict(self, data, files, name):
    #     print("vfd %s" % str(data), file=sys.stderr)
    #     return super().value_from_datadict(data, files, name)

    def setRange(self, min_value, max_value):
        step = self.attrs.get('step', 1)
        self.attrs.update({
            'min_value': step * math.floor(min_value / step),
            'max_value': step * math.ceil(max_value / step)
        })


class PriceWidget(ShopRangeWidget):
    template_name = 'shop/widgets/cz_price_range.html'


def categories(request):
    categories = {}
    root = Category.objects.get(slug=settings.MPTT_ROOT)
    if request is None:
        for category in root.get_children():
            categories[category.pk] = str(category)
    else:
        for product in request.qs.iterator():
            category = product.categories.filter(tree_id=root.tree_id, active=True).order_by('hidden', '-level', 'lft').first()
            if category:
                ancestors = category.get_ancestors(include_self=True)
                categories[ancestors[1].pk] = str(ancestors[1])

    categories = [(k, categories[k]) for k in sorted(categories, key=categories.get)]
    return categories


def manufacturers(request):
    manufacturers = {}
    if request is None:
        for manufacturer in Manufacturer.objects.all().iterator():
            manufacturers[manufacturer.pk] = str(manufacturer)
    else:
        for product in request.qs.iterator():
            manufacturers[product.manufacturer.pk] = str(product.manufacturer)

    manufacturers = [(k, manufacturers[k]) for k in sorted(manufacturers, key=manufacturers.get)]
    return manufacturers


class ShopChoiceFilter(django_filters.ChoiceFilter):
    def __init__(self, *args, **kwargs):
        self.choices = kwargs.pop('choices')
        super(ShopChoiceFilter, self).__init__(*args, **kwargs)

    def get_request(self):
        try:
            return self.parent.request
        except AttributeError:
            return None

    def get_choices(self, request):
        choices = self.choices
        if callable(choices):
            return choices(request)
        return choices

    @property
    def field(self):
        request = self.get_request()
        choices = self.get_choices(request)

        if choices is not None:
            self.extra['choices'] = choices

        return super().field


class ShopMultipleChoiceFilter(django_filters.MultipleChoiceFilter):
    def __init__(self, *args, **kwargs):
        self.choices = kwargs.pop('choices')
        super(ShopMultipleChoiceFilter, self).__init__(*args, **kwargs)

    def get_request(self):
        try:
            return self.parent.request
        except AttributeError:
            return None

    def get_choices(self, request):
        choices = self.choices
        if callable(choices):
            return choices(request)
        return choices

    @property
    def field(self):
        request = self.get_request()
        choices = self.get_choices(request)

        if choices is not None:
            self.extra['choices'] = choices

        return super().field


class MultipleChoiceWidget(forms.widgets.ChoiceWidget):
    allow_multiple_selected = True
    template_name = 'shop/widgets/cz_filter.html'


shuttles = (
    ('горизонтальный', 'Горизонтальный вращающийся'),
    ('качающийся', 'Вертикальный качающийся (колеблющийся)'),
    ('двойного', 'Вертикальный вращающийся'),
)


class BaseProductFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(lookup_expr='icontains')
    # sm_dualtransporter_bool = django_filters.BooleanFilter(widget=BooleanWidget)
    # sm_autobuttonhole_bool = django_filters.BooleanFilter(widget=BooleanWidget)
    # sm_power = django_filters.NumberFilter(lookup_expr='gt')
    sm_power = django_filters.NumberFilter(widget=ShopSliderWidget(attrs={'step': 10, 'min_value': 20, 'max_value': 100}), lookup_expr='gt', label='Потребляемая мощность больше, Вт')
    sm_stitchquantity = django_filters.NumberFilter(widget=ShopSliderWidget(attrs={'step': 10, 'min_value': 0, 'max_value': 250}), lookup_expr='gt')
    price = django_filters.RangeFilter(widget=PriceWidget(attrs={'step': 10, }))
    categories = ShopMultipleChoiceFilter(widget=MultipleChoiceWidget(), choices=categories)
    manufacturer = ShopMultipleChoiceFilter(widget=MultipleChoiceWidget(), choices=manufacturers)
    sm_shuttletype = django_filters.ChoiceFilter(choices=shuttles, empty_label='не важно', lookup_expr='icontains')

    def __init__(self, data=None, *args, **kwargs):
        fields = kwargs.pop('fields')
        super(BaseProductFilter, self).__init__(data, *args, **kwargs)
        self.filters = OrderedDict([(name, filter) for name, filter in self.filters.items() if name in fields])


class BaseProductMetaclass:
    model = Product
    filter_overrides = {
        models.BooleanField: {
            'filter_class': django_filters.BooleanFilter,
            'extra': lambda f: {
                'widget': ShopBooleanWidget,
            },
        },
    }


def get_product_filter(data=None, *args, **kwargs):
    #if '_div_' in kwargs['fields']:
    #    kwargs['fields'] = tuple(x for x in kwargs['fields'] if x != '_div_')
    # get a mutable copy of the QueryDict
    data = data.copy()
    price_min = 1000000000
    price_max = 0
    if 'price' in kwargs['fields']:
        if not data.get('price_max'):
            data['_initial'] = True
        for product in kwargs['queryset'].iterator():
            if product.price < price_min:
                price_min = int(product.price)
            if product.price > price_max:
                price_max = int(product.price)

    if kwargs['request']:
        request = kwargs['request']
        request.qs = kwargs['queryset']

    meta = type('Meta', (BaseProductMetaclass,), {'fields': kwargs['fields']})
    filter_class = type('ProductFilterSet', (BaseProductFilter,), {'Meta': meta})
    product_filter = filter_class(data, *args, **kwargs)

    if 'price' in kwargs['fields']:
        if price_min <= price_max:
            product_filter.form.fields['price'].widget.setRange(price_min, price_max)
            #product_filter.filters['price'].field.widget.setRange(price_min, price_max)
        else:
            product_filter.form.fields['price'].widget.setRange(0, 700000)  # todo: find proper max price

        if not data.get('price_max'):
            price_min = 1000000000
            price_max = 0
            for product in product_filter.qs.iterator():
                if product.price < price_min:
                    price_min = int(product.price)
                if product.price > price_max:
                    price_max = int(product.price)
            if price_min <= price_max:
                data['price_min'] = price_min
                data['price_max'] = price_max

    return product_filter
