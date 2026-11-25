from datetime import date, time
from decimal import Decimal
from unittest.mock import patch

from django.contrib.sites.models import Site
from django.test import TestCase

from beru.tasks import MarketUnavailable, TaskFailure, get_integration_orders, get_orders, notify_beru_order_status
from sewingworld.models import SiteProfile
from shop.models import Basket, Box, Contractor, Integration, Order, ShopUser

from .fixtures import add_marketplace_sites, add_product
from .marketplace_api import OpenAPIMock, load_spec


MARKET_SPEC = load_spec('marketplaces/yandex_market.json')
CAMPAIGN = '/v2/campaigns/{campaignId}'
ORDERS = '/v1/businesses/{businessId}/orders'
BOXES = '/v2/campaigns/{campaignId}/orders/{orderId}/boxes'
STATUS = '/v2/campaigns/{campaignId}/orders/{orderId}/status'
FILTERS = {'campaignIds': [123], 'programTypes': ['FBS'], 'fake': False}
AWAITING_PACKING = {'statuses': ['PROCESSING'], 'substatuses': ['STARTED']}
READY_TO_SHIP = {'status': 'PROCESSING', 'substatus': 'READY_TO_SHIP'}


def item(sku, market_id, count=1, **fields):
    return {'offerId': sku, 'id': market_id, 'offerName': sku, 'count': count, **fields}


def market_order(order_id=789, *, status='PROCESSING', substatus='STARTED', items=(), **fields):
    return {
        'orderId': order_id, 'campaignId': 123, 'programType': 'FBS',
        'status': status, 'substatus': substatus, 'creationDate': '2026-11-25T12:00:00+03:00',
        'paymentType': 'PREPAID', 'paymentMethod': 'YANDEX', 'fake': False, 'items': list(items),
        'delivery': {
            'type': 'DELIVERY', 'serviceName': 'Яндекс Маркет', 'deliveryServiceId': 1,
            'deliveryPartnerType': 'YANDEX_MARKET', 'dates': {'fromDate': '2026-11-30'},
        },
        **fields,
    }


def ready_response():
    return {'order': {
        **READY_TO_SHIP,
        'id': 789, 'creationDate': '25-11-2026 12:00:00', 'currency': 'RUR',
        'itemsTotal': 1700, 'deliveryTotal': 0, 'buyerItemsTotalBeforeDiscount': 2000,
        'paymentType': 'PREPAID', 'paymentMethod': 'YANDEX', 'fake': False, 'taxSystem': 'USN', 'buyer': {'type': 'PERSON'},
        'items': [item('machine', 10, 2, price=850, buyerPrice=850, buyerPriceBeforeDiscount=1000)],
        'delivery': {
            'type': 'DELIVERY', 'serviceName': 'Яндекс Маркет', 'deliveryServiceId': 1,
            'deliveryPartnerType': 'YANDEX_MARKET', 'dates': {'fromDate': '30-11-2026'},
        },
    }}


class BeruOrderTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        add_marketplace_sites()  # Saving order items may mark marketplace stock for notification.
        site = Site.objects.create(domain='market.yandex.ru', name='Яндекс Маркет')
        SiteProfile.objects.create(site=site)
        seller = Contractor.objects.create(code='beru-seller', name='Продавец')
        cls.integration = Integration.objects.create(
            name='Яндекс Маркет', utm_source='beru', source_site=site, target_site=Site.objects.get_current(),
            uses_api=True, uses_boxes=True, enabled=True, seller=seller, settings={'ym_campaign': '123', 'api_key': 'test-api-key'},
        )
        cls.user = ShopUser.objects.create(phone='0000')
        cls.product = add_product(1, article='machine')

    def setUp(self):
        self.market = OpenAPIMock(self, {'Api-Key': 'test-api-key'})
        self.enterContext(patch('beru.tasks.urlopen', side_effect=self.market))

    def expect(self, path, method, response, **kwargs):
        params = {'campaignId': 123, 'businessId': 456, 'orderId': 789}
        self.market.expect(MARKET_SPEC, path, method, response, path_params=params, **kwargs)

    def expect_campaign(self):
        self.expect(CAMPAIGN, 'GET', {
            'campaign': {'id': 123, 'business': {'id': 456, 'name': 'Швейный Мир'}, 'placementType': 'FBS'},
        })

    def expect_orders(self, orders, filters, *, token=None, next_token=None):
        response = {'orders': orders}
        if next_token:
            response['paging'] = {'nextPageToken': next_token}
        query = {'limit': ['50']}
        if token:
            query['pageToken'] = [token]
        self.expect(ORDERS, 'POST', response, body={**FILTERS, **filters}, query=query)

    def poll(self):
        return get_integration_orders.run(self.integration.utm_source, target_site_id=self.integration.target_site_id)

    def local_order(self, market_id=789, status=Order.STATUS_NEW, **fields):
        return Order.objects.create(
            site=self.integration.source_site, integration=self.integration, user=self.user,
            delivery_tracking_number=str(market_id), status=status, **fields,
        )

    def send_ready(self, order):
        return notify_beru_order_status.run(order.pk, READY_TO_SHIP['status'], READY_TO_SHIP['substatus'])

    def pack_order(self):
        order = self.local_order(status=Order.STATUS_COLLECTED)
        for _ in range(2):
            box = Box.objects.create(order=order)
            order.items.create(product=self.product, product_price=1000, quantity=1, box=box)
        return order

    def test_dispatches_only_enabled_marketplace_api_integrations(self):
        for source, fields in (
            ('disabled', {'enabled': False, 'uses_api': True, 'settings': self.integration.settings}),
            ('feed', {'enabled': True, 'uses_api': False, 'settings': self.integration.settings}),
            ('ozon', {'enabled': True, 'uses_api': True, 'settings': {'client_id': 123}}),
        ):
            Integration.objects.create(
                name=source, utm_source=source, source_site=self.integration.source_site, target_site=self.integration.target_site,
                **fields,
            )
        with patch.object(get_integration_orders, 's') as signature:
            self.assertEqual(get_orders.run(), 1)
        signature.assert_called_once_with('beru', target_site_id=self.integration.target_site_id)
        signature.return_value.apply_async.assert_called_once()

    def test_paginates_and_imports_valid_lines_with_discounts_and_an_alert(self):
        prices = {
            'payment': {'value': 1510, 'currencyId': 'RUR'},
            'cashback': {'value': 17, 'currencyId': 'RUR'},
            'subsidy': {'value': 172, 'currencyId': 'RUR'},
        }
        incomplete = market_order(items=[item('machine', 10, 2, prices=prices), item('missing', 11)], notes='Комментарий')
        incomplete['delivery'].update(
            shipment={'id': 110, 'shipmentDate': '2026-11-26'},
            courier={'region': {'id': 2, 'name': 'Москва', 'type': 'CITY', 'parent': {'id': 1, 'name': 'Россия', 'type': 'COUNTRY'}}},
        )
        incomplete['delivery']['dates'].update(fromTime='12:00:00', toTime='18:00:00')
        second = market_order(790, items=[item('machine', 12)])
        self.expect_campaign()
        self.expect_orders([incomplete], AWAITING_PACKING, next_token='page/+2')
        self.expect_orders([
            second,
            market_order(791, substatus='READY_TO_SHIP'),
            market_order(792, fake=True),
            market_order(793, programType='EXPRESS'),
        ], AWAITING_PACKING, token='page/+2')
        with self.assertLogs('beru', 'WARNING'):
            self.assertEqual(self.poll(), 2)

        order = Order.objects.get(integration=self.integration, delivery_tracking_number='789')
        self.assertEqual((order.status, order.paid, order.user, order.site),
                         (Order.STATUS_NEW, True, self.user, self.integration.source_site))
        self.assertEqual((order.city, order.address, order.comment), ('Москва', 'Москва, Россия', 'Комментарий'))
        self.assertEqual((order.delivery_dispatch_date, order.delivery_handing_date), (date(2026, 11, 26), date(2026, 11, 30)))
        self.assertEqual((order.delivery_time_from, order.delivery_time_till), (time(12), time(18)))
        self.assertIn('missing', order.alert)
        line = order.items.get()
        self.assertEqual((line.product, line.quantity, line.val_discount), (self.product, 2, Decimal('150.50')))
        self.assertEqual(Order.objects.get(integration=self.integration, delivery_tracking_number='790').items.get().val_discount, 0)

        self.expect_campaign()
        self.expect_orders([incomplete, second], {'orderIds': [789, 790]})
        self.expect_orders([incomplete, second], AWAITING_PACKING)
        self.assertEqual(self.poll(), 0)
        self.assertEqual(Basket.objects.filter(secondary=True).count(), 2)

    def test_updates_legacy_orders_and_preserves_local_packing(self):
        order = self.local_order(status=Order.STATUS_COLLECTING, comment='Из старого API')
        for status, substatus, expected in (
            ('PROCESSING', 'READY_TO_SHIP', Order.STATUS_COLLECTING),
            ('DELIVERY', 'DELIVERY_SERVICE_RECEIVED', Order.STATUS_SENT),
            ('PICKUP', 'PICKUP_SERVICE_RECEIVED', Order.STATUS_DELIVERED),
            ('DELIVERED', 'USER_RECEIVED', Order.STATUS_DONE),
        ):
            with self.subTest(status=status):
                self.expect_campaign()
                self.expect_orders([market_order(status=status, substatus=substatus)], {'orderIds': [789]})
                self.expect_orders([], AWAITING_PACKING)
                with patch.object(notify_beru_order_status, 'delay') as outbound, self.captureOnCommitCallbacks(execute=True):
                    self.assertEqual(self.poll(), 1)
                outbound.assert_not_called()
                order.refresh_from_db()
                self.assertEqual((order.status, order.comment), (expected, 'Из старого API'))
        self.assertFalse(Basket.objects.exists())

    def test_cancels_new_orders_and_flags_cancellation_during_fulfillment(self):
        new = self.local_order()
        collecting = self.local_order(790, status=Order.STATUS_COLLECTING, owner=self.user)
        failed = self.local_order(791)
        cancelled = [
            market_order(789, status='CANCELLED', substatus='USER_CHANGED_MIND'),
            market_order(790, status='CANCELLED', substatus='USER_CHANGED_MIND'),
            market_order(791, status='CANCELLED', substatus='SHOP_FAILED'),
        ]
        self.expect_campaign()
        self.expect_orders(cancelled, {'orderIds': [789, 790, 791]})
        self.expect_orders([], AWAITING_PACKING)
        self.assertEqual(self.poll(), 2)
        new.refresh_from_db()
        collecting.refresh_from_db()
        failed.refresh_from_db()
        self.assertEqual(new.status, Order.STATUS_CANCELED)
        self.assertEqual(failed.status, Order.STATUS_PROBLEM)
        self.assertEqual(collecting.alert, '')

        collecting.owner = None
        collecting.save(update_fields=['owner'])
        for count in (1, 0):
            self.expect_campaign()
            self.expect_orders(cancelled[1:], {'orderIds': [790, 791]})
            self.expect_orders([], AWAITING_PACKING)
            self.assertEqual(self.poll(), count)
        collecting.refresh_from_db()
        failed.refresh_from_db()
        self.assertEqual(collecting.status, Order.STATUS_COLLECTING)
        self.assertEqual(collecting.alert, new.delivery_info)
        self.assertEqual(failed.delivery_info.count('\n'), 0)

    def test_batches_tracked_orders_and_ignores_nonnumeric_numbers(self):
        Order.objects.bulk_create(
            Order(site=self.integration.source_site, integration=self.integration, user=self.user, delivery_tracking_number=str(number))
            for number in range(1, 52)
        )
        self.local_order('local-only')
        self.local_order(52, status=Order.STATUS_DONE)
        self.expect_campaign()
        self.expect_orders([], {'orderIds': list(range(1, 51))})
        self.expect_orders([], {'orderIds': [51]})
        self.expect_orders([], AWAITING_PACKING)
        self.assertEqual(self.poll(), 0)

    def test_rejects_a_malformed_order_page(self):
        self.expect_campaign()
        self.expect(ORDERS, 'POST', b'<html>unexpected response</html>',
                    body={**FILTERS, **AWAITING_PACKING}, query={'limit': ['50']})
        with self.assertRaisesRegex(MarketUnavailable, 'invalid JSON'):
            self.poll()
        self.assertFalse(Order.objects.exists())

    def test_uploads_boxes_and_reuses_them_after_a_transient_status_failure(self):
        order = self.pack_order()
        remote = market_order(items=[item('machine', 10, 2)])
        boxes = [{'items': [{'id': 10, 'fullCount': 1}]}] * 2
        self.expect_campaign()
        self.expect_orders([remote], {'orderIds': [789]})
        self.expect(BOXES, 'PUT', {'status': 'OK'}, body={'boxes': boxes, 'allowRemove': False})
        self.expect(STATUS, 'PUT', {'status': 'ERROR', 'errors': [{'code': 'SERVICE_ERROR'}]},
                    status=500, body={'order': READY_TO_SHIP})
        with self.assertRaisesRegex(MarketUnavailable, 'HTTP 500'):
            self.send_ready(order)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.STATUS_COLLECTED)

        remote['delivery']['boxesLayout'] = [
            {**box, 'boxId': index, 'barcode': f'MARKET-{index}'} for index, box in enumerate(boxes, start=1)
        ]
        self.expect_campaign()
        self.expect_orders([remote], {'orderIds': [789]})
        self.expect(STATUS, 'PUT', ready_response(), body={'order': READY_TO_SHIP})
        self.assertEqual(self.send_ready(order), '789: PROCESSING READY_TO_SHIP')

        self.expect_campaign()
        self.expect_orders([market_order(substatus='READY_TO_SHIP')], {'orderIds': [789]})
        self.assertIsNone(self.send_ready(order))

    def test_incomplete_packing_is_visible_in_admin_and_sends_no_updates(self):
        order = self.pack_order()
        self.expect_campaign()
        self.expect_orders([market_order(items=[item('machine', 10, 2), item('missing', 11)])], {'orderIds': [789]})
        with self.assertRaisesRegex(TaskFailure, 'Комплектация коробок'):
            self.send_ready(order)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.STATUS_PROBLEM)
        self.assertIn('Комплектация коробок', order.delivery_info)

    def test_market_rejection_is_reported_without_including_the_response_body(self):
        order = self.pack_order()
        self.expect_campaign()
        self.expect_orders([market_order(items=[item('machine', 10, 2)])], {'orderIds': [789]})
        self.expect(
            BOXES, 'PUT', {'status': 'ERROR', 'errors': [{'code': 'BAD_REQUEST', 'message': 'raw details'}]},
            body={'boxes': [{'items': [{'id': 10, 'fullCount': 1}]}] * 2, 'allowRemove': False}, status=400,
        )
        with self.assertRaisesRegex(TaskFailure, 'HTTP 400'):
            self.send_ready(order)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.STATUS_PROBLEM)
        self.assertIn('HTTP 400', order.delivery_info)
        self.assertNotIn('raw details', order.delivery_info)

    def test_ignores_queued_shipped_calls(self):
        self.assertIsNone(notify_beru_order_status.run(42, 'PROCESSING', 'SHIPPED'))
