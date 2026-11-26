"""
The basic auth of SberMegaMarket's notifications. Its credentials come from .env and are empty when unset, which must
not let in a request with empty credentials. See settings.py on how to run.
"""
import base64
from unittest import mock

from django.http import HttpResponse
from django.test import RequestFactory, SimpleTestCase

from sber import views


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
