# Credentials of the SMS gateways, marketplaces, mailing and accounting services. They are secrets, so they come from
# .env like the rest of the configuration (settings/__init__.py reads it first). An unset one is empty and the
# integration that needs it fails when used. The values are read as they are, without django-environ's "$" proxying,
# because a password may start with "$".
import os


def _get(name):
    return os.environ.get(name, '')


def _int(name):
    value = _get(name)
    return int(value) if value else None


SMSRU_KEY = _get('SMSRU_KEY')
BONUSES_SMSRU_KEY = _get('BONUSES_SMSRU_KEY')
SMS_USLUGI_LOGIN = _get('SMS_USLUGI_LOGIN')
SMS_USLUGI_PASSWORD = _get('SMS_USLUGI_PASSWORD')

# Yandex Metrika's CDP uploads
YM_COUNTER_ID = _get('YM_COUNTER_ID')
YM_API_TOKEN = _get('YM_API_TOKEN')

UNISENDER_KEY = _get('UNISENDER_KEY')
UNISENDER_PRODUCT_REVIEW_LIST = _int('UNISENDER_PRODUCT_REVIEW_LIST')
UNISENDER_ABANDONED_BASKET_LIST = _int('UNISENDER_ABANDONED_BASKET_LIST')

RARUS = {
    'login': _get('RARUS_LOGIN'),
    'password': _get('RARUS_PASSWORD'),
}

# The API of SberMegaMarket, and the basic auth of its notifications to us
SBER_MARKET = {
    'api': _get('SBER_MARKET_API'),
    'token': _get('SBER_MARKET_TOKEN'),
    'merchant_code': _get('SBER_MARKET_MERCHANT_CODE'),
    'auth_user': _get('SBER_MARKET_AUTH_USER'),
    'auth_password': _get('SBER_MARKET_AUTH_PASSWORD'),
}

# The bot that posts to the staff channel: its token from @BotFather, and the channel as its chat id (-100…) or @name.
# The bot must be an administrator of the channel allowed to post. Unset, nothing is posted.
TELEGRAM_BOT_TOKEN = _get('TELEGRAM_BOT_TOKEN')
TELEGRAM_STAFF_CHAT = _get('TELEGRAM_STAFF_CHAT')
