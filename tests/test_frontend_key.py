"""
Storefronts and direct callers of the API, see FrontendKeyMiddleware. See settings.py on how to run.
"""
from django.contrib.sites.models import Site
from django.core.cache import cache
from django.http import HttpResponse
from django.test import RequestFactory, TestCase, override_settings

from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from sewingworld.middleware import FrontendKeyMiddleware
from sewingworld.models import SiteProfile
from shop.models import ShopUser

from .clients import FRONTEND_KEY, StorefrontClient, add_storefront_key

OTHER_KEY = 'other-storefront-key'
OTHER_ORIGIN = 'https://wholesale.test'
REFUSED = {'detail': 'Only storefronts and token holders can change data'}


class SiteTests(TestCase):
    def setUp(self):
        add_storefront_key()
        self.default_site = Site.objects.get_current()
        self.other_site = Site.objects.create(domain='wholesale.test', name='Wholesale')
        SiteProfile.objects.create(site=self.other_site, wholesale=True, frontend_key=OTHER_KEY)

    def site_id(self, client, **extra):
        response = client.get('/api/v0/sites/current/', **extra)
        self.assertEqual(response.status_code, 200)
        return response.json()['id']

    def test_key_picks_its_site(self):
        self.assertEqual(self.site_id(StorefrontClient()), self.default_site.id)
        self.assertEqual(self.site_id(APIClient(headers={'X-Frontend-Key': OTHER_KEY})), self.other_site.id)

    def test_key_wins_over_origin(self):
        self.assertEqual(self.site_id(StorefrontClient(), HTTP_ORIGIN=OTHER_ORIGIN), self.default_site.id)

    def test_direct_caller_cannot_choose_the_site(self):
        self.assertEqual(self.site_id(APIClient(), HTTP_ORIGIN=OTHER_ORIGIN), self.default_site.id)
        self.assertEqual(self.site_id(APIClient(), HTTP_REFERER=f'{OTHER_ORIGIN}/catalog/'), self.default_site.id)

    def test_wrong_or_empty_key_counts_as_none(self):
        for key in ('wrong-key', ''):
            client = APIClient(headers={'X-Frontend-Key': key})
            self.assertEqual(self.site_id(client, HTTP_ORIGIN=OTHER_ORIGIN), self.default_site.id, key)
            self.assertEqual(client.post('/api/v0/users/logout/').status_code, 403, key)


class DirectCallerTests(TestCase):
    def setUp(self):
        add_storefront_key()
        self.user = ShopUser.objects.create(phone='+79161234567')

    def test_session_is_ignored(self):
        storefront = StorefrontClient()
        storefront.force_login(self.user)
        direct = APIClient()
        direct.force_login(self.user)

        self.assertEqual(storefront.get('/api/v0/users/current/').json()['id'], self.user.id)
        self.assertIsNone(direct.get('/api/v0/users/current/').json()['id'])

    def test_write_is_refused(self):
        response = APIClient().post('/api/v0/users/logout/')

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), REFUSED)

    def test_write_with_another_authorization_scheme_is_refused(self):
        client = APIClient(headers={'Authorization': 'Basic dXNlcjpwYXNz'})
        self.assertEqual(client.post('/api/v0/users/logout/').status_code, 403)

    def test_write_with_token_passes(self):
        token = Token.objects.create(user=self.user)
        self.assertEqual(APIClient(headers={'Authorization': f'Token {token.key}'}).post('/api/v0/users/logout/').status_code, 204)

    def test_write_with_invalid_token_is_rejected_by_drf(self):
        response = APIClient(headers={'Authorization': 'Token wrong'}).post('/api/v0/users/logout/')

        # DRF answers 403, not 401, because SessionAuthentication comes first
        self.assertEqual(response.status_code, 403)
        self.assertNotEqual(response.json(), REFUSED)

    def test_anonymous_reads_work(self):
        self.assertEqual(APIClient().get('/api/v0/sites/current/').status_code, 200)
        # the QR codes on products lead to the video redirect, the view answers for an unknown product
        response = APIClient().get('/api/v0/products/no-such-product/video/')
        self.assertEqual(response.status_code, 404)
        self.assertNotEqual(response.json(), REFUSED)


class ClientAddressTests(TestCase):
    def setUp(self):
        add_storefront_key()

    def seen_by_view(self, path='/api/v0/sites/current/', **meta):
        seen = {}

        def get_response(request):
            seen['address'] = request.META['REMOTE_ADDR']
            seen['site'] = getattr(request, 'site', None)
            return HttpResponse()

        FrontendKeyMiddleware(get_response)(RequestFactory().get(path, **meta))
        return seen

    def test_storefront_passes_the_client_address(self):
        for address in ('203.0.113.7', '2001:db8::1'):
            seen = self.seen_by_view(HTTP_X_FRONTEND_KEY=FRONTEND_KEY, HTTP_X_REAL_IP=address)
            self.assertEqual(seen['address'], address)

    def test_malformed_address_is_ignored(self):
        for address in ('not-an-address', '203.0.113.7, 10.0.0.1', ''):
            seen = self.seen_by_view(HTTP_X_FRONTEND_KEY=FRONTEND_KEY, HTTP_X_REAL_IP=address)
            self.assertEqual(seen['address'], '127.0.0.1', address)

    def test_direct_caller_cannot_set_the_address(self):
        self.assertEqual(self.seen_by_view(HTTP_X_REAL_IP='203.0.113.7')['address'], '127.0.0.1')

    def test_other_paths_are_left_alone(self):
        seen = self.seen_by_view('/admin/', HTTP_X_REAL_IP='203.0.113.7')
        self.assertEqual(seen['address'], '127.0.0.1')
        self.assertIsNone(seen['site'])


# Throttles count attempts in cache and tests clear it, so that they never touch the shared memcached
@override_settings(CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}})
class ThrottleTests(TestCase):
    def setUp(self):
        cache.clear()
        add_storefront_key()

    def login(self, address, n):
        # a phone per attempt, so that only the limit per client address applies
        client = StorefrontClient(headers={'X-Real-IP': address})
        return client.post('/api/v0/users/login/', {'phone': f'+7916000{n:04d}', 'password': 'wrong'}, format='json')

    def test_clients_of_one_storefront_have_their_own_limits(self):
        statuses = [self.login('203.0.113.1', n).status_code for n in range(11)]

        self.assertNotIn(429, statuses[:10])
        self.assertEqual(statuses[10], 429)
        self.assertNotEqual(self.login('203.0.113.2', 11).status_code, 429)
