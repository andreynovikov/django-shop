import os
from django import forms
from django.conf import settings

import autocomplete_light

from shop.models import Supplier, Product, Stock, Order
from shop.widgets import PhoneWidget, TagAutoComplete
from shop.tasks import import1c


class UserForm(forms.Form):
    name = forms.CharField(label='Имя', max_length=100, error_messages={'required': 'Укажите ваше имя'})
    phone = forms.CharField(label='Телефон', max_length=30, help_text='Мы принимаем только мобильные телефоны')
    email = forms.EmailField(label='Эл.почта', required=False)
    address = forms.CharField(label='Адрес', max_length=255, required=False)


class OneSImportForm(forms.Form):
    file = forms.ChoiceField(label="CSV файл 1С", required=True)

    def __init__(self, *args, **kwargs):
        super(OneSImportForm, self).__init__(*args, **kwargs)
        import_dir = getattr(settings, 'SHOP_IMPORT_DIRECTORY', 'import')
        files = [(f, f) for f in filter(lambda x: x.endswith('.txt'), os.listdir(import_dir))]
        self.fields['file'].choices = files
        self.fields['file'].initial=files[0]

    def save(self):
        import1c.delay(self.cleaned_data['file'])
        shop_settings = getattr(settings, 'SHOP_SETTINGS', {})
        return 'Импорт запущен в фоновом режиме, результат придёт на адрес %s' % ', '.join(shop_settings['email_managers'])


class WarrantyCardPrintForm(forms.Form):
    serial_number = forms.CharField(label='Серийный номер', max_length=30, required=False)


class OrderAdminForm(autocomplete_light.ModelForm):
    user_tags = forms.CharField(label='Теги', max_length=50, required=False)

    def __init__(self, *args, **kwargs):
        super(OrderAdminForm, self).__init__(*args, **kwargs)
        try:
            instance = kwargs['instance']
            self.fields['user_tags'].initial = instance.user.tags
            self.fields['user_tags'].widget = TagAutoComplete()
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
