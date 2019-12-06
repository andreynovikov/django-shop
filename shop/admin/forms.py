import os
import re

from tidylib import tidy_fragment

from django import forms
from django.conf import settings
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.utils.encoding import smart_text
from django.utils.html import conditional_escape, mark_safe

from mptt.forms import TreeNodeMultipleChoiceField
from import_export.forms import ImportForm, ConfirmImportForm, ExportForm
from model_field_list import ModelFieldListFormField

from djconfig import config

from sewingworld.widgets import AutosizedTextarea

from shop.models import Supplier, Product, Order, OrderItem, ShopUser, Box, ActOrder
from shop.tasks import import1c

from .widgets import PhoneWidget, TagAutoComplete, ReadOnlyInput, DisablePluralText, OrderItemTotalText, \
    OrderItemProductLink, ListTextWidget, YandexDeliveryWidget


class CategoryAdminForm(forms.ModelForm):
    class Meta:
        widgets = {
            'brief': AutosizedTextarea(attrs={'rows': 3}),
            'description': AutosizedTextarea(attrs={'rows': 3}),
        }


class OneSImportForm(forms.Form):
    file = forms.ChoiceField(label="CSV файл 1С", required=True)

    def __init__(self, *args, **kwargs):
        super(OneSImportForm, self).__init__(*args, **kwargs)
        import_dir = getattr(settings, 'SHOP_IMPORT_DIRECTORY', 'import')
        files = [(f, f) for f in filter(lambda x: x.endswith('.txt'), os.listdir(import_dir))]
        self.fields['file'].choices = files
        if len(files):
            self.fields['file'].initial = files[0]

    def save(self):
        import1c.delay(self.cleaned_data['file'])
        return 'Импорт запущен в фоновом режиме, результат придёт на адрес %s' % config.sw_email_managers


class WarrantyCardPrintForm(forms.Form):
    serial_number = forms.CharField(label='Серийный номер', max_length=30, required=False)


class OrderCombineForm(forms.Form):
    order_number = forms.IntegerField(label='Номер заказа', min_value=1, required=True)


class OrderDiscountForm(forms.Form):
    discount = forms.FloatField(label='Скидка', min_value=0, required=True)
    unit = forms.ChoiceField(label='Вид', choices=(('pct', 'проценты'), ('val', 'рубли')),
                             widget=forms.RadioSelect, initial='pct', required=True)


class SendSmsForm(forms.Form):
    message = forms.CharField(label='Сообщение', max_length=160, required=True)

    def __init__(self, *args, **kwargs):
        _message_list = getattr(settings, 'SHOP_SMS_MESSAGES', ())
        super(SendSmsForm, self).__init__(*args, **kwargs)
        self.fields['message'].widget = ListTextWidget(data_list=_message_list, attrs={'size': 90})


class YandexDeliveryForm(forms.Form):
    yd_client = getattr(settings, 'YD_CLIENT', {})
    warehouses = yd_client.get('warehouses', [])
    fio = forms.CharField(label='ФИО', required=True)
    fio_last = forms.BooleanField(label='Фамилия в конце', required=False)
    warehouse = forms.ChoiceField(label='Склад', choices=map(lambda x: (x['id'], x['name']), warehouses))

    def __init__(self, *args, **kwargs):
        super(YandexDeliveryForm, self).__init__(*args, **kwargs)
        self.fields['fio'].widget = ReadOnlyInput(None)

    class Media:
        css = {
            'all': ('admin/css/forms.css',)
        }


class SelectTagForm(forms.Form):
    tags = forms.CharField(label='Теги', max_length=50, required=True)

    def __init__(self, *args, **kwargs):
        model = kwargs.pop('model', None)
        super(SelectTagForm, self).__init__(*args, **kwargs)
        self.fields['tags'].widget = TagAutoComplete(model=model)


class SelectSupplierForm(forms.Form):
    supplier = forms.ModelChoiceField(label='Поставщик', queryset=Supplier.objects.order_by('order'), required=True, empty_label=None)


class StockInlineForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['supplier'].widget = ReadOnlyInput(self.instance.supplier)
            self.fields['quantity'].widget = ReadOnlyInput(self.instance.quantity)


class SWTreeNodeMultipleChoiceField(TreeNodeMultipleChoiceField):
    def label_from_instance(self, obj):
        return mark_safe(conditional_escape(smart_text('/'.join([x['name'] for x in obj.get_ancestors(include_self=True).values()]))))


class ProductImportForm(ImportForm):
    id_field = forms.ChoiceField(label='Идентификационное поле', choices=(('id', 'ID'), ('code', 'идентификатор'), ('article', 'код 1С'), ('partnumber', 'partnumber'), ('gtin', 'GTIN')))


class ProductConfirmImportForm(ConfirmImportForm):
    id_field = forms.CharField(widget=forms.HiddenInput())


class ProductExportForm(ExportForm):
    export_fields = ModelFieldListFormField(source_model=Product, label='Поля для экспорта', widget=FilteredSelectMultiple('свойства товара', False))


class ProductAdminForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = '__all__'
        field_classes = {
            'categories': SWTreeNodeMultipleChoiceField,
        }
        widgets = {
            'title': forms.TextInput(attrs={'size': 120}),
            'runame': forms.TextInput(attrs={'size': 120}),
            'gtin': forms.TextInput(attrs={'size': 10}),
            'whatis': AutosizedTextarea(attrs={'rows': 1}),
            'spec': AutosizedTextarea(attrs={'rows': 3}),
            'shortdescr': AutosizedTextarea(attrs={'rows': 3}),
            'yandexdescr': AutosizedTextarea(attrs={'rows': 3}),
            'descr': AutosizedTextarea(attrs={'rows': 3}),
            'manuals': AutosizedTextarea(attrs={'rows': 2}),
            'state': AutosizedTextarea(attrs={'rows': 1}),
            'complect': AutosizedTextarea(attrs={'rows': 3}),
            'dealertxt': AutosizedTextarea(attrs={'rows': 2}),
            'tags': TagAutoComplete(model=ShopUser)
        }

    def clean_article(self):
        article = self.cleaned_data['article']
        if article and Product.objects.filter(article=article).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Такой код 1С уже используется")
        return article

    def clean(self):
        cleaned_data = super().clean()
        # clean HTML in some fields
        for field in ['shortdescr', 'yandexdescr', 'descr', 'spec', 'manuals', 'state', 'complect', 'stitches', 'dealertxt', 'sm_display', 'sm_software']:
            value = cleaned_data.get(field)
            if not value:
                continue
            fragment, errors = tidy_fragment(value, options={'indent': 0})
            if not fragment:
                self.add_error(field, forms.ValidationError("Ошибка очистки HTML"))
                continue
            cleaned_data[field] = fragment

        code = cleaned_data.get('code')
        reg = re.compile('^[-\.\w]+$')
        # test for code presence is required for mass edit
        if code and not reg.match(code):
            self.add_error('code', forms.ValidationError("Код товара содержит недопустимые символы"))
        return cleaned_data


class ProductKindForm(forms.ModelForm):
    class Meta:
        widgets = {
            'comparison': FilteredSelectMultiple('свойства товара', False)
        }


class OrderItemInlineAdminForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['product'].widget = OrderItemProductLink(self.instance)
        if 'product_price' in self.fields:
            self.fields['product_price'].widget = DisablePluralText(self.instance, attrs={'style': 'width: 6em'})
        if 'pct_discount' in self.fields:
            self.fields['pct_discount'].widget = forms.TextInput(attrs={'style': 'width: 3em'})
        if 'val_discount' in self.fields:
            self.fields['val_discount'].widget = DisablePluralText(self.instance, attrs={'style': 'width: 4em'})
        if 'quantity' in self.fields:
            self.fields['quantity'].widget = DisablePluralText(self.instance, attrs={'style': 'width: 3em'})
        if 'box' in self.fields:
            if self.instance.pk:
                self.fields['box'].queryset = Box.objects.filter(order=self.instance.order)
        self.fields['total'].widget = OrderItemTotalText(self.instance, attrs={'style': 'width: 6em'})

    def clean_box(self):
        box = self.cleaned_data.get('box', None)
        status = int(self.data.get('status', '0'))
        if status == Order.STATUS_COLLECTED and not box:
            raise forms.ValidationError("Не выбрана коробка")
        return box

    class Meta:
        model = OrderItem
        fields = '__all__'


class BoxInlineAdminForm(forms.ModelForm):
    def has_changed(self):
        if self.instance.pk:
            return super().has_changed()
        else:
            return True

    def clean_field(self, field):
        value = self.cleaned_data.get(field, None)
        status = int(self.data.get('status', '0'))
        if status == Order.STATUS_COLLECTED and not value:
            raise forms.ValidationError("Отсутствует {}".format(self.fields[field].label.split(',')[0].lower()))
        return value

    def clean_weight(self):
        return self.clean_field('weight')

    def clean_length(self):
        return self.clean_field('length')

    def clean_width(self):
        return self.clean_field('width')

    def clean_height(self):
        return self.clean_field('height')

    class Meta:
        model = Box
        fields = '__all__'


class OrderAdminForm(forms.ModelForm):
    user_tags = forms.CharField(label='Теги', max_length=getattr(settings, 'MAX_TAG_LENGTH', 50), required=False)

    def __init__(self, *args, **kwargs):
        super(OrderAdminForm, self).__init__(*args, **kwargs)
        try:
            instance = kwargs['instance']
            self.fields['user_tags'].initial = instance.user.tags
            self.fields['user_tags'].widget = TagAutoComplete(model=type(instance.user), attrs=self.fields['user_tags'].widget.attrs)
            self.fields['delivery_yd_order'].widget = YandexDeliveryWidget(instance.id)
        except (KeyError, AttributeError):
            pass

    def clean_store(self):
        store = self.cleaned_data.get('store', None)
        if self.cleaned_data['status'] == Order.STATUS_DELIVERED_SHOP and store is None:
            raise forms.ValidationError("Не указан магазин доставки!")
        return store

    def save(self, commit=True):
        if 'user_tags' in self.cleaned_data:  # massadmin does not have it
            self.instance.user.tags = self.cleaned_data['user_tags']
            self.instance.user.save()
        return super(OrderAdminForm, self).save(commit=commit)

    class Meta:
        model = Order
        exclude = ['created']
        widgets = {
            'address': forms.TextInput(attrs={'style': 'width: 60%'}),
            'phone': PhoneWidget(),
            'phone_aux': PhoneWidget()
        }

    class Media:
        js = [
            'js/time-shortcuts.js'
        ]
        css = {
            'all': ('css/time-shortcuts.css',)
        }


class ActOrderInlineAdminForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['order'].widget = ReadOnlyInput(self.instance.order)

    class Meta:
        model = ActOrder
        fields = '__all__'
