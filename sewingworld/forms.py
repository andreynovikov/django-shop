from django import forms

from djconfig.forms import ConfigForm


class SWConfigForm(ConfigForm):
    sw_sms_provider = forms.ChoiceField(label='Смс провайдер', initial='sms_uslugi', choices=[('sms_uslugi', 'смс-услуги'), ('smsru', 'sms.ru')])

    sw_email_from = forms.CharField(label='Адрес эл.почты робота')
    sw_email_unisender = forms.CharField(label='Адрес эл.почты Unisender')
    sw_email_managers = forms.CharField(label='Адрес эл.почты менеджера заказов', help_text='Можно несколько через запятую')
