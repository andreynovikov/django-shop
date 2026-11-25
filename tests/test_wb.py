from datetime import UTC, datetime
from unittest import expectedFailure
from unittest.mock import patch

from django.contrib.sites.models import Site
from django.test import TestCase

from sewingworld.models import SiteProfile
from shop.models import Basket, Contractor, Integration, Order, Product, ProductIntegration, ShopUser
from wb import tasks

from .fixtures import add_marketplace_sites, add_product
from .marketplace_api import OpenAPIMock, load_spec


ITEMS = load_spec('marketplaces/wb_items.json')
ORDERS = load_spec('marketplaces/wb_orders.json')
WAREHOUSES = '/api/v3/warehouses'
NEW_ORDERS = '/api/v3/orders/new'
ORDER_LIST = '/api/v3/orders'
STATUSES = '/api/v3/orders/status'
CARDS = '/content/v2/get/cards/list'
STOCKS = '/api/v3/stocks/{warehouseId}'
NOW = datetime(2026, 11, 25, 12, tzinfo=UTC)


def order_data(order_id, warehouse_id, *skus):
    return {
        'id': order_id, 'warehouseId': warehouse_id, 'skus': list(skus),
        'deliveryType': 'fbs', 'createdAt': '2026-11-25T11:55:00Z', 'comment': 'Комментарий',
    }


class WildberriesTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        add_marketplace_sites()
        site = Site.objects.get(domain='wildberries.ru')
        SiteProfile.objects.create(site=site)
        seller = Contractor.objects.create(code='wb-seller', name='Продавец')
        cls.integration = Integration.objects.create(
            name='Wildberries', utm_source='wb', source_site=site, target_site=Site.objects.get_current(),
            uses_api=True, enabled=True, seller=seller, settings={'warehouse_id': 101, 'api_key': 'test-wb-key'},
        )
        cls.user = ShopUser.objects.create(phone='0003')
        cls.product = add_product(1, article='machine', gtin='4603743187500', gtins=['4603743187517'])
        cls.product_link = ProductIntegration.objects.create(product=cls.product, integration=cls.integration, notify_stock=True)

    def setUp(self):
        self.market = OpenAPIMock(self, {'Authorization': 'test-wb-key'})
        self.enterContext(patch('wb.tasks.urlopen', side_effect=self.market))

    def run_task(self, task, *args, **kwargs):
        return task.run(*args, self.integration.utm_source, target_site_id=self.integration.target_site_id, **kwargs)

    def expect_warehouses(self, *, detached=True):
        warehouses = [{'id': 101, 'name': 'Основной склад'}]
        if detached:
            warehouses.append({'id': 102, 'name': 'Другой склад'})
        self.market.expect(ITEMS, WAREHOUSES, 'GET', warehouses)

    def local_order(self, market_id, status=Order.STATUS_NEW):
        return Order.objects.create(
            user=self.user, site=self.integration.source_site, integration=self.integration,
            delivery_tracking_number=str(market_id), status=status,
        )

    def test_imports_new_orders_by_gtin_or_alternate_sku_and_flags_missing_products(self):
        main = order_data(555, 101, self.product.gtin)
        detached = order_data(556, 102, self.product.gtins[0], '4603743187524')
        # The same GTIN can exist outside this marketplace's catalog.
        add_product(2, gtin=self.product.gtin)
        self.expect_warehouses()
        self.market.expect(ORDERS, NEW_ORDERS, 'GET', {'orders': [main, detached]})
        with self.assertLogs('wb', 'ERROR'):
            self.assertEqual(self.run_task(tasks.get_integration_new_orders), 2)

        first = Order.objects.get(integration=self.integration, delivery_tracking_number='555')
        self.assertEqual((first.user, first.site, first.status),
                         (self.user, self.integration.source_site, Order.STATUS_NEW))
        self.assertEqual(first.items.get().product, self.product)
        second = Order.objects.get(integration=self.integration, delivery_tracking_number='556')
        self.assertEqual((second.status, second.manager_comment, second.comment),
                         (Order.STATUS_DELIVERED_STORE, 'Другой склад', 'Комментарий'))
        self.assertEqual(second.items.get().product, self.product)
        self.assertTrue(second.alert)

        self.expect_warehouses()
        self.market.expect(ORDERS, NEW_ORDERS, 'GET', {'orders': [main, detached]})
        self.assertEqual(self.run_task(tasks.get_integration_new_orders), 0)
        self.assertEqual(Basket.objects.filter(secondary=True).count(), 2)

    def test_imports_only_other_warehouses_from_recent_order_list(self):
        self.expect_warehouses()
        result = {'next': 0, 'orders': [order_data(555, 101, self.product.gtin), order_data(556, 102, self.product.gtin)]}
        query = {'limit': ['1000'], 'next': ['0'], 'dateFrom': [str(int(NOW.timestamp()) - 30 * 60)]}
        self.market.expect(ORDERS, ORDER_LIST, 'GET', result, query=query)
        with patch('wb.tasks.datetime') as clock:
            clock.now.return_value = NOW
            self.assertEqual(self.run_task(tasks.get_integration_detached_orders), 1)

        order = Order.objects.get(integration=self.integration)
        self.assertEqual((order.delivery_tracking_number, order.status, order.manager_comment),
                         ('556', Order.STATUS_DELIVERED_STORE, 'Другой склад'))
        self.assertEqual(order.items.get().product, self.product)

    def test_reports_new_order_api_rate_limit(self):
        self.expect_warehouses()
        self.market.expect(ORDERS, NEW_ORDERS, 'GET', {'status': 429, 'detail': 'Rate limit reached'}, status=429)
        with self.assertLogs('wb', 'ERROR'), self.assertRaisesRegex(tasks.TaskFailure, 'Rate limit reached'):
            self.run_task(tasks.get_integration_new_orders)
        self.assertFalse(Order.objects.exists())

    def expect_status(self, status):
        self.market.expect(ORDERS, STATUSES, 'POST', {
            'orders': [{'id': 555, 'supplierStatus': 'complete', 'wbStatus': status}],
        }, body={'orders': [555]})

    def test_polls_open_orders_and_queues_completion_or_cancellation(self):
        order = self.local_order(555)
        self.local_order(556, status=Order.STATUS_DONE)
        cases = (
            (Order.STATUS_NEW, 'sold', {'status': Order.STATUS_DONE}),
            (Order.STATUS_NEW, 'canceled_by_client', {'status': Order.STATUS_CANCELED}),
            (Order.STATUS_COLLECTING, 'canceled_by_client', {'alert': 'canceled_by_client'}),
            (Order.STATUS_COLLECTING, 'waiting', None),
        )
        for local, remote, update in cases:
            with self.subTest(local=local, remote=remote):
                order.status = local
                order.save(update_fields=['status'])
                self.expect_status(remote)
                with patch('wb.tasks.update_order.delay') as enqueue:
                    self.assertEqual(self.run_task(tasks.get_integration_order_statuses), int(update is not None))
                if update is None:
                    enqueue.assert_not_called()
                else:
                    enqueue.assert_called_once_with(order.pk, update)

    @expectedFailure
    def test_queues_arrival_for_the_documented_pickup_status(self):
        order = self.local_order(555, status=Order.STATUS_COLLECTING)
        self.expect_status('ready_for_pickup')
        with patch('wb.tasks.update_order.delay') as enqueue:
            self.run_task(tasks.get_integration_order_statuses)
        # The task currently maps ready_to_pickup while the API sends ready_for_pickup.
        enqueue.assert_called_once_with(order.pk, {'status': Order.STATUS_DELIVERED_STORE})

    def expect_card_lookup(self, response, *, status=200):
        query = {'settings': {'filter': {'textSearch': self.product.gtin, 'withPhoto': -1}}}
        self.market.expect(ITEMS, CARDS, 'POST', response, body=query, status=status)

    def expect_stock(self, *, amount):
        self.market.expect(ITEMS, STOCKS, 'PUT', None, status=204, path_params={'warehouseId': 101},
                           body={'stocks': [{'chrtId': 42, 'amount': amount}]})

    def test_resolves_size_id_uploads_stock_and_reuses_the_cached_id(self):
        self.expect_card_lookup({'cards': [{'sizes': [
            {'chrtID': 41, 'skus': ['4603743187524']},
            {'chrtID': 42, 'skus': [self.product.gtin]},
        ]}]})
        self.expect_stock(amount=20)
        with patch('wb.tasks.sleep'), patch.object(Product, 'get_stocks', return_value={self.product.pk: 25}) as count:
            self.assertTrue(self.run_task(tasks.notify_product_stocks, [self.product.pk]))
        count.assert_called_once_with([self.product.pk], integration=self.integration)
        self.product_link.refresh_from_db()
        self.assertEqual(self.product_link.meta, {'chrtID': 42})
        self.assertFalse(self.product_link.notify_stock)

        self.expect_stock(amount=0)
        with patch.object(Product, 'get_stocks') as count:
            self.assertTrue(self.run_task(tasks.notify_product_stocks, [self.product.pk], zero_out=True))
        count.assert_not_called()

    def test_keeps_stock_pending_when_card_lookup_is_rate_limited(self):
        self.expect_card_lookup({'status': 429, 'detail': 'Rate limit reached'}, status=429)
        with patch('wb.tasks.sleep'), self.assertLogs('wb', 'ERROR'):
            self.assertFalse(self.run_task(tasks.notify_product_stocks, [self.product.pk]))
        self.product_link.refresh_from_db()
        self.assertTrue(self.product_link.notify_stock)
        self.assertIsNone(self.product_link.meta)
