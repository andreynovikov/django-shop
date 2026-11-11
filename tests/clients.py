"""
Storefronts send their site's key, see FrontendKeyMiddleware. API tests act as one, unless they test direct callers.
"""
from django.contrib.sites.models import Site
from django.db import connection
from django.test.utils import CaptureQueriesContext

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


def count_queries(*requests):
    """
    Queries that the requests make, each a function without arguments. Tests compare the counts for a few and
    for more objects shown: a count that grows with them means a query or more for each object.
    """
    with CaptureQueriesContext(connection) as context:
        for request in requests:
            response = request()
            assert response.status_code == 200, (response.status_code, response.content)
    return len(context.captured_queries)
