from collections import OrderedDict

CONSTANCE_IGNORE_ADMIN_VERSION_CHECK = True
CONSTANCE_BACKEND = 'constance.backends.database.DatabaseBackend'
CONSTANCE_DATABASE_CACHE_BACKEND = 'default'

CONSTANCE_ADDITIONAL_FIELDS = {
    'sms_provider_select': [
        'django.forms.fields.ChoiceField',
        {
            'widget': 'django.forms.Select',
            'choices': (('sms_uslugi', 'смс-услуги'), ('smsru', 'sms.ru'))
        }
    ],
    'contractor_model_select': [
        'sewingworld.fields.ConstanceModelChoiceField',
        {
            'model_string': 'shop.Contractor',
            'model_filters': {'is_seller': True},
            'required': False,
        }
    ],
}

CONSTANCE_CONFIG = OrderedDict([
    ('sw_sms_provider', ('smsru', 'Смс провайдер', 'sms_provider_select')),
    ('sw_default_seller', (None, 'Продавец по-умолчанию', 'contractor_model_select')),
    ('sw_email_from', ('', 'Адрес эл.почты робота')),
    ('sw_email_unisender', ('', 'Адрес эл.почты Unisender')),
    ('sw_beru_delivery', ('', 'Доставщик Беру')),
    ('sw_yd_campaign', ('', 'Идентификатор кампании Яндекс.Доставка')),
    ('sw_yd_sender', ('', 'Идентификатор магазина Яндекс.Доставка')),
    ('sw_yd_token', ('', 'OAuth-токен магазина Яндекс.Доставка')),
    ('sw_bonuses_ydisk_token', ('', 'OAuth токен Яндекс.Диск для бонусов')),
])
