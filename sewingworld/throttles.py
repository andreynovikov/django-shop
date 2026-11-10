"""
Rate limits of the user endpoints, rates are in DEFAULT_THROTTLE_RATES. With a storefront's key the client address
is the customer's, see FrontendKeyMiddleware.
"""
from rest_framework.throttling import SimpleRateThrottle

from shop.models import ShopUserManager


class PhoneRateThrottle(SimpleRateThrottle):
    """
    Limits attempts per target phone regardless of client IP, so that one-time codes cannot be brute forced.
    The phone comes from the URL or the body, unless it is given.
    """
    def __init__(self, phone=None):
        super().__init__()
        self.phone = phone

    def get_cache_key(self, request, view):
        if self.phone is not None:
            ident = self.phone
        elif view.detail:
            ident = str(view.kwargs.get(view.lookup_field, ''))
        else:
            data = request.data if isinstance(request.data, dict) else {}
            ident = str(data.get('phone', ''))
        return self.cache_format % {'scope': self.scope, 'ident': ShopUserManager.normalize_phone(ident)}


class IpRateThrottle(SimpleRateThrottle):
    """ Limits attempts per client IP, for authenticated and anonymous users alike """
    def get_cache_key(self, request, view):
        return self.cache_format % {'scope': self.scope, 'ident': self.get_ident(request)}


class LoginIpThrottle(IpRateThrottle):
    scope = 'login'


class PasswordFailureThrottle(PhoneRateThrottle):
    """
    Limits wrong permanent passwords of a phone. Only failures count, see failed(), so whoever tries passwords
    can't lock the owner out: a code from SMS logs in whatever the count, and the codes have limits of their own.
    """
    def throttle_success(self):
        return True  # nothing is counted until the password turns out wrong

    def failed(self):
        """ Counts a wrong password, after allow_request() has let it be checked """
        super().throttle_success()


class PasswordFailureHourlyThrottle(PasswordFailureThrottle):
    scope = 'login_phone'


class PasswordFailureDailyThrottle(PasswordFailureThrottle):
    scope = 'login_phone_day'


class CheckIpThrottle(IpRateThrottle):
    scope = 'check'


class CheckPhoneThrottle(PhoneRateThrottle):
    """ Limits codes sent, not requests, so it is applied only when a code is about to be sent """
    scope = 'check_phone'


class CheckPhoneDailyThrottle(PhoneRateThrottle):
    """
    Codes a day, with the hourly limit: each code takes 5 guesses, and the login limits above don't apply to codes.
    Applied with CheckPhoneThrottle.
    """
    scope = 'check_phone_day'


class RegistrationIpThrottle(IpRateThrottle):
    """ Registration says which phones and usernames are taken, so it is limited as the phone lookup is """
    scope = 'register'


class EmailLinkUserThrottle(SimpleRateThrottle):
    """ Limits confirmation links sent for a user's address, it is applied when a link is about to be sent """
    scope = 'email_link'

    def __init__(self, user):
        super().__init__()
        self.user = user

    def get_cache_key(self, request, view):
        return self.cache_format % {'scope': self.scope, 'ident': self.user.pk}


class EmailLinkIpThrottle(IpRateThrottle):
    """ Accounts created at checkout need no SMS, so links are limited per client as well """
    scope = 'email_link_ip'
