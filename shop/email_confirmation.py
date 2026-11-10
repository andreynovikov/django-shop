"""
Links that confirm a user's email address. The token is signed and names the user and the address,
so it confirms nothing once the address has changed. It needs no record and works without a session.
"""
from datetime import timedelta
from urllib.parse import quote

from django.core import signing

LIFETIME = timedelta(days=7)
SALT = 'shop.email-confirmation'


def make_token(user):
    return signing.dumps({'user': user.pk, 'email': user.email}, salt=SALT, compress=True)


def read_token(token):
    """ Returns user id and email. Raises signing.BadSignature, or its subclass SignatureExpired. """
    data = signing.loads(token, salt=SALT, max_age=LIFETIME)
    return data['user'], data['email']


def make_link(site, user):
    # A storefront page, which sends the token to the API: browsers reach Django only through the storefronts
    return 'https://%s/confirm-email/?token=%s' % (site.domain, quote(make_token(user)))
