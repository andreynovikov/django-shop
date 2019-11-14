from django import forms
from django.forms.models import model_to_dict

from shop.models import ShopUser


class UserForm(forms.Form):
    name = forms.CharField(label='Имя', max_length=100, required=False, error_messages={'required': 'Укажите ваше имя'})
    phone = forms.CharField(label='Телефон', max_length=30, help_text='Мы принимаем только мобильные телефоны')
    email = forms.EmailField(label='Эл.почта', required=False)
    address = forms.CharField(label='Адрес', max_length=255, required=False)
    #username = forms.CharField(label='Псевдоним', max_length=100, required=False, help_text='Отображается в форуме')

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
