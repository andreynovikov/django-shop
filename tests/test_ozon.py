from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from unittest import expectedFailure
from unittest.mock import call, patch

from django.contrib.sites.models import Site
from django.test import TestCase

from ozon import tasks
from sewingworld.models import SiteProfile
from shop.models import Basket, Contractor, Integration, Order, Product, ProductIntegration, ShopUser

from .fixtures import add_marketplace_sites, add_product
from .marketplace_api import OpenAPIMock, load_spec


SPEC = load_spec('marketplaces/ozon.json')
POSTINGS = '/v4/posting/fbs/list'
STOCKS = '/v2/products/stocks'
NOW = datetime(2026, 11, 25, 12, tzinfo=UTC)
POSTING_REQUEST = {
    'sort_dir': 'DESC',
    'filter': {
        'since': (NOW - timedelta(days=7)).isoformat(),
        'to': NOW.isoformat(),
        'statuses': ['awaiting_registration', 'awaiting_approve', 'awaiting_packaging', 'awaiting_deliver', 'delivering', 'delivered'],
    },
    'limit': 100,
    'with': {'analytics_data': True, 'financial_data': True, 'barcodes': True},
}


def posting(number, **fields):
    return {
        'posting_number': number, 'status': 'awaiting_packaging', 'shipment_date': '2026-11-26T12:00:00Z',
        'products': [{'offer_id': 'machine', 'sku': 234, 'quantity': 2, 'price': {'amount': '850.50', 'currency': 'RUB'}}],
        **fields,
    }


class OzonTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        add_marketplace_sites()
        site = Site.objects.get(domain='ozon.ru')
        SiteProfile.objects.create(site=site)
        seller = Contractor.objects.create(code='ozon-seller', name='Продавец')
        cls.integration = Integration.objects.create(
            name='Ozon', utm_source='ozon', source_site=site, target_site=Site.objects.get_current(),
            uses_api=True, enabled=True, seller=seller,
            settings={
                'client_id': '42', 'api_key': 'test-ozon-key',
                'warehouses': [{'id': 101}, {'id': 102, 'is_express': True}],
            },
        )
        cls.user = ShopUser.objects.create(phone='0002')
        cls.product = add_product(1, article='machine')

    def setUp(self):
        self.market = OpenAPIMock(self, {'Client-Id': '42', 'Api-Key': 'test-ozon-key'})
        self.enterContext(patch('ozon.tasks.urlopen', side_effect=self.market))

    def expect_postings(self, postings, *, cursor=None, next_cursor=None):
        body = POSTING_REQUEST if cursor is None else {**POSTING_REQUEST, 'cursor': cursor}
        response = {'has_next': next_cursor is not None, 'cursor': next_cursor or '', 'postings': postings}
        self.market.expect(SPEC, POSTINGS, 'POST', response, body=body)

    def poll(self):
        with patch('ozon.tasks.timezone.now', return_value=NOW):
            return tasks.get_integration_unfulfilled_orders.run(self.integration.utm_source, target_site_id=self.integration.target_site_id)

    def test_paginates_and_imports_express_and_standard_postings(self):
        express = posting(
            '123-1-1', is_express=True, scanit='BARCODE',
            analytics_data={'city': 'Москва', 'region': 'Центральный округ', 'delivery_date_end': '2026-11-29T12:00:00Z'},
        )
        standard = posting('123-1-2')
        self.expect_postings([express], next_cursor='next/+page')
        self.expect_postings([standard], cursor='next/+page')
        self.assertEqual(self.poll(), 2)

        order = Order.objects.get(integration=self.integration, delivery_tracking_number='123-1-1')
        self.assertEqual((order.user, order.site, order.delivery), (self.user, self.integration.source_site, Order.DELIVERY_EXPRESS))
        self.assertEqual((order.delivery_dispatch_date, order.delivery_handing_date), (date(2026, 11, 26), date(2026, 11, 29)))
        self.assertEqual((order.city, order.address, order.meta['barcode']), ('Москва', 'Центральный округ, Москва', 'BARCODE'))
        line = order.items.get()
        self.assertEqual((line.product, line.quantity, line.val_discount), (self.product, 2, Decimal('149.50')))

        other = Order.objects.get(integration=self.integration, delivery_tracking_number='123-1-2')
        self.assertEqual(other.delivery, Order.DELIVERY_UNKNOWN)
        self.assertEqual(Basket.objects.filter(secondary=True).count(), 2)

    def test_updates_existing_posting_metadata_without_duplicating_items(self):
        remote = posting('123-1-1', scanit='before')
        self.expect_postings([remote])
        self.assertEqual(self.poll(), 1)
        order = Order.objects.get(integration=self.integration, delivery_tracking_number='123-1-1')
        line = order.items.get()
        order.meta['staff_note'] = 'keep'
        order.save(update_fields=['meta'])

        self.expect_postings([{**remote, 'scanit': 'after', 'analytics_data': {'city': 'Казань', 'region': 'Казань'}}])
        self.assertEqual(self.poll(), 1)
        order.refresh_from_db()
        self.assertEqual(order.meta, {'barcode': 'after', 'staff_note': 'keep'})
        self.assertEqual((order.city, order.address), ('Казань', 'Казань'))
        self.assertEqual(order.items.get().pk, line.pk)
        self.assertEqual(Basket.objects.filter(secondary=True).count(), 1)

    def test_reports_posting_api_error_without_importing_orders(self):
        self.market.expect(SPEC, POSTINGS, 'POST', {'code': 3, 'message': 'Invalid filter'}, body=POSTING_REQUEST, status=400)
        with self.assertLogs('ozon', 'ERROR'), self.assertRaisesRegex(tasks.TaskFailure, 'Invalid filter'):
            self.poll()
        self.assertFalse(Order.objects.exists())

    def send_stock(self, product):
        with patch.object(Product, 'get_stocks', side_effect=[{product.pk: 24}, {product.pk: -3}]) as count:
            tasks.notify_product_stocks.run([product.pk], self.integration.utm_source, target_site_id=self.integration.target_site_id)
        self.assertEqual(count.call_args_list, [
            call([product.pk], integration=self.integration), call([product.pk], integration=self.integration, express=True),
        ])

    def expect_stock_update(self, *, updated=True):
        body = {'stocks': [
            {'offer_id': 'machine', 'stock': 20, 'warehouse_id': 101},
            {'offer_id': 'machine', 'stock': 0, 'warehouse_id': 102},
        ]}
        response = {'result': [
            {'offer_id': 'machine', 'warehouse_id': 101, 'updated': updated,
             'errors': [] if updated else [{'code': 'TOO_MANY_REQUESTS', 'message': 'Try again'}]},
            {'offer_id': 'machine', 'warehouse_id': 102, 'updated': True, 'errors': []},
        ]}
        self.market.expect(SPEC, STOCKS, 'POST', response, body=body)

    def test_updates_standard_and_express_stocks_and_clears_the_notification_flag(self):
        link = ProductIntegration.objects.create(product=self.product, integration=self.integration, notify_stock=True)
        self.expect_stock_update()
        self.send_stock(self.product)
        link.refresh_from_db()
        self.assertFalse(link.notify_stock)

    @expectedFailure
    def test_keeps_stock_pending_when_ozon_rejects_one_warehouse(self):
        link = ProductIntegration.objects.create(product=self.product, integration=self.integration, notify_stock=True)
        self.expect_stock_update(updated=False)
        self.send_stock(self.product)
        link.refresh_from_db()
        # The task currently clears this flag even when a result row has updated=false.
        self.assertTrue(link.notify_stock)
