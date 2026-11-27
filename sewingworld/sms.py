from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from constance import config

from . import sms_uslugi, smsru


# sms.ru's statuses about one recipient, which tell nothing about the provider: a wrong, barred or stop-listed
# number, and its limits of messages
SMSRU_RECIPIENT_ERRORS = {202, 207, 209, 230, 231, 232}


class SmsFailure(Exception):
    """ The provider didn't take the message, such as for want of funds or a wrong key: the tasks retry """


def send_sms(phone, message, bonuses=False):
    """
    Sends an SMS through the provider chosen in constance (sw_sms_provider). With bonuses, sms.ru is called with
    the key of the retired bonus program (BONUSES_SMSRU_KEY).

    Each one counts in the health of sending SMS (shop/health.py), whose failures the managers hear of: sms.ru's
    statuses other than accepted, but for those about the recipient, raise SmsFailure. sms-uslugi's answer is
    returned as it is, and only its errors of connection count.
    """
    from shop import health  # sewingworld, the project package, loads before the shop

    with health.monitor(None, health.SMS):
        result = _send(phone, message, bonuses)
        if config.sw_sms_provider == 'smsru' and result['code'] != 100 and result['code'] not in SMSRU_RECIPIENT_ERRORS:
            raise SmsFailure(f"sms.ru {result['code']}: {result['descr']}")
    return result


def _send(phone, message, bonuses):
    sms_client = None
    if config.sw_sms_provider == 'sms_uslugi':
        sms_login = getattr(settings, 'SMS_USLUGI_LOGIN', None)
        sms_password = getattr(settings, 'SMS_USLUGI_PASSWORD', None)
        sms_client = sms_uslugi.Client(sms_login, sms_password)
    if config.sw_sms_provider == 'smsru':
        if bonuses:
            smsru_key = getattr(settings, 'BONUSES_SMSRU_KEY', None)
        else:
            smsru_key = getattr(settings, 'SMSRU_KEY', None)
        sms_client = smsru.Client(smsru_key)
    if sms_client is None:
        raise ImproperlyConfigured("Required setting SMS_PROVIDER should be one of ('sms_uslugi', 'smsru')")
    return sms_client.send(phone, message)
