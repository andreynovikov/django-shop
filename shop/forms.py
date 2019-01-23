import os
import re
from django import forms
from django.forms.models import model_to_dict
#from suit.widgets import AutosizedTextarea
from django.conf import settings

#import autocomplete_light

from shop.models import Supplier, Product, Stock, Order, OrderItem, ShopUser
from shop.widgets import PhoneWidget, TagAutoComplete, ReadOnlyInput, DisablePluralText, OrderItemTotalText, \
    OrderItemProductLink
from shop.tasks import import1c


class UserForm(forms.Form):
    name = forms.CharField(label='Имя', max_length=100, required=False, error_messages={'required': 'Укажите ваше имя'})
    phone = forms.CharField(label='Телефон', max_length=30, help_text='Мы принимаем только мобильные телефоны')
    email = forms.EmailField(label='Эл.почта', required=False)
    address = forms.CharField(label='Адрес', max_length=255, required=False)
    username = forms.CharField(label='Псевдоним', max_length=100, required=False, help_text='Отображается в форуме')

    def __init__(self, *args, **kwargs):
        self.instance = kwargs.pop('user', None)
        if self.instance:
            kwargs['initial'] = model_to_dict(self.instance)
        super(UserForm, self).__init__(*args, **kwargs)

    def clean_username(self):
        username = self.cleaned_data['username']
        if ShopUser.objects.filter(username=username).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Такой псевдоним уже используется")
        return username


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
        shop_settings = getattr(settings, 'SHOP_SETTINGS', {})
        return 'Импорт запущен в фоновом режиме, результат придёт на адрес %s' % ', '.join(shop_settings['email_managers'])


class WarrantyCardPrintForm(forms.Form):
    serial_number = forms.CharField(label='Серийный номер', max_length=30, required=False)


class OrderCombineForm(forms.Form):
    order_number = forms.IntegerField(label='Номер заказа', min_value=1, required=True)


class OrderDiscountForm(forms.Form):
    discount = forms.IntegerField(label='Скидка', min_value=0, required=True)


class SendSmsForm(forms.Form):
    message = forms.CharField(label='Сообщение', max_length=160, required=True)


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


from django.utils.encoding import smart_text
from django.utils.html import conditional_escape, mark_safe
from mptt.forms import TreeNodeChoiceField, TreeNodeMultipleChoiceField

class SWTreeNodeMultipleChoiceField(TreeNodeMultipleChoiceField):
    def label_from_instance(self, obj):
        return mark_safe(conditional_escape(smart_text('/'.join([x['name'] for x in obj.get_ancestors(include_self=True).values()]))))


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
            #'spec': AutosizedTextarea(attrs={'rows': 3,}),
            #'shortdescr': AutosizedTextarea(attrs={'rows': 3,}),
            #'yandexdescr': AutosizedTextarea(attrs={'rows': 3,}),
            #'descr': AutosizedTextarea(attrs={'rows': 3,}),
            #'state': AutosizedTextarea(attrs={'rows': 2,}),
            #'complect': AutosizedTextarea(attrs={'rows': 3,}),
            #'dealertxt': AutosizedTextarea(attrs={'rows': 2,}),
            'tags': TagAutoComplete(model=ShopUser)
        }

    def clean(self):
        code = self.cleaned_data.get('code')
        reg = re.compile('^[-\.\w]+$')
        # test for code presence is required for mass edit
        if not code or reg.match(code):
            return super().clean()
        else:
            self.add_error('code', forms.ValidationError("Код товара содержит недопустимые символы"))


class OrderItemInlineAdminForm(forms.ModelForm):
    class Meta:
        model = OrderItem
        fields = '__all__'
        widgets = {
            'pct_discount': forms.TextInput(attrs={'style': 'width: 3em'}),
            }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['product'].widget = OrderItemProductLink(self.instance)
        self.fields['product_price'].widget = DisablePluralText(self.instance, attrs={'style': 'width: 6em'})
        self.fields['val_discount'].widget = DisablePluralText(self.instance, attrs={'style': 'width: 4em'})
        self.fields['quantity'].widget = DisablePluralText(self.instance, attrs={'style': 'width: 3em'})
        self.fields['total'].widget = OrderItemTotalText(self.instance, attrs={'style': 'width: 6em'})


class OrderAdminForm(forms.ModelForm): #autocomplete_light.ModelForm):
    user_tags = forms.CharField(label='Теги', max_length=getattr(settings, 'MAX_TAG_LENGTH', 50), required=False)

    def __init__(self, *args, **kwargs):
        super(OrderAdminForm, self).__init__(*args, **kwargs)
        try:
            instance = kwargs['instance']
            self.fields['user_tags'].initial = instance.user.tags
            self.fields['user_tags'].widget = TagAutoComplete(model=type(instance.user), attrs=self.fields['user_tags'].widget.attrs)
        except (KeyError, AttributeError):
            pass

    def clean_store(self):
        store = self.cleaned_data.get('store', None)
        if self.cleaned_data['status'] == Order.STATUS_DELIVERED_SHOP and store is None:
            raise forms.ValidationError("Не указан магазин доставки!")
        return store

    def save(self, commit=True):
        self.instance.user.tags = self.cleaned_data['user_tags']
        self.instance.user.save()
        return super(OrderAdminForm, self).save(commit=commit)

    class Meta:
        model = Order
        exclude = ['created']
        widgets = {
            'phone': PhoneWidget(),
            'phone_aux': PhoneWidget(),
            }
