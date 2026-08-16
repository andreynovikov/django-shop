from yookassa import Configuration

default_app_config = 'yandex_kassa.apps.YandexKassaAppConfig'


def configure_yookassa(order):
    if order.site.profile.yookassa_id:
        Configuration.account_id = order.site.profile.yookassa_id
        Configuration.secret_key = order.site.profile.yookassa_key
    else:
        Configuration.account_id = order.seller.yookassa_id
        Configuration.secret_key = order.seller.yookassa_key
