from django import forms

from djconfig.forms import ConfigForm


class SWConfigForm(ConfigForm):
    sw_sms_provider = forms.ChoiceField(label='Смс провайдер', initial='sms_uslugi', choices=[('sms_uslugi', 'смс-услуги'), ('smsru', 'sms.ru')])

    sw_email_from = forms.CharField(label='Адрес эл.почты робота')
    sw_email_unisender = forms.CharField(label='Адрес эл.почты Unisender')
    sw_email_managers = forms.CharField(label='Адрес эл.почты менеджера заказов', help_text='Можно несколько через запятую')
    sw_sms_manager = forms.CharField(label='Телефон менеджера заказов Яндекс.Такси')

    sw_yd_campaign = forms.CharField(label='Идентификатор кампании Яндекс.Доставка')
    sw_yd_sender = forms.CharField(label='Идентификатор магазина Яндекс.Доставка')
    sw_yd_token = forms.CharField(label='OAuth-токен магазина Яндекс.Доставка')

    sw_yd_campaign = forms.CharField(label='Идентификатор кампании Яндекс.Доставка')
    sw_yd_sender = forms.CharField(label='Идентификатор магазина Яндекс.Доставка')
    sw_yd_token = forms.CharField(label='OAuth-токен магазина Яндекс.Доставка')

    sw_beru_campaign = forms.CharField(label='Идентификатор кампании Беру!')
    sw_beru_application = forms.CharField(label='ID OAuth-приложения магазина Беру!', help_text='<a href="https://oauth.yandex.ru">https://oauth.yandex.ru</a>')
    sw_beru_token = forms.CharField(label='OAuth-токен магазина Беру!')

    sw_taxi_campaign = forms.CharField(label='Идентификатор кампании Такси!')
    sw_taxi_application = forms.CharField(label='ID OAuth-приложения магазина Такси!', help_text='<a href="https://oauth.yandex.ru">https://oauth.yandex.ru</a>')
    sw_taxi_token = forms.CharField(label='OAuth-токен магазина Такси!')

    sw_modulkassa_login = forms.CharField(label='Логин МодульКасса')
    sw_modulkassa_password = forms.CharField(label='Пароль МодульКасса')
