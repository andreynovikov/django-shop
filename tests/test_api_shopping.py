"""
Baskets, favorites and comparisons. See settings.py on how to run.
"""
import copy
import threading

from django.contrib.sites.models import Site
from django.db import connection
from django.test import TestCase, TransactionTestCase

from shop.models import Basket, BasketItem, Favorites, Product, ProductKind, ProductPrice, ShopUser

from .clients import StorefrontClient, add_storefront_key, count_queries, signed_in
from .fixtures import add_product


class Base(TestCase):
    def setUp(self):
        add_storefront_key()
        self.site = Site.objects.get_current()
        add_product(1, price=1000)
        add_product(2, price=300)
        self.client = StorefrontClient()


class BasketTests(Base):
    def setUp(self):
        super().setUp()
        response = self.client.post('/api/v0/baskets/')
        self.assertEqual(response.status_code, 201)
        self.basket = response.json()['id']

    def post(self, action, client=None, **body):
        return (client or self.client).post(f'/api/v0/baskets/{self.basket}/{action}/', body, format='json')

    def items(self):
        """ Quantities by product, None when the basket is gone """
        response = self.client.get(f'/api/v0/baskets/{self.basket}/')
        if response.status_code == 404:
            return None
        return {item['product']['id']: item['quantity'] for item in response.json()['items']}

    def test_one_basket_per_session(self):
        self.assertEqual(self.client.post('/api/v0/baskets/').json()['id'], self.basket)
        self.assertEqual([basket['id'] for basket in self.client.get('/api/v0/baskets/').json()], [self.basket])
        self.assertNotEqual(StorefrontClient().post('/api/v0/baskets/').json()['id'], self.basket)

    def test_created_with_data(self):
        response = self.client.post('/api/v0/baskets/', {'phone': '+79161234567', 'utm_source': 'email'}, format='json')
        self.assertEqual(response.status_code, 201)
        basket = Basket.objects.get()
        self.assertEqual((basket.id, basket.phone, basket.utm_source), (self.basket, '+79161234567', 'email'))

    def test_add(self):
        self.assertEqual(self.post('add', product=1, quantity=2).status_code, 204)
        self.post('add', product=1)
        self.post('add', product=2)
        self.assertEqual(self.items(), {1: 3, 2: 1})

    def test_totals(self):
        self.post('add', product=1, quantity=2)
        self.post('add', product=2)
        data = self.client.get(f'/api/v0/baskets/{self.basket}/').json()
        self.assertEqual((data['total'], data['quantity']), (2300, 3))
        self.assertEqual([(item['cost'], item['price']) for item in data['items']], [(1000, 2000), (300, 300)])

    def test_prices_of_the_site(self):
        ProductPrice.objects.bulk_create([ProductPrice(product_id=1, site=self.site, price=900, cur_price=900, pct_discount=10)])
        self.post('add', product=1, quantity=2)
        data = self.client.get(f'/api/v0/baskets/{self.basket}/').json()
        [item] = data['items']
        self.assertEqual((item['product']['price'], item['product']['cost'], item['cost'], item['price']), (900, 810, 810, 1620))
        self.assertEqual((item['discount'], item['discount_text'], data['total']), (90, '10%', 1620))

    def test_queries_do_not_grow_with_the_items(self):
        def queries():
            return count_queries(lambda: self.client.get('/api/v0/baskets/'), lambda: self.client.get(f'/api/v0/baskets/{self.basket}/'))

        self.post('add', product=1)
        few = queries()
        for pk in range(10, 15):
            add_product(pk)
            self.post('add', product=pk)
        ProductPrice.objects.bulk_create(ProductPrice(product_id=pk, site=self.site, price=900, cur_price=900) for pk in (1, 10))
        self.assertEqual(queries(), few)

    def test_update(self):
        self.post('add', product=1)
        self.assertEqual(self.post('update', product=1, quantity=5).status_code, 204)
        self.post('update', product=2, quantity=2)
        self.assertEqual(self.items(), {1: 5, 2: 2})
        self.post('update', product=1, quantity=0)
        self.assertEqual(self.items(), {2: 2})
        self.post('update', product=2, quantity=0)
        self.assertIsNone(self.items())  # the last item takes the basket with it

    def test_remove(self):
        self.post('add', product=1)
        self.post('add', product=2)
        self.assertEqual(self.post('remove', product=1).status_code, 204)
        self.assertEqual(self.post('remove', product=1).status_code, 204)
        self.assertEqual(self.items(), {2: 1})
        self.post('remove', product=2)
        self.assertIsNone(self.items())

    def test_unknown_product(self):
        for action in ('add', 'update', 'remove'):
            with self.subTest(action):
                response = self.post(action, product=999)
                self.assertEqual(response.status_code, 400)
                self.assertIn('product', response.json())

    def test_basket_of_another_session(self):
        other = StorefrontClient()
        self.assertEqual(other.get('/api/v0/baskets/').json(), [])
        self.assertEqual(other.get(f'/api/v0/baskets/{self.basket}/').status_code, 404)
        self.assertEqual(self.post('add', client=other, product=1).status_code, 404)
        self.assertEqual(self.items(), {})

    def test_add_stops_at_the_largest_quantity(self):
        self.post('add', product=1, quantity=32000)
        self.assertEqual(self.post('add', product=1, quantity=32000).status_code, 204)
        self.assertEqual(self.items(), {1: 32767})

    def test_update_without_quantity_keeps_it(self):
        self.post('add', product=1, quantity=3)
        self.post('update', product=1)
        self.post('update', product=2)
        self.assertEqual(self.items(), {1: 3, 2: 1})

    def test_cannot_be_deleted_or_replaced(self):
        path = f'/api/v0/baskets/{self.basket}/'
        self.assertEqual(self.client.delete(path).status_code, 405)
        self.assertEqual(self.client.put(path, {}, format='json').status_code, 405)
        self.assertEqual(self.client.patch(path, {}, format='json').status_code, 405)
        self.assertTrue(Basket.objects.filter(pk=self.basket).exists())


class BasketRaceTests(TransactionTestCase):
    """ A storefront can send requests of one session at once, a double tap or a request sent twice on the way """
    serialized_rollback = True  # the current Site from migrations, which an earlier TransactionTestCase flushes

    def setUp(self):
        add_storefront_key()
        add_product(1)
        self.client = StorefrontClient()
        self.client.post('/api/v0/baskets/', format='json')  # starts the session

    def at_once(self, path, body=None, times=6):
        """ Posts the request from several threads at once, in the session of self.client """
        barrier = threading.Barrier(times)
        statuses = []

        def post():
            client = StorefrontClient()
            client.cookies = copy.deepcopy(self.client.cookies)
            barrier.wait()
            try:
                statuses.append(client.post(path, body, format='json').status_code)
            finally:
                connection.close()

        threads = [threading.Thread(target=post) for _ in range(times)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        return statuses

    def test_basket_created_once(self):
        Basket.objects.all().delete()
        for _ in range(5):
            self.assertEqual(self.at_once('/api/v0/baskets/'), [201] * 6)
            self.assertEqual(Basket.objects.count(), 1)
            Basket.objects.all().delete()

    def test_additions_counted_in_one_item(self):
        basket = Basket.objects.get()
        for _ in range(5):
            self.assertEqual(self.at_once(f'/api/v0/baskets/{basket.id}/add/', {'product': 1}), [204] * 6)
            self.assertEqual(list(BasketItem.objects.values_list('product', 'quantity')), [(1, 6)])
            BasketItem.objects.all().delete()

    def test_updates_make_one_item(self):
        basket = Basket.objects.get()
        for _ in range(5):
            self.assertEqual(self.at_once(f'/api/v0/baskets/{basket.id}/update/', {'product': 1, 'quantity': 2}), [204] * 6)
            self.assertEqual(list(BasketItem.objects.values_list('product', 'quantity')), [(1, 2)])
            BasketItem.objects.all().delete()


class FavoritesTests(Base):
    def setUp(self):
        super().setUp()
        self.user = ShopUser.objects.create(phone='+79161234567')
        self.client = signed_in(self.user)

    def post(self, action, product, client=None):
        return (client or self.client).post(f'/api/v0/favorites/{action}/', {'product': product}, format='json')

    def favorites(self):
        return self.client.get('/api/v0/favorites/').json()

    def test_add_and_remove(self):
        self.assertEqual(self.post('add', 1).status_code, 204)
        self.post('add', 2)
        self.post('add', 1)
        self.assertEqual(self.favorites(), [1, 2])
        self.assertEqual(self.post('remove', 1).status_code, 204)
        self.assertEqual(self.post('remove', 1).status_code, 204)
        self.assertEqual(self.favorites(), [2])

    def test_per_user_and_site(self):
        other_site = Site.objects.create(domain='other.test', name='other')
        Favorites.objects.create(user=self.user, site=other_site, product_id=1)
        Favorites.objects.create(user=ShopUser.objects.create(phone='+79160000000'), site=self.site, product_id=2)
        self.assertEqual(self.favorites(), [])

    def test_unknown_product(self):
        response = self.post('add', 999)
        self.assertEqual(response.status_code, 400)
        self.assertIn('product', response.json())

    def test_anonymous(self):
        anonymous = StorefrontClient()
        self.assertEqual(anonymous.get('/api/v0/favorites/').status_code, 403)
        self.assertEqual(self.post('add', 1, client=anonymous).status_code, 403)
        self.assertFalse(Favorites.objects.exists())

    def test_only_add_and_remove_change_them(self):
        self.post('add', 1)
        favorite = Favorites.objects.get()
        self.assertEqual(self.client.post('/api/v0/favorites/', {'product': 2}, format='json').status_code, 405)
        self.assertEqual(self.client.put(f'/api/v0/favorites/{favorite.id}/', {'product': 2}, format='json').status_code, 405)
        self.assertEqual(self.client.delete(f'/api/v0/favorites/{favorite.id}/').status_code, 405)
        self.assertEqual(self.favorites(), [1])


class ComparisonTests(Base):
    def post(self, action, product, client=None):
        return (client or self.client).post(f'/api/v0/comparisons/{action}/', {'product': product}, format='json')

    def compared(self, client=None, **params):
        return (client or self.client).get('/api/v0/comparisons/', params).json()

    def test_add_and_remove(self):
        self.assertEqual(self.compared(), [])
        self.assertEqual(self.post('add', 1).json(), [1])
        self.assertEqual(self.post('add', 2).json(), [1, 2])
        self.assertEqual(self.post('add', 1).json(), [1, 2])
        self.assertEqual(self.compared(), [1, 2])
        self.assertEqual(self.post('remove', 1).json(), [2])
        self.assertEqual(self.post('remove', 2).json(), [])
        self.assertEqual(self.compared(), [])
        self.assertEqual(self.post('remove', 2).json(), [])

    def test_kept_in_the_session(self):
        self.post('add', 1)
        self.assertEqual(self.compared(client=StorefrontClient()), [])

    def test_products_of_a_kind(self):
        overlock = ProductKind.objects.create(name='Оверлок', comparison=[])
        Product.objects.get(pk=2).kind.add(overlock)
        self.post('add', 1)
        self.post('add', 2)
        self.assertEqual(self.compared(kind=overlock.id), [2])
        response = self.client.get('/api/v0/comparisons/', {'kind': 'abc'})
        self.assertEqual((response.status_code, response.json()), (400, {'kind': ['Неверное значение']}))

    def test_unknown_product(self):
        response = self.post('add', 999)
        self.assertEqual((response.status_code, response.json()), (400, {'product': ['Product does not exist']}))
