"""
Storefronts send their site's key, see FrontendKeyMiddleware. API tests act as one, unless they test direct callers.
"""
from django.contrib.auth.models import Group, Permission
from django.contrib.sites.models import Site
from django.db import connection
from django.test.utils import CaptureQueriesContext

from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from sewingworld.models import SiteProfile
from shop.models import ShopUser

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


def token_client(user):
    """ A direct caller, such as analytics, that signs in with the user's token and sends no storefront key """
    return APIClient(headers={'Authorization': f'Token {Token.objects.create(user=user).key}'})


def api_reader(*codenames, phone='+79160000009', through_group=False):
    """
    An account with the permissions to read all (api_read_users, api_read_orders), given directly or through a group,
    and its token client
    """
    user = ShopUser.objects.create(phone=phone, name='Аналитика')
    permissions = Permission.objects.filter(content_type__app_label='shop', codename__in=codenames)
    assert len(permissions) == len(codenames), codenames
    if through_group:
        group = Group.objects.create(name='Аналитика')
        group.permissions.add(*permissions)
        user.groups.add(group)
    else:
        user.user_permissions.add(*permissions)
    return user, token_client(user)


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
