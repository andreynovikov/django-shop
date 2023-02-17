from django import forms
from django.forms.models import model_to_dict

from reviews.forms import ReviewForm

from shop.models import ShopUser, ShopUserManager


class ProductReviewForm(ReviewForm):
    def __init__(self, *args, **kwargs):
        super(ProductReviewForm, self).__init__(*args, **kwargs)
        self.fields['comment'].required = False


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

    def clean_phone(self):
        norm_phone = ShopUserManager.normalize_phone(self.cleaned_data['phone'])
        if ShopUser.objects.filter(phone=norm_phone).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Пользователь с указанным номером уже зарегестрирован")
        return norm_phone

    def clean_email(self):
        email = self.cleaned_data['email']
        if email == '':
            return email
        if ShopUser.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Пользователь с указанным адресом уже зарегестрирован")
        return email

    def clean_username(self):
        username = self.cleaned_data['username']
        if ShopUser.objects.filter(username=username).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Такой псевдоним уже используется")
        return username


class WarrantyCardForm(forms.Form):
    number = forms.CharField(label='Серийный номер', max_length=100,
                             help_text='Серийный номер можно найти на корпусе изделия или в гарантийном талоне',
                             error_messages={'required': 'Укажите серийный номер изделия'})
