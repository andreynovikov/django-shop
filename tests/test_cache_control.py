"""
API responses to a session stay out of caches, see PrivateApiCacheMiddleware. See settings.py on how to run.
"""
from django.test import TestCase

from shop.models import ShopUser

from .clients import StorefrontClient, add_storefront_key


class PrivateCacheTests(TestCase):
    def setUp(self):
        add_storefront_key()
        self.client = StorefrontClient()

    def assertNotStored(self, response):
        self.assertIn('no-store', response['Cache-Control'])
        self.assertIn('private', response['Cache-Control'])

    def test_signed_in_user(self):
        self.client.force_login(ShopUser.objects.create(phone='+79161234567'))
        self.assertNotStored(self.client.get('/api/v0/users/current/'))
        self.assertNotStored(self.client.get('/api/v0/orders/'))

    def test_response_that_starts_a_session(self):
        response = self.client.post('/api/v0/baskets/', {}, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertNotStored(response)
        self.assertNotStored(self.client.get('/api/v0/baskets/'))

    def test_requests_without_a_session_are_left_alone(self):
        # Such as the storefront's server-side ones, which build its pages
        response = self.client.get('/api/v0/users/current/')
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.has_header('Cache-Control'))
