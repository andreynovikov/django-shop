from django import forms

from djconfig.forms import ConfigForm


class SWConfigForm(ConfigForm):
    sw_sms_provider = forms.ChoiceField(label='Смс провайдер', initial='sms_uslugi', choices=[('sms_uslugi', 'смс-услуги'), ('smsru', 'sms.ru')])

    sw_email_from = forms.CharField(label='Адрес эл.почты робота')
    sw_email_unisender = forms.CharField(label='Адрес эл.почты Unisender')
    sw_email_managers = forms.CharField(label='Адрес эл.почты менеджера заказов', help_text='Можно несколько через запятую')

    sw_beru_campaign = forms.CharField(label='Идентификатор кампании Беру!')
    sw_beru_application = forms.CharField(label='ID OAuth-приложения магазина Беру!', help_text='<a href="https://oauth.yandex.ru">https://oauth.yandex.ru</a>')
    sw_beru_token = forms.CharField(label='OAuth-токен магазина Беру!')

    sw_modulkassa_login = forms.CharField(label='Логин МодульКасса')
    sw_modulkassa_password = forms.CharField(label='Пароль МодульКасса')
