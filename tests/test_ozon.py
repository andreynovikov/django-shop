"""
Ozon: FBS postings polled and pushed by notifications, and stock updates. urlopen is mocked with the operations of
the bundled API schema in tests/data/marketplaces, so nothing reaches the marketplace. See settings.py on how to run.
"""
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from unittest.mock import call, patch
from urllib.error import HTTPError

from django.contrib.sites.models import Site
from django.test import Client, TestCase
from django.urls import reverse
from kombu.exceptions import OperationalError

from ozon import tasks
from sewingworld.models import SiteProfile
from shop.models import Basket, Contractor, Integration, IntegrationCheck, Order, Product, ProductIntegration, ShopUser

from .fixtures import add_marketplace_sites, add_product, mock_constance
from .marketplace_api import OpenAPIMock, load_spec


SPEC = load_spec('marketplaces/ozon.json')
POSTINGS = '/v4/posting/fbs/list'
POSTING_DETAIL = '/v3/posting/fbs/get'
STOCKS = '/v2/products/stocks'
NOW = datetime(2026, 11, 25, 12, tzinfo=UTC)
POSTING_REQUEST = {
    'sort_dir': 'DESC',
    'filter': {
        'since': (NOW - timedelta(days=7)).isoformat(),
        'to': NOW.isoformat(),
        'statuses': ['awaiting_registration', 'awaiting_approve', 'awaiting_packaging', 'awaiting_deliver', 'delivering', 'delivered'],
        'warehouse_ids': ['101', '102'],
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
        mock_constance(self)
        self.market = OpenAPIMock(self, {'Client-Id': '42', 'Api-Key': 'test-ozon-key'})
        self.enterContext(patch('ozon.tasks.urlopen', side_effect=self.market))

    def expect_postings(self, postings, *, cursor=None, next_cursor=None, reconcile=False):
        body = POSTING_REQUEST
        if reconcile:
            filters = POSTING_REQUEST['filter']
            body = {**body, 'filter': {**filters, 'statuses': [*filters['statuses'], 'cancelled']}}
        if cursor is not None:
            body = {**body, 'cursor': cursor}
        response = {'has_next': next_cursor is not None, 'cursor': next_cursor or '', 'postings': postings}
        self.market.expect(SPEC, POSTINGS, 'POST', response, body=body)

    def expect_posting_detail(self, number, *, http_status=200, **fields):
        body = {'posting_number': number, 'with': {'analytics_data': True, 'barcodes': True}}
        if http_status == 200:
            price = {'offer_id': 'machine', 'sku': 234, 'quantity': 2, 'price': '850.50', 'currency_code': 'RUB'}
            response = {'result': posting(number, products=[price], **fields)}
        else:
            response = {'code': 5, 'message': 'Posting unavailable'}
        self.market.expect(SPEC, POSTING_DETAIL, 'POST', response, body=body, status=http_status)

    def enable_push(self):
        self.integration.settings['push_token'] = 'test-push-token'
        self.integration.save(update_fields=['settings'])

    def sync(self, number):
        return tasks.sync_integration_posting.run(self.integration.pk, number)

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

    def test_records_the_reply_as_the_integrations_failure_until_a_success(self):
        self.market.expect(SPEC, POSTINGS, 'POST', {'code': 7, 'message': 'Api-key is deactivated'}, body=POSTING_REQUEST, status=403)
        with self.assertLogs('ozon', 'ERROR'), self.assertRaises(tasks.TaskFailure):
            self.poll()
        check = IntegrationCheck.objects.get(integration=self.integration, operation='ozon.tasks.get_integration_unfulfilled_orders')
        self.assertEqual(check.failures, 1)
        self.assertEqual(check.error.splitlines(), [
            'HTTP 403: Api-key is deactivated', '{"code": 7, "message": "Api-key is deactivated"}',
        ])

        self.expect_postings([])
        self.assertEqual(self.poll(), 0)
        check.refresh_from_db()
        self.assertEqual((check.failures, check.error), (0, ''))

    def test_integrations_of_one_account_take_only_the_postings_of_their_warehouses(self):
        # ozon and ozon_rfbs share a seller account: rFBS duplicated the orders of the other integration once.
        rfbs = Integration.objects.create(
            name='Ozon rFBS', utm_source='ozon_rfbs', source_site=self.integration.source_site,
            target_site=self.integration.target_site, uses_api=True, enabled=True, seller=self.integration.seller,
            settings={**self.integration.settings, 'warehouses': [{'id': 201, 'is_express': True}, {'id': 201}]},
        )
        own, other = posting('123-1-1', delivery_method={'warehouse_id': 101}), posting('123-2-1', delivery_method={'warehouse_id': 201})
        self.expect_postings([own, other])
        self.assertEqual(self.poll(), 1)

        filters = {**POSTING_REQUEST['filter'], 'warehouse_ids': ['201']}
        self.market.expect(SPEC, POSTINGS, 'POST', {'has_next': False, 'postings': [own, other]}, body={**POSTING_REQUEST, 'filter': filters})
        with patch('ozon.tasks.timezone.now', return_value=NOW):
            self.assertEqual(tasks.get_integration_unfulfilled_orders.run('ozon_rfbs', target_site_id=rfbs.target_site_id), 1)

        self.assertEqual(
            sorted(Order.objects.values_list('delivery_tracking_number', 'integration__utm_source')),
            [('123-1-1', 'ozon'), ('123-2-1', 'ozon_rfbs')],
        )

    def test_does_not_import_a_posting_that_is_the_order_of_another_integration(self):
        self.expect_postings([posting('123-1-1')])
        self.assertEqual(self.poll(), 1)
        order = Order.objects.get()

        shared = Integration.objects.create(
            name='Ozon 2', utm_source='ozon_2', source_site=self.integration.source_site,
            target_site=self.integration.target_site, uses_api=True, enabled=True, seller=self.integration.seller, settings={'client_id': '42', 'api_key': 'test-ozon-key'},
        )
        filters = {key: value for key, value in POSTING_REQUEST['filter'].items() if key != 'warehouse_ids'}
        self.market.expect(SPEC, POSTINGS, 'POST', {'has_next': False, 'postings': [posting('123-1-1', scanit='OTHER')]},
                           body={**POSTING_REQUEST, 'filter': filters})
        with patch('ozon.tasks.timezone.now', return_value=NOW), self.assertLogs('ozon', 'WARNING'):
            self.assertEqual(tasks.get_integration_unfulfilled_orders.run('ozon_2', target_site_id=shared.target_site_id), 0)
        self.assertEqual(list(Order.objects.all()), [order])
        order.refresh_from_db()
        self.assertNotIn('barcode', order.meta or {})

    def test_push_ignores_a_posting_of_another_warehouse(self):
        self.enable_push()
        self.expect_posting_detail('123-2-1', delivery_method={'warehouse_id': 201})
        self.assertFalse(self.sync('123-2-1'))
        self.assertFalse(Order.objects.exists())

    def test_push_details_import_and_reconcile_the_same_posting_as_polling(self):
        self.enable_push()
        number = '123-1-1'
        self.expect_posting_detail(
            number, scanit='BARCODE', is_express=True,
            analytics_data={'city': 'Москва', 'delivery_date_end': '2026-11-29T12:00:00Z'},
        )
        self.assertTrue(self.sync(number))
        order = Order.objects.get(integration=self.integration, delivery_tracking_number=number)
        line = order.items.get()
        self.assertEqual((line.product, line.quantity, line.val_discount), (self.product, 2, Decimal('149.50')))
        self.assertEqual((order.delivery, order.meta['barcode']), (Order.DELIVERY_EXPRESS, 'BARCODE'))
        self.assertEqual((order.status, order.delivery_handing_date), (Order.STATUS_NEW, date(2026, 11, 29)))

        self.expect_postings([posting(number, status='delivering')], reconcile=True)
        self.assertEqual(self.poll(), 1)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.STATUS_SENT)

        self.expect_posting_detail(
            number, shipment_date='2026-11-27T12:00:00Z',
            analytics_data={'city': 'Москва', 'delivery_date_end': '2026-11-30T12:00:00Z'},
        )
        self.assertTrue(self.sync(number))
        order.refresh_from_db()
        self.assertEqual(order.status, Order.STATUS_SENT)
        self.assertEqual((order.delivery_dispatch_date, order.delivery_handing_date), (date(2026, 11, 27), date(2026, 11, 30)))
        self.assertEqual(order.items.get().pk, line.pk)
        self.assertEqual(Basket.objects.filter(secondary=True).count(), 1)

        self.expect_posting_detail(number, status='delivered')
        self.assertTrue(self.sync(number))
        order.refresh_from_db()
        self.assertEqual(order.status, Order.STATUS_DELIVERED)

    def test_cancels_new_orders_and_flags_cancellations_during_fulfillment(self):
        self.enable_push()
        first, second, unknown = '123-1-1', '123-1-2', '123-1-3'
        self.expect_postings([posting(first), posting(second)], reconcile=True)
        self.assertEqual(self.poll(), 2)
        collecting = Order.objects.get(delivery_tracking_number=second)
        collecting.status = Order.STATUS_COLLECTING
        collecting.alert = 'Существующее предупреждение'
        collecting.save(update_fields=['status', 'alert'])

        self.expect_postings([posting(first, status='cancelled'), posting(unknown, status='cancelled')], reconcile=True)
        self.assertEqual(self.poll(), 1)
        self.assertEqual(Order.objects.get(delivery_tracking_number=first).status, Order.STATUS_CANCELED)
        self.assertFalse(Order.objects.filter(delivery_tracking_number=unknown).exists())

        for status in ('cancelled', 'cancelled', 'delivering'):
            self.expect_posting_detail(second, status=status)
            self.assertTrue(self.sync(second))
        collecting.refresh_from_db()
        self.assertEqual(collecting.status, Order.STATUS_COLLECTING)
        self.assertEqual(collecting.alert.splitlines(), ['Ozon: отправление отменено', 'Существующее предупреждение'])

    def test_ignores_missing_fbs_posting_and_retries_server_error(self):
        self.enable_push()
        self.expect_posting_detail('123-1-1', http_status=404)
        self.assertFalse(self.sync('123-1-1'))
        self.expect_posting_detail('123-1-1', http_status=500)
        with patch.object(tasks.sync_integration_posting, 'retry', side_effect=lambda *, exc, **kwargs: exc) as retry:
            with self.assertRaises(HTTPError):
                self.sync('123-1-1')
        self.assertEqual(retry.call_args.kwargs['exc'].code, 500)
        self.assertFalse(Order.objects.exists())

    def test_queued_sync_checks_push_configuration_again(self):
        self.enable_push()
        self.integration.enabled = False
        self.integration.save(update_fields=['enabled'])
        self.assertFalse(self.sync('123-1-1'))

    def send_stock(self, product):
        with patch.object(Product, 'get_stocks', side_effect=[{product.pk: 24}, {product.pk: -3}]) as count:
            tasks.notify_product_stocks.run([product.pk], self.integration.utm_source, target_site_id=self.integration.target_site_id)
        self.assertEqual(count.call_args_list, [
            call([product.pk], integration=self.integration), call([product.pk], integration=self.integration, express=True),
        ])

    def expect_stock_update(self, *, updated=True, code='TOO_MANY_REQUESTS'):
        body = {'stocks': [
            {'offer_id': 'machine', 'stock': 20, 'warehouse_id': 101},
            {'offer_id': 'machine', 'stock': 0, 'warehouse_id': 102},
        ]}
        response = {'result': [
            {'offer_id': 'machine', 'warehouse_id': 101, 'updated': updated,
             'errors': [] if updated else [{'code': code, 'message': 'Try again' if code == 'TOO_MANY_REQUESTS' else 'Unknown warehouse'}]},
            {'offer_id': 'machine', 'warehouse_id': 102, 'updated': True, 'errors': []},
        ]}
        self.market.expect(SPEC, STOCKS, 'POST', response, body=body)

    def test_updates_standard_and_express_stocks_and_clears_the_notification_flag(self):
        link = ProductIntegration.objects.create(product=self.product, integration=self.integration, notify_stock=True)
        self.expect_stock_update()
        self.send_stock(self.product)
        link.refresh_from_db()
        self.assertFalse(link.notify_stock)

    def test_keeps_stock_pending_when_ozon_limits_the_rate_for_one_warehouse(self):
        link = ProductIntegration.objects.create(product=self.product, integration=self.integration, notify_stock=True)
        self.expect_stock_update(updated=False)
        self.send_stock(self.product)
        link.refresh_from_db()
        self.assertTrue(link.notify_stock)
        # The exchange itself works
        check = IntegrationCheck.objects.get(integration=self.integration, operation='ozon.tasks.notify_product_stocks')
        self.assertEqual(check.failures, 0)

    def test_records_other_errors_of_a_warehouse_as_the_integrations_failure(self):
        link = ProductIntegration.objects.create(product=self.product, integration=self.integration, notify_stock=True)
        self.expect_stock_update(updated=False, code='WAREHOUSE_NOT_FOUND')
        with self.assertLogs('ozon', 'ERROR'):
            self.send_stock(self.product)
        link.refresh_from_db()
        self.assertFalse(link.notify_stock)  # until its stock changes again
        check = IntegrationCheck.objects.get(integration=self.integration, operation='ozon.tasks.notify_product_stocks')
        self.assertEqual(check.failures, 1)
        self.assertEqual(check.error, 'Ozon не принял остатки:\nmachine, склад 101: WAREHOUSE_NOT_FOUND: Unknown warehouse')


class OzonNotificationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        add_marketplace_sites()
        cls.integration = Integration.objects.create(
            name='Ozon', utm_source='ozon', source_site=Site.objects.get(domain='ozon.ru'),
            target_site=Site.objects.get_current(), enabled=True, settings={'push_token': 'test-push-token'},
        )

    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)
        self.publish = self.enterContext(patch('ozon.views.sync_integration_posting.apply_async'))

    # The default sender is in OZON_NETWORKS of ozon/views.py, the addresses Ozon notifies from
    def notify(self, payload, *, token='test-push-token', sender='91.223.93.246', integration_id=None, **headers):
        url = reverse('ozon-notifications', args=[integration_id or self.integration.pk], query={'token': token})
        return self.client.post(url, payload, content_type='application/json', REMOTE_ADDR=sender, **headers)

    def test_ping_returns_the_ozon_connection_check_response(self):
        with patch('ozon.views.timezone.now', return_value=NOW):
            response = self.notify({'message_type': 'TYPE_PING', 'time': '2026-11-25T11:59:59Z'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'version': '1.0', 'name': 'Sewing World', 'time': '2026-11-25T12:00:00Z'})
        self.publish.assert_not_called()

    def test_queues_the_supported_posting_events(self):
        for event in (
            'TYPE_NEW_POSTING', 'TYPE_POSTING_CANCELLED', 'TYPE_STATE_CHANGED',
            'TYPE_CUTOFF_DATE_CHANGED', 'TYPE_DELIVERY_DATE_CHANGED',
        ):
            with self.subTest(event=event):
                response = self.notify({'message_type': event, 'posting_number': '123-1-1'})
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json(), {'result': True})
        self.assertEqual(self.publish.call_args_list, [call((self.integration.pk, '123-1-1'), retry=False)] * 5)

    def test_both_url_prefixes_accept_posting_notifications(self):
        canonical = reverse('ozon-notifications', args=[self.integration.pk])
        self.assertEqual(canonical, f'/integrations/ozon/notifications/{self.integration.pk}/')
        for path in (canonical, f'/ozon/notifications/{self.integration.pk}/'):
            with self.subTest(path=path):
                response = self.client.post(
                    f'{path}?token=test-push-token',
                    {'message_type': 'TYPE_NEW_POSTING', 'posting_number': '123-1-1'},
                    content_type='application/json', REMOTE_ADDR='91.223.93.246',
                )
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json(), {'result': True})
        self.assertEqual(self.publish.call_args_list, [call((self.integration.pk, '123-1-1'), retry=False)] * 2)

    def test_rejects_untrusted_sender_wrong_token_and_disabled_integration(self):
        payload = {'message_type': 'TYPE_NEW_POSTING', 'posting_number': '123-1-1'}
        for kwargs in (
            {'sender': '127.0.0.1', 'HTTP_X_FORWARDED_FOR': '91.223.93.246', 'HTTP_X_REAL_IP': '91.223.93.246'},
            {'token': 'invalid'},
            {'token': ''},
            {'integration_id': self.integration.pk + 1},
        ):
            with self.subTest(kwargs=kwargs):
                self.assertEqual(self.notify(payload, **kwargs).status_code, 403)
        self.integration.enabled = False
        self.integration.save(update_fields=['enabled'])
        self.assertEqual(self.notify(payload).status_code, 403)
        self.publish.assert_not_called()

    def test_rejects_invalid_requests_and_acknowledges_unrelated_events(self):
        self.assertEqual(self.client.get(reverse('ozon-notifications', args=[self.integration.pk])).status_code, 405)
        for payload in (b'{', [], {}, {'message_type': 'TYPE_NEW_POSTING', 'posting_number': []}):
            with self.subTest(payload=payload):
                self.assertEqual(self.notify(payload).status_code, 400)
        response = self.notify({'message_type': 'TYPE_FBO_POSTING_NEW', 'posting_number': '123-1-1'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'result': True})
        self.publish.assert_not_called()

    def test_returns_service_unavailable_if_the_task_cannot_be_published(self):
        self.publish.side_effect = OperationalError
        with self.assertLogs('ozon', 'ERROR'):
            response = self.notify({'message_type': 'TYPE_NEW_POSTING', 'posting_number': '123-1-1'})
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()['error']['code'], 'ERROR_UNKNOWN')
