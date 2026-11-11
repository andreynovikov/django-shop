"""
Orders, serial numbers of the products bought and warranty cards. See settings.py on how to run.
"""
import copy
import threading
from types import SimpleNamespace
from unittest import mock

from django.contrib.sites.models import Site
from django.db import connection, transaction
from django.test import TestCase, TransactionTestCase
from django.utils import timezone

from rest_framework.authtoken.models import Token
from yookassa import Configuration

from sewingworld.models import SiteProfile
from shop.models import Basket, Contractor, Order, Product, Serial, ShopUser

from .clients import StorefrontClient, add_storefront_key, count_queries, signed_in
from .fixtures import add_marketplace_sites, add_product

PHONE = '+79161234567'


class Shop:
    def setUp(self):
        add_storefront_key()
        add_marketplace_sites()
        self.site = Site.objects.get_current()
        self.seller = Contractor.objects.create(code='seller', name='ООО Продавец', vat_rate=Contractor.VAT_RATE_20,
                                                tax_system=Contractor.TAX_SYSTEM_GTS)
        for target, new in (
            # Constance refuses the local-memory cache of the tests
            ('shop.models.order.config', SimpleNamespace(sw_default_seller=self.seller.pk)),
            ('shop.signals.logger', mock.Mock()),  # logs every product put in an order
        ):
            patcher = mock.patch(target, new=new)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.user = ShopUser.objects.create(phone=PHONE, name='Покупатель', phone_verified=True)
        self.client = signed_in(self.user)
        self.machine = add_product(1, title='Janome 1225s', price=20000)
        self.needles = add_product(2, title='Иглы', price=300)

    def order(self, **fields):
        fields.setdefault('user', self.user)
        fields.setdefault('site', self.site)
        fields.setdefault('seller', self.seller)
        return Order.objects.create(**fields)

    def ids(self, path='/api/v0/orders/', **params):
        response = self.client.get(path, params)
        self.assertEqual(response.status_code, 200, response.content)
        return [order['id'] for order in response.json()['results']]


class Base(Shop, TestCase):
    pass


class ListTests(Base):
    def test_own_orders_newest_first(self):
        first, second = self.order(), self.order()
        self.order(user=ShopUser.objects.create(phone='+79160000000'))
        self.assertEqual(self.ids(), [second.id, first.id])

    def test_by_status(self):
        new = self.order()
        done = self.order(status=Order.STATUS_DONE)
        finished = self.order(status=Order.STATUS_FINISHED)
        canceled = self.order(status=Order.STATUS_CANCELED)
        self.assertEqual(self.ids(filter='active'), [new.id])
        self.assertEqual(self.ids(filter='done'), [finished.id, done.id])
        self.assertEqual(self.ids(filter='canceled'), [canceled.id])

    def test_by_site(self):
        self.order()
        there = self.order(site=Site.objects.create(domain='other.test', name='other'))
        self.assertEqual(self.ids(site=there.site_id), [there.id])
        response = self.client.get('/api/v0/orders/', {'site': 'abc'})
        self.assertEqual((response.status_code, response.json()), (400, {'site': ['Неверное значение']}))

    def test_anonymous(self):
        self.assertEqual(StorefrontClient().get('/api/v0/orders/').status_code, 403)

    def test_queries_do_not_grow_with_the_orders(self):
        def add_order():
            order = self.order()
            order.items.create(product=self.machine, product_price=20000)
            order.items.create(product=self.needles, product_price=300, quantity=2)
            return order

        def queries():
            Product.objects.update(num=5)  # adding to an order resets the stock, the order page would count it
            return count_queries(lambda: self.client.get('/api/v0/orders/'), lambda: self.client.get(f'/api/v0/orders/{order.id}/'))

        order = add_order()
        few = queries()
        for _ in range(3):
            add_order()
        order.items.create(product=add_product(3), product_price=100)
        self.assertEqual(queries(), few)
        self.assertEqual(self.client.get('/api/v0/orders/').json()['results'][-1]['total'], 20700)


class RetrieveTests(Base):
    def test_own_order(self):
        order = self.order(delivery_price=500, payment=Order.PAYMENT_CARD)
        order.items.create(product=self.machine, product_price=20000, quantity=2)
        data = self.client.get(f'/api/v0/orders/{order.id}/').json()
        self.assertEqual((data['total'], data['status_text'], data['payment_text']), (40500, 'новый заказ', 'банковская карта'))
        self.assertEqual([(item['product']['id'], item['quantity'], item['price']) for item in data['items']], [(1, 2, 40000)])

    def test_order_of_another_user(self):
        order = self.order(user=ShopUser.objects.create(phone='+79160000000'))
        self.assertEqual(self.client.get(f'/api/v0/orders/{order.id}/').status_code, 404)

    def test_cannot_be_deleted(self):
        order = self.order()
        self.assertEqual(self.client.delete(f'/api/v0/orders/{order.id}/').status_code, 405)
        self.assertTrue(Order.objects.filter(pk=order.pk).exists())


class CreateTests(Base):
    def setUp(self):
        super().setUp()
        patcher = mock.patch.multiple('sewingworld.api.orders', notify_user_order_new_mail=mock.DEFAULT, notify_user_order_new_sms=mock.DEFAULT)
        self.notices = patcher.start()
        self.addCleanup(patcher.stop)

    def fill_basket(self):
        basket = self.client.post('/api/v0/baskets/').json()['id']
        self.client.post(f'/api/v0/baskets/{basket}/add/', {'product': 1, 'quantity': 2}, format='json')
        self.client.post(f'/api/v0/baskets/{basket}/add/', {'product': 2}, format='json')

    def test_basket_becomes_an_order(self):
        self.fill_basket()
        response = self.client.post('/api/v0/orders/')
        self.assertEqual(response.status_code, 200)
        order = Order.objects.get()
        self.assertEqual((response.json()['id'], response.json()['total']), (order.id, 40300))
        self.assertEqual((order.user, order.site, order.seller, order.name, order.phone), (self.user, self.site, self.seller, 'Покупатель', PHONE))
        self.assertEqual([(item.product_id, item.quantity) for item in order.items.all()], [(1, 2), (2, 1)])
        self.assertFalse(Basket.objects.exists())
        for notice in self.notices.values():
            notice.apply_async.assert_called_once_with((order.id,), countdown=300)

    def test_promo_discount_is_used_up(self):
        session = self.client.session
        session['discount'] = 5
        session.save()
        self.fill_basket()
        order = Order.objects.get(pk=self.client.post('/api/v0/orders/').json()['id'])
        self.assertEqual([item.pct_discount for item in order.items.all()], [5, 5])
        self.assertNotIn('discount', self.client.session)

    def test_without_a_basket(self):
        response = self.client.post('/api/v0/orders/')
        self.assertEqual((response.status_code, response.json()), (400, 'Basket does not exist'))

    def test_empty_basket(self):
        self.client.post('/api/v0/baskets/')
        response = self.client.post('/api/v0/orders/')
        self.assertEqual((response.status_code, response.json()), (400, 'Basket is empty'))
        self.assertFalse(Order.objects.exists())

    def test_caller_without_a_session_gets_no_basket_of_ended_sessions(self):
        for _ in range(2):
            Basket.objects.create(site=self.site).items.create(product=self.machine)
        token = Token.objects.create(user=self.user)
        response = StorefrontClient(headers={'Authorization': f'Token {token.key}'}).post('/api/v0/orders/')
        self.assertEqual((response.status_code, response.json()), (400, 'Basket does not exist'))
        self.assertFalse(Order.objects.exists())

    def test_anonymous(self):
        self.assertEqual(StorefrontClient().post('/api/v0/orders/').status_code, 403)


class CreateRaceTests(Shop, TransactionTestCase):
    """ The storefront has sent the request to order a basket several times at once """
    serialized_rollback = True  # the current Site from migrations, which an earlier TransactionTestCase flushes

    def setUp(self):
        super().setUp()
        patcher = mock.patch.multiple('sewingworld.api.orders', notify_user_order_new_mail=mock.DEFAULT, notify_user_order_new_sms=mock.DEFAULT)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_basket_ordered_once(self):
        for _ in range(3):
            basket = self.client.post('/api/v0/baskets/').json()['id']
            self.client.post(f'/api/v0/baskets/{basket}/add/', {'product': 1}, format='json')
            barrier = threading.Barrier(4)
            statuses = []

            def post():
                client = StorefrontClient()
                client.cookies = copy.deepcopy(self.client.cookies)
                barrier.wait()
                try:
                    statuses.append(client.post('/api/v0/orders/').status_code)
                finally:
                    connection.close()

            threads = [threading.Thread(target=post) for _ in range(4)]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()
            self.assertEqual(sorted(statuses), [200, 400, 400, 400])
            self.assertEqual(Order.objects.count(), 1)
            self.assertFalse(Basket.objects.exists())
            Order.objects.all().delete()


class PreorderTests(Base):
    def preorder(self, body):
        return self.client.post('/api/v0/orders/preorder/', body, format='json')

    def test_order_for_the_product(self):
        response = self.preorder({'product': 1})
        self.assertEqual(response.status_code, 200)
        order = Order.objects.get()
        self.assertEqual((response.json()['id'], order.comment), (order.id, 'Запрос о поступлении'))
        self.assertEqual([(item.product_id, item.quantity) for item in order.items.all()], [(1, 1)])
        self.assertFalse(Basket.objects.exists())

    def test_basket_of_the_session_stays(self):
        basket = self.client.post('/api/v0/baskets/').json()['id']
        self.client.post(f'/api/v0/baskets/{basket}/add/', {'product': 2}, format='json')
        self.preorder({'product': 1})
        self.assertEqual([item['product']['id'] for item in self.client.get(f'/api/v0/baskets/{basket}/').json()['items']], [2])

    def test_unknown_product(self):
        for body in ({'product': 999}, {'product': 'abc'}, {}):
            with self.subTest(body):
                response = self.preorder(body)
                self.assertEqual(response.status_code, 400)
                self.assertIn('product', response.json())
        self.assertFalse(Order.objects.exists())
        self.assertFalse(Basket.objects.exists())


class PayTests(Base):
    def setUp(self):
        super().setUp()
        SiteProfile.objects.filter(site=self.site).update(yookassa_id='shop-account', yookassa_key='shop-key')
        patcher = mock.patch('yandex_kassa.views.Payment')
        self.payment = patcher.start()
        self.addCleanup(patcher.stop)
        self.payment.create.return_value.confirmation.confirmation_url = 'https://yookassa.test/pay'
        patcher = mock.patch.multiple(Configuration, account_id=None, secret_key=None)  # set by the view
        patcher.start()
        self.addCleanup(patcher.stop)
        self.unpaid = self.order(payment=Order.PAYMENT_CARD, delivery_price=500)
        self.unpaid.items.create(product=self.machine, product_price=20000)

    def pay(self, order, **body):
        return self.client.post(f'/api/v0/orders/{order.id}/pay/', body, format='json')

    def test_payment_link(self):
        response = self.pay(self.unpaid, return_url='https://shop.test/thanks/')
        self.assertEqual(response.json(), {'location': 'https://yookassa.test/pay'})
        details = self.payment.create.call_args.args[0]
        self.assertEqual(details['amount'], {'value': '20500', 'currency': 'RUB'})
        self.assertEqual([item['amount']['value'] for item in details['receipt']['items']], ['20000', '500'])
        self.assertEqual(details['confirmation']['return_url'], 'https://shop.test/thanks/')
        self.assertEqual(details['metadata'], {'order_id': self.unpaid.id, 'user_id': self.user.id})
        self.assertEqual((Configuration.account_id, Configuration.secret_key), ('shop-account', 'shop-key'))

    def test_returns_to_the_order_by_default(self):
        self.pay(self.unpaid)
        details = self.payment.create.call_args.args[0]
        self.assertEqual(details['confirmation']['return_url'], f'https://example.com/user/orders/{self.unpaid.id}/')

    def test_order_of_another_user(self):
        order = self.order(user=ShopUser.objects.create(phone='+79160000000'))
        self.assertEqual(self.pay(order).status_code, 404)
        self.payment.create.assert_not_called()


class LastAndUnpaidTests(Base):
    def post(self, action):
        return self.client.post(f'/api/v0/orders/{action}/').json()

    def test_last_order_in_work(self):
        self.assertEqual(self.post('last'), {'id': None})
        in_work = self.order()
        for status in (Order.STATUS_DONE, Order.STATUS_FINISHED, Order.STATUS_CANCELED):
            self.order(status=status)
        self.order(user=ShopUser.objects.create(phone='+79160000000'))
        self.assertEqual(self.post('last'), {'id': in_work.id})

    def test_unpaid_collected_order(self):
        self.assertEqual(self.post('unpaid'), {'id': None})
        unpaid = self.order(status=Order.STATUS_COLLECTED, payment=Order.PAYMENT_CARD)
        self.order(status=Order.STATUS_COLLECTED, payment=Order.PAYMENT_CARD, paid=True)
        self.order(status=Order.STATUS_COLLECTED, payment=Order.PAYMENT_CASH)
        self.order(status=Order.STATUS_ACCEPTED, payment=Order.PAYMENT_TRANSFER)
        self.assertEqual(self.post('unpaid'), {'id': unpaid.id})


class WarrantyCardTests(Base):
    def test_card_of_a_product_sold(self):
        self.order().items.create(product=self.machine, product_price=20000, serial_number='SN123')
        response = StorefrontClient().get('/api/v0/warrantycard/%20SN123%20/')
        self.assertEqual(response.status_code, 200)
        html = response.json()['html']
        for text in ('SN123', 'Janome 1225s', 'ООО Продавец'):
            self.assertIn(text, html)

    def test_serial_number_in_any_case(self):
        self.order().items.create(product=self.machine, product_price=20000, serial_number='SN123ab')
        self.assertEqual(StorefrontClient().get('/api/v0/warrantycard/sn123AB/').status_code, 200)

    def test_unknown_serial_number(self):
        response = StorefrontClient().get('/api/v0/warrantycard/SN404/')
        self.assertEqual(response.status_code, 400)
        self.assertIn('code', response.json())


class SerialTests(Base):
    def register(self, number, client=None):
        return (client or self.client).post('/api/v0/serials/', {'number': number}, format='json')

    def test_serial_of_own_order_is_approved(self):
        order = self.order()
        order.items.create(product=self.machine, product_price=20000, serial_number='SN1')
        response = self.register('sn1')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json(), {
            'number': 'sn1', 'purchase_date': str(timezone.localdate(order.created)), 'product': 1, 'order': order.id, 'approved': True,
        })

    def test_unknown_serial_waits_for_a_check(self):
        self.assertEqual(self.register('SN2').json(), {'number': 'SN2', 'purchase_date': None, 'product': None, 'order': None, 'approved': False})

    def test_own_serials(self):
        Serial.objects.create(number='SN3', user=ShopUser.objects.create(phone='+79160000000'))
        self.register('SN4')
        self.assertEqual([serial['number'] for serial in self.client.get('/api/v0/serials/').json()], ['SN4'])

    def test_blank(self):
        self.assertEqual(self.register('  ').status_code, 400)
        self.assertFalse(Serial.objects.exists())

    def test_cannot_be_changed_or_deleted(self):
        self.register('SN5')
        serial = Serial.objects.get()
        self.assertEqual(self.client.put(f'/api/v0/serials/{serial.id}/', {'number': 'SN6'}, format='json').status_code, 405)
        self.assertEqual(self.client.delete(f'/api/v0/serials/{serial.id}/').status_code, 405)
        self.assertEqual(Serial.objects.get().number, 'SN5')

    def test_anonymous(self):
        self.assertEqual(self.register('SN7', client=StorefrontClient()).status_code, 403)

    def test_registered_once(self):
        self.register('SN8')
        other = signed_in(ShopUser.objects.create(phone='+79160000000'))
        # Serial.register() relies on autocommit to go on after the failed insert, the test runs in a transaction
        with transaction.atomic():
            response = self.register('SN8', client=other)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Serial.objects.get().user, self.user)
