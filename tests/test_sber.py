"""
The basic auth of SberMegaMarket's notifications. Its credentials come from .env and are empty when unset, which must
not let in a request with empty credentials. Also what the order tasks write when the API refuses a call or answers.
See settings.py on how to run.
"""
import base64
import io
import json
from unittest import mock
from urllib.error import HTTPError

from django.contrib.sites.models import Site
from django.db import connection
from django.http import HttpResponse
from django.test import RequestFactory, SimpleTestCase, TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import resolve

from sber import tasks, views
from shop.models import Order, ShopUser


def basic(user, password):
    return 'Basic ' + base64.b64encode(f'{user}:{password}'.encode()).decode()


@views.auth_required
def notification(request):
    return HttpResponse('ok')


class AuthRequiredTests(SimpleTestCase):
    def call(self, authorization=None):
        headers = {'HTTP_AUTHORIZATION': authorization} if authorization is not None else {}
        return notification(RequestFactory().post('/sber/order/new', **headers))

    def test_unset_credentials_let_nobody_in(self):
        with mock.patch.dict(views.SBER_MARKET, {'auth_user': '', 'auth_password': ''}):
            self.assertEqual(self.call(basic('', '')).status_code, 403)
            self.assertEqual(self.call().status_code, 403)

    def test_credentials(self):
        with mock.patch.dict(views.SBER_MARKET, {'auth_user': 'sber', 'auth_password': 'secret'}):
            self.assertEqual(self.call(basic('sber', 'secret')).status_code, 200)
            self.assertEqual(self.call(basic('sber', 'wrong')).status_code, 403)
            self.assertEqual(self.call(basic('сбер', 'secret')).status_code, 403)
            self.assertEqual(self.call(basic('', '')).status_code, 403)


class UrlTests(SimpleTestCase):
    def test_both_url_prefixes_lead_to_the_views(self):
        for prefix in ('/integrations/sber/', '/sber/'):
            for path, view in (('order/new', views.new_order), ('order/cancel', views.cancel_order)):
                with self.subTest(path=prefix + path):
                    self.assertIs(resolve(prefix + path).func, view)


class OrderTaskTests(TestCase):
    def setUp(self):
        patcher = mock.patch.dict(tasks.SBER_MARKET, {'api': 'https://sber.test', 'token': 'token'})
        patcher.start()
        self.addCleanup(patcher.stop)
        buyer = ShopUser.objects.create(phone='+79161234567')
        self.order = Order.objects.create(user=buyer, site=Site.objects.get_current(), delivery_tracking_number='S1',
                                          delivery_info='Курьер')

    def test_refused_call_waits_for_the_lock(self):
        error = HTTPError('https://sber.test', 400, 'Bad Request', {}, io.BytesIO(b'{"error": "closed"}'))
        with mock.patch('sber.tasks.urlopen', side_effect=error), mock.patch('sber.tasks.update_order') as update, \
                self.assertLogs('sber', 'ERROR'), self.assertRaises(HTTPError):
            tasks.confirm_sber_order.run(self.order.pk)  # called directly, the retry raises
        update.delay.assert_called_once_with(self.order.pk, {'status': Order.STATUS_PROBLEM},
                                             append={'delivery_info': '{"error": "closed"}'})
        self.order.refresh_from_db()
        self.assertEqual(self.order.delivery_info, 'Курьер')  # update_order() adds it when it may

    def test_details_write_the_delivery_date_only(self):
        answer = {'success': 1, 'data': {'shipments': [{'deliveryDate': '2026-12-01T10:00:00+03:00'}]}}
        response = mock.Mock()
        response.read.return_value = json.dumps(answer).encode()
        with mock.patch('sber.tasks.urlopen', return_value=response), CaptureQueriesContext(connection) as queries:
            tasks.get_sber_order_details.run(self.order.pk)
        [update] = [query['sql'] for query in queries if query['sql'].startswith('UPDATE "shop_order"')]
        self.assertIn('"delivery_handing_date"', update)
        self.assertNotIn('"delivery_info"', update)
