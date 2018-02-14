import os
from django import forms
from django.conf import settings

from shop.models import Supplier, Product, Stock
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
