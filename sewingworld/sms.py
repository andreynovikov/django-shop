from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from . import sms_uslugi, smsru


sms_client = None
sms_provider = getattr(settings, 'SMS_PROVIDER', None)
if sms_provider == 'sms_uslugi':
    sms_login = getattr(settings, 'SMS_USLUGI_LOGIN', None)
    sms_password = getattr(settings, 'SMS_USLUGI_PASSWORD', None)
    sms_client = sms_uslugi.Client(sms_login, sms_password)
if sms_provider == 'smsru':
    smsru_key = getattr(settings, 'SMSRU_KEY', None)
    sms_client = smsru.Client(smsru_key)
if sms_client is None:
    raise ImproperlyConfigured("Required setting SMS_PROVIDER should be one of ('sms_uslugi', 'smsru')")
