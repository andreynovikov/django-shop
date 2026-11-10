"""
Storefronts send their site's key, see FrontendKeyMiddleware. API tests act as one, unless they test direct callers.
"""
from django.contrib.sites.models import Site

from rest_framework.test import APIClient

from sewingworld.models import SiteProfile

FRONTEND_KEY = 'storefront-key'


def add_storefront_key(site=None):
    """ Gives the site, the default one unless given, the key that StorefrontClient sends """
    SiteProfile.objects.update_or_create(site=site or Site.objects.get_current(), defaults={'frontend_key': FRONTEND_KEY})


class StorefrontClient(APIClient):
    """ A client whose requests come through the storefront of the default site """
    def __init__(self, *args, headers=None, **kwargs):
        super().__init__(*args, headers={'X-Frontend-Key': FRONTEND_KEY, **(headers or {})}, **kwargs)


def signed_in(user):
    """ A storefront client with the user logged in """
    client = StorefrontClient()
    client.force_login(user)
    return client
