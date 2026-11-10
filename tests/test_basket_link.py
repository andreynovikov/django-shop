"""
The links of the abandoned basket notice. They open the storefront's pages at their paths, which send them here.
See settings.py on how to run.
"""
from unittest import mock

from django.contrib.sessions.backends.db import SessionStore
from django.contrib.sites.models import Site
from django.core import signing
from django.test import TestCase, override_settings

from shop import tasks
from shop.models import Basket, Country, Currency, Manufacturer, Product

from .clients import StorefrontClient, add_storefront_key


def add_products(*ids):
    """ Without Product.save(), whose signals reach the marketplaces """
    Currency.objects.get_or_create(code=643, defaults={'name': 'RUB'})
    Manufacturer.objects.get_or_create(pk=49, defaults={'code': 'test', 'name': 'Test'})
    Country.objects.get_or_create(pk=1, defaults={'name': 'Россия', 'ename': 'Russia'})
    return Product.objects.bulk_create(Product(pk=pk, code=f'p{pk}', title=f'Товар {pk}') for pk in ids)


class Base(TestCase):
    def setUp(self):
        add_storefront_key()
        self.client = StorefrontClient()
        self.site = Site.objects.get_current()

    def restore(self, contents, client=None, **body):
        return (client or self.client).post('/api/v0/baskets/restore/', {'contents': contents, **body}, format='json')

    def basket(self, client=None):
        return (client or self.client).get('/api/v0/baskets/').json()


class RestoreTests(Base):
    def setUp(self):
        super().setUp()
        add_products(1, 2)

    def test_fills_a_basket_for_the_session(self):
        self.assertEqual(self.restore('1*2,2*1', utm_source='email').status_code, 204)
        [basket] = self.basket()
        self.assertEqual({item['product']['id']: item['quantity'] for item in basket['items']}, {1: 2, 2: 1})
        self.assertEqual(basket['utm_source'], 'email')
        stored = Basket.objects.get()
        self.assertTrue(stored.secondary)  # gets no notice of its own
        self.assertEqual(stored.site, self.site)

    def test_session_keeps_its_basket(self):
        self.restore('1*1')
        self.restore('2*5')
        [basket] = self.basket()
        self.assertEqual([(item['product']['id'], item['quantity']) for item in basket['items']], [(1, 1)])

    def test_malformed_entries_and_unknown_products_are_skipped(self):
        self.restore('1*0,x*1,2*99999,3*1,2*3')
        [basket] = self.basket()
        self.assertEqual([(item['product']['id'], item['quantity']) for item in basket['items']], [(2, 3)])

    def test_nothing_to_restore_makes_no_basket(self):
        self.assertEqual(self.restore('3*1').status_code, 204)
        self.assertEqual(self.basket(), [])
        self.assertFalse(Basket.objects.exists())

    def test_utm_source_is_cleaned_and_cut(self):
        self.restore('1*1', utm_source='e-mail/' + 'x' * 30)
        self.assertEqual(Basket.objects.get().utm_source, 'e_mail_' + 'x' * 13)

    def test_direct_callers_cannot_restore(self):
        response = StorefrontClient(headers={'X-Frontend-Key': ''}).post('/api/v0/baskets/restore/', {'contents': '1*1'}, format='json')
        self.assertEqual(response.status_code, 403)
        self.assertFalse(Basket.objects.exists())


class ClearTests(Base):
    def setUp(self):
        super().setUp()
        session = SessionStore()
        session.create()
        self.other = Basket.objects.create(site=self.site, session_id=session.session_key)

    def test_deletes_the_basket_of_the_link_in_any_session(self):
        response = self.client.post('/api/v0/baskets/clear/', {'sign': signing.Signer().sign(self.other.id)}, format='json')
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Basket.objects.exists())

    def test_bad_signature(self):
        for sign in (str(self.other.id), f'{self.other.id}:forged', '', signing.Signer().sign('not a basket')):
            response = self.client.post('/api/v0/baskets/clear/', {'sign': sign}, format='json')
            self.assertEqual(response.status_code, 400, sign)
            self.assertEqual(response.json(), {'sign': ['Ссылка недействительна']})
        self.assertTrue(Basket.objects.exists())

    def test_basket_gone_already(self):
        sign = signing.Signer().sign(self.other.id)
        self.other.delete()
        self.assertEqual(self.client.post('/api/v0/baskets/clear/', {'sign': sign}, format='json').status_code, 204)


@override_settings(UNISENDER_KEY='', UNISENDER_ABANDONED_BASKET_LIST='')
class NoticeTests(Base):
    def test_links_lead_to_the_storefront_pages(self):
        add_products(1, 2)
        session = SessionStore()
        session.create()
        basket = Basket.objects.create(site=self.site, session_id=session.session_key)
        basket.items.create(product_id=1, quantity=2)
        basket.items.create(product_id=2, quantity=1)
        with mock.patch('shop.tasks.Unisender') as unisender, \
                mock.patch('shop.tasks.config', new=mock.Mock(sw_email_unisender='shop@example.com')), \
                mock.patch('shop.tasks.get_default_site', return_value=Site(domain='www.example.com')):
            unisender.return_value.errorMessage = None
            unisender.return_value.sendEmail.return_value = {'result': [{'index': 0, 'id': 'sent'}]}
            tasks.notify_abandoned_basket(basket.id, 'buyer@example.com', '')
        html = unisender.return_value.sendEmail.call_args.args[4]
        self.assertIn('https://www.example.com/shop/basket/restore/1*2,2*1/?utm_source=email', html)
        sign = signing.Signer().sign(basket.id)
        self.assertIn(f'https://www.example.com/shop/basket/clear/{sign}/?utm_source=email', html)

        # What the pages send
        basket.delete()
        self.restore('1*2,2*1', utm_source='email')
        self.assertEqual(Basket.objects.get().items.count(), 2)
