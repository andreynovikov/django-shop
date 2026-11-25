"""
Endpoints for token holders, such as the storefronts' servers: integrations and their product feeds, stock,
and the API schema. See settings.py on how to run.
"""
from django.contrib.sites.models import Site
from django.db import IntegrityError, transaction
from django.test import TestCase

from drf_spectacular.drainage import GENERATOR_STATS
from rest_framework.authtoken.models import Token

from sewingworld.models import SiteProfile
from shop.models import Category, Integration, ProductIntegration, ShopUser, Stock, Supplier

from .clients import StorefrontClient, add_storefront_key, count_queries, signed_in
from .fixtures import add_catalog, add_product


class Base(TestCase):
    def setUp(self):
        add_storefront_key()
        self.site = Site.objects.get_current()
        token = Token.objects.create(user=ShopUser.objects.create(phone='+79160000001'))
        self.client = StorefrontClient(headers={'Authorization': f'Token {token.key}'})
        self.suppliers = Supplier.objects.bulk_create(Supplier(code=f's{n}', code1c=f's{n}', name=f'Склад {n}', order=n) for n in (1, 2))


class IntegrationTests(Base):
    def setUp(self):
        super().setUp()
        root = add_catalog()
        self.machines = machines = Category.objects.create(name='Швейные машины', slug='machines', parent=root)
        fabrics = Category.objects.create(name='Ткани', slug='fabrics', parent=root, feed=False)
        marketplace = Site.objects.create(domain='ozon.ru', name='Ozon')  # without a profile, the feed takes the catalog of the request's site
        self.ozon = Integration.objects.create(name='Ozon', utm_source='ozon', source_site=marketplace, target_site=self.site,
                                               output_template='ozon', settings={'client_id': '123', 'api_key': 'secret-api-key'})
        self.ozon.suppliers.add(self.suppliers[0])
        for pk, fields in (
            (1, {'image': 'products/test/p1.jpg'}),
            (2, {}),
            (3, {'enabled': False}),
            (4, {'price': 0}),
            (5, {'variations': 'цвет'}),
            (6, {'categories': [fabrics]}),
        ):
            product = add_product(pk, **{'enabled': True, 'categories': [machines], **fields})
            ProductIntegration.objects.create(product=product, integration=self.ozon, price=900)
        add_product(7, enabled=True, categories=[machines])  # not given to Ozon

    def feed(self, **flags):
        Integration.objects.filter(pk=self.ozon.pk).update(**flags)
        response = self.client.get(f'/api/v0/integrations/{self.ozon.id}/products/')
        self.assertEqual(response.status_code, 200, response.content)
        return {product['id']: product for product in response.json()}

    def test_api_keys_stay_hidden(self):
        customer = signed_in(ShopUser.objects.create(phone='+79161234567'))
        for client in (self.client, customer):
            for path in ('integrations/', f'integrations/{self.ozon.id}/', 'integrations/ozon/byutm/'):
                with self.subTest(path):
                    self.assertNotIn(b'secret-api-key', client.get(f'/api/v0/{path}').content)

    def test_list_and_retrieve(self):
        [integration] = self.client.get('/api/v0/integrations/').json()
        self.assertEqual((integration['id'], integration['utm_source']), (self.ozon.id, 'ozon'))
        self.assertEqual(integration['name'], 'Ozon')
        self.assertEqual(integration['source_site'], self.ozon.source_site_id)
        self.assertEqual(integration['target_site'], self.site.pk)
        self.assertNotIn('settings', integration)
        self.assertEqual(self.client.get('/api/v0/integrations/ozon/byutm/').json(), integration)
        self.assertEqual(self.client.get(f'/api/v0/integrations/{self.ozon.id}/').json(), integration)
        self.assertEqual(self.client.get('/api/v0/integrations/nope/byutm/').status_code, 404)

    def test_integrations_are_scoped_to_the_storefront(self):
        other_site = Site.objects.create(domain='other.test', name='Other storefront')
        SiteProfile.objects.create(site=other_site, frontend_key='other-storefront-key')
        other_integration = Integration.objects.create(
            name='Other Ozon', utm_source='ozon', source_site=self.ozon.source_site, target_site=other_site, enabled=True,
        )
        for integration, foreign_integration, headers in (
            (self.ozon, other_integration, {}),
            (other_integration, self.ozon, {'X-Frontend-Key': 'other-storefront-key'}),
        ):
            with self.subTest(site=integration.target_site_id):
                [listed] = self.client.get('/api/v0/integrations/', headers=headers).json()
                self.assertEqual(listed['id'], integration.pk)
                self.assertEqual(self.client.get('/api/v0/integrations/ozon/byutm/', headers=headers).json(), listed)
                self.assertEqual(listed.get('output_template'), integration.output_template or None)
                for suffix in ('', 'products/'):
                    response = self.client.get(f'/api/v0/integrations/{foreign_integration.pk}/{suffix}', headers=headers)
                    self.assertEqual(response.status_code, 404)

    def test_utm_source_is_unique_within_a_storefront(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Integration.objects.create(name='Duplicate', utm_source='ozon', source_site=self.ozon.source_site, target_site=self.site)

    def test_site_reverse_relations(self):
        self.assertQuerySetEqual(self.site.integrations.all(), [self.ozon])
        self.assertQuerySetEqual(self.ozon.source_site.source_integrations.all(), [self.ozon])
        self.assertEqual(Site.objects.get(integration=self.ozon), self.site)
        self.assertEqual(Site.objects.get(source_integration=self.ozon), self.ozon.source_site)

    def test_utm_lookup_defaults_to_the_configured_site(self):
        other_site = Site.objects.create(domain='other.test', name='Other storefront')
        other_integration = Integration.objects.create(
            name='Other Ozon', utm_source='ozon', source_site=self.ozon.source_site, target_site=other_site,
        )
        self.addCleanup(Site.objects.clear_cache)
        with self.settings(SITE_ID=other_site.pk):
            self.assertEqual(Integration.get_for_utm_source('ozon'), other_integration)
            self.assertEqual(Integration.get_for_utm_source('ozon', self.site.pk), self.ozon)

    def test_anonymous(self):
        self.assertEqual(StorefrontClient().get('/api/v0/integrations/').status_code, 403)
        self.assertEqual(StorefrontClient().get(f'/api/v0/integrations/{self.ozon.id}/products/').status_code, 403)

    def test_feed_has_products_given_to_the_integration(self):
        products = self.feed()
        self.assertEqual(sorted(products), [1, 2])
        self.assertEqual((products[1]['price'], products[1]['instock']), (1000, 5))
        self.assertNotIn('stock', products[1])

    def test_feed_of_all_products(self):
        self.assertEqual(sorted(self.feed(output_all=True)), [1, 2, 7])

    def test_feed_of_products_with_images(self):
        self.assertEqual(sorted(self.feed(output_with_images=True)), [1])

    def test_feed_without_categories(self):
        products = self.feed(output_skip_categories=True)
        self.assertEqual(sorted(products), [1, 2, 6])
        self.assertNotIn('categories', products[1])

    def test_feed_of_available_products(self):
        Stock.objects.create(product_id=1, supplier=self.suppliers[0], quantity=2)
        Stock.objects.create(product_id=2, supplier=self.suppliers[0], quantity=1, correction=-1)
        Stock.objects.create(product_id=2, supplier=self.suppliers[1], quantity=10)  # not the integration's
        self.assertEqual(sorted(self.feed(output_available=True)), [1])

    def test_feed_with_stock_of_the_integrations_suppliers(self):
        Stock.objects.create(product_id=1, supplier=self.suppliers[0], quantity=2)
        Stock.objects.create(product_id=1, supplier=self.suppliers[1], quantity=10)
        products = self.feed(output_stock=True)
        self.assertEqual((products[1]['stock'], products[2]['stock']), (2, 0))

    def test_feed_counts_the_stock_of_all_its_products_at_once(self):
        Integration.objects.filter(pk=self.ozon.pk).update(output_stock=True)
        Stock.objects.create(product_id=1, supplier=self.suppliers[0], quantity=2)

        def feed():
            return self.client.get(f'/api/v0/integrations/{self.ozon.id}/products/')

        few = count_queries(feed)
        for pk in range(10, 15):
            product = add_product(pk, enabled=True, categories=[self.machines])
            ProductIntegration.objects.create(product=product, integration=self.ozon, price=900)
            Stock.objects.create(product=product, supplier=self.suppliers[0], quantity=3)
        self.assertEqual(count_queries(feed), few)
        self.assertEqual(len(feed().json()), 7)


class StockTests(Base):
    def setUp(self):
        super().setUp()
        add_product(1)
        add_product(2)
        for product, supplier, quantity in ((1, 0, 3), (1, 1, 1), (2, 0, 7)):
            Stock.objects.create(product_id=product, supplier=self.suppliers[supplier], quantity=quantity)

    def stock(self, **params):
        response = self.client.get('/api/v0/stocks/', params)
        self.assertEqual(response.status_code, 200, response.content)
        return [(row['product'], row['supplier'], row['quantity']) for row in response.json()['results']]

    def test_stock_by_supplier_and_product(self):
        self.assertEqual(self.stock(), [('p1', 's1', 3), ('p1', 's2', 1), ('p2', 's1', 7)])
        self.assertEqual(self.stock(supplier='s1'), [('p1', 's1', 3), ('p2', 's1', 7)])
        self.assertEqual(self.stock(supplier='s1', product='p2'), [('p2', 's1', 7)])
        self.assertEqual(self.stock(product=['p1', 'p2'], page_size=2), [('p1', 's1', 3), ('p1', 's2', 1)])

    def test_anonymous(self):
        self.assertEqual(StorefrontClient().get('/api/v0/stocks/').status_code, 403)


class SchemaTests(Base):
    def schema(self, client):
        with GENERATOR_STATS.silence():  # warnings about the reviews app
            return client.get('/api/v0/schema/', {'format': 'json'})

    def test_token_holders_get_the_schema(self):
        response = self.schema(self.client)
        self.assertEqual(response.status_code, 200)
        schema = response.json()
        self.assertIn('400', schema['paths']['/api/v0/orders/preorder/']['post']['responses'])
        self.assertNotIn('settings', schema['components']['schemas']['Integration']['properties'])

    def test_others_do_not(self):
        for client in (StorefrontClient(), signed_in(ShopUser.objects.create(phone='+79161234567'))):
            self.assertEqual(self.schema(client).status_code, 401)
