from django import forms

from djconfig.forms import ConfigForm


class SWConfigForm(ConfigForm):
    sw_sms_provider = forms.ChoiceField(label='Смс провайдер', initial='sms_uslugi', choices=[('sms_uslugi', 'смс-услуги'), ('smsru', 'sms.ru')])

    sw_email_from = forms.CharField(label='Адрес эл.почты робота')
    sw_email_unisender = forms.CharField(label='Адрес эл.почты Unisender')
    sw_email_managers = forms.CharField(label='Адрес эл.почты менеджера заказов', help_text='Можно несколько через запятую')
    sw_sms_manager = forms.CharField(label='Телефон менеджера заказов Яндекс.Такси')

    sw_beru_delivery = forms.CharField(label='Доставщик Беру')

    sw_yd_campaign = forms.CharField(label='Идентификатор кампании Яндекс.Доставка')
    sw_yd_sender = forms.CharField(label='Идентификатор магазина Яндекс.Доставка')
    sw_yd_token = forms.CharField(label='OAuth-токен магазина Яндекс.Доставка')

    sw_modulkassa_login = forms.CharField(label='Логин МодульКасса')
    sw_modulkassa_password = forms.CharField(label='Пароль МодульКасса')
