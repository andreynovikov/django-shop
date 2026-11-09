"""
Session and CSRF cookies: the move to __Host- names and logout with POST. See settings.py on how to run.
"""
from django.contrib.sites.models import Site
from django.test import TestCase, override_settings

from shop.models import Basket, ShopUser

from .clients import StorefrontClient, add_storefront_key

OLD_NAMES = {'SESSION_COOKIE_NAME': 'sessionid', 'CSRF_COOKIE_NAME': 'csrftoken'}
NEW_SESSION = '__Host-sessionid'
NEW_CSRF = '__Host-csrftoken'


@override_settings(SESSION_COOKIE_NAME=NEW_SESSION, CSRF_COOKIE_NAME=NEW_CSRF)
class CookieRenameTests(TestCase):
    def setUp(self):
        add_storefront_key()
        self.user = ShopUser.objects.create(phone='+79161234567')
        # cookies of a visitor who signed in before the rename
        with self.settings(**OLD_NAMES):
            before = StorefrontClient()
            before.force_login(self.user)
            before.get('/api/v0/csrf/')
        self.session_key = before.cookies['sessionid'].value
        self.csrf = before.cookies['csrftoken'].value

    def client_with_old_cookies(self, **kwargs):
        client = StorefrontClient(**kwargs)
        client.cookies['sessionid'] = self.session_key
        client.cookies['csrftoken'] = self.csrf
        return client

    def test_visitor_stays_signed_in_and_gets_new_cookies(self):
        response = self.client_with_old_cookies().get('/api/v0/users/current/')

        self.assertEqual(response.json()['id'], self.user.id)
        self.assertEqual(response.cookies[NEW_SESSION].value, self.session_key)
        self.assertTrue(response.cookies[NEW_SESSION]['httponly'])
        self.assertTrue(response.cookies[NEW_SESSION]['secure'])
        self.assertEqual(response.cookies[NEW_CSRF].value, self.csrf)
        for old in ('sessionid', 'csrftoken'):
            self.assertEqual(response.cookies[old]['max-age'], 0, old)

    def test_old_csrf_token_still_passes_the_check(self):
        client = self.client_with_old_cookies(enforce_csrf_checks=True)

        self.assertEqual(client.post('/api/v0/users/logout/', HTTP_X_CSRFTOKEN=self.csrf).status_code, 204)
        self.assertIsNone(client.get('/api/v0/users/current/').json()['id'])

    def test_new_cookies_are_left_alone(self):
        client = StorefrontClient()
        client.force_login(self.user)

        response = client.get('/api/v0/users/current/')

        self.assertEqual(response.json()['id'], self.user.id)
        self.assertNotIn('sessionid', response.cookies)
        self.assertNotIn(NEW_SESSION, response.cookies)


class LogoutTests(TestCase):
    def setUp(self):
        add_storefront_key()

    def test_logout_with_post(self):
        client = StorefrontClient()
        client.force_login(ShopUser.objects.create(phone='+79161234567'))

        self.assertEqual(client.post('/api/v0/users/logout/').status_code, 204)
        self.assertIsNone(client.get('/api/v0/users/current/').json()['id'])

    def test_anonymous_logout_with_post(self):
        # baskets whose session expired keep no session, a visitor without one must not match them
        site = Site.objects.get_current()
        Basket.objects.create(site=site)
        Basket.objects.create(site=site)

        self.assertEqual(StorefrontClient().post('/api/v0/users/logout/').status_code, 204)
