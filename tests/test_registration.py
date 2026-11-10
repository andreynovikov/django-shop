"""
Registration with a code sent to the phone, through the real endpoints. SMS and mail are mocked. See settings.py on how to run.
"""
from unittest import mock

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.cache import cache
from django.db.models import F
from django.test import TestCase, override_settings

from shop.models import Basket, LoginCode, PhoneCode, ShopUser

from .clients import StorefrontClient, add_storefront_key

PHONE = '+79161234567'
OTHER = '+79167654321'


@override_settings(CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}})
class Base(TestCase):
    def setUp(self):
        cache.clear()
        for name in ('send_phone_code', 'send_password', 'send_email_confirmation'):
            patcher = mock.patch(f'sewingworld.api.{name}')
            setattr(self, name, patcher.start())
            self.addCleanup(patcher.stop)
        add_storefront_key()
        self.client = StorefrontClient()

    def register(self, client=None, **body):
        body.setdefault('phone', PHONE)
        return (client or self.client).post('/api/v0/users/', body, format='json')

    def code(self):
        return self.send_phone_code.delay.call_args.args[1]

    def current(self, client=None):
        return (client or self.client).get('/api/v0/users/current/').json()['id']

    def resend_delay_passes(self):
        PhoneCode.objects.update(expires=F('expires') - PhoneCode.RESEND_DELAY)


class SendTests(Base):
    def test_data_first_then_code(self):
        response = self.register(name='Иван')
        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.json(), {'phone': PHONE, 'retry_after': 240, 'attempts_left': 5})
        self.send_phone_code.delay.assert_called_once()
        self.assertEqual(self.send_phone_code.delay.call_args.args[0], PHONE)
        self.assertRegex(self.code(), r'^\d{6}$')
        self.assertFalse(ShopUser.objects.filter(phone=PHONE).exists())
        self.assertIsNone(self.current())

    def test_phone_is_normalized(self):
        self.assertEqual(self.register(phone='9161234567').json()['phone'], PHONE)

    def test_taken_data_sends_nothing(self):
        ShopUser.objects.create(phone=OTHER, email='taken@example.com', username='taken')
        for body in ({'phone': OTHER}, {'email': 'taken@example.com'}, {'username': 'taken'}):
            response = self.register(**body)
            self.assertEqual(response.status_code, 400, body)
            self.assertEqual(set(response.json()), set(body), body)
        self.send_phone_code.delay.assert_not_called()

    def test_only_russian_phones(self):
        for phone in ('+375291234567', '+7916123', '12345'):
            response = self.register(phone=phone)
            self.assertEqual(response.status_code, 400, phone)
            self.assertIn('phone', response.json())
        self.send_phone_code.delay.assert_not_called()

    def test_short_password_sends_nothing(self):
        response = self.register(password='short')
        self.assertEqual(response.status_code, 400)
        self.assertIn('password', response.json())
        self.send_phone_code.delay.assert_not_called()

    def test_resubmit_within_delay_sends_nothing(self):
        self.register()
        self.register()
        self.send_phone_code.delay.assert_called_once()
        self.resend_delay_passes()
        self.assertEqual(self.register().json()['retry_after'], 240)
        self.assertEqual(self.send_phone_code.delay.call_count, 2)

    def test_phone_limit_is_shared_with_login_codes(self):
        user = ShopUser.objects.create(phone=OTHER)
        for _ in range(3):
            self.client.post(f'/api/v0/users/{OTHER}/check/', {}, format='json')
            LoginCode.objects.update(expires=F('expires') - LoginCode.RESEND_DELAY)
        user.delete()  # so the phone can be registered
        for _ in range(2):
            self.assertEqual(self.register(phone=OTHER).status_code, 202)
            self.resend_delay_passes()
        self.assertEqual(self.register(phone=OTHER).status_code, 429)
        self.assertEqual(self.send_password.delay.call_count + self.send_phone_code.delay.call_count, 5)


class CodeTests(Base):
    def test_good_code_creates_account_and_logs_in(self):
        self.register(name='Иван')
        response = self.register(name='Иван', code=self.code())
        self.assertEqual(response.status_code, 201)
        user = ShopUser.objects.get(phone=PHONE)
        self.assertEqual(response.json()['id'], user.id)
        self.assertEqual(user.name, 'Иван')
        self.assertTrue(user.phone_verified)
        self.assertFalse(user.has_usable_password())
        self.assertFalse(user.permanent_password)
        self.assertEqual(self.current(), user.id)
        self.assertFalse(PhoneCode.objects.exists())

    def test_wrong_code_counts_attempts(self):
        self.register()
        for attempt in range(1, PhoneCode.MAX_ATTEMPTS):
            response = self.register(code='wrong')
            self.assertEqual(response.status_code, 400)
            self.assertEqual(response.json(), {'code': ['Неверный или устаревший код']})
            self.assertEqual(PhoneCode.objects.get().attempts, attempt)
        self.register(code='wrong')
        self.assertFalse(PhoneCode.objects.exists())
        self.assertEqual(self.register(code=self.code()).status_code, 400)  # used up
        self.assertFalse(ShopUser.objects.exists())

    def test_new_code_at_once_when_attempts_run_out(self):
        self.register()
        for _ in range(PhoneCode.MAX_ATTEMPTS):
            self.register(code='wrong')
        self.assertEqual(self.register().status_code, 202)
        self.assertEqual(self.send_phone_code.delay.call_count, 2)
        self.assertEqual(self.register(code=self.code()).status_code, 201)

    def test_code_is_bound_to_its_phone(self):
        self.register()
        code = self.code()
        self.register(phone=OTHER)
        self.assertEqual(self.register(phone=OTHER, code=code).status_code, 400)

    def test_code_of_a_phone_change_does_not_register(self):
        user = ShopUser.objects.create(phone=OTHER)
        with mock.patch('shop.models.user.secrets.randbelow', return_value=42):
            PhoneCode.issue(PHONE, user)
        self.assertEqual(self.register(code='000042').status_code, 400)

    def test_code_from_another_session_works(self):
        # The code proves the phone, not the browser
        self.register()
        client = StorefrontClient()
        self.assertEqual(self.register(client=client, code=self.code()).status_code, 201)
        self.assertEqual(self.current(client), ShopUser.objects.get(phone=PHONE).id)

    def test_phone_registered_meanwhile(self):
        self.register()
        ShopUser.objects.create(phone=PHONE)
        response = self.register(code=self.code())
        self.assertEqual(response.status_code, 400)
        self.assertIn('phone', response.json())

    def test_permanent_password(self):
        self.register(password='long-enough')
        self.assertEqual(self.register(password='long-enough', code=self.code()).status_code, 201)
        user = ShopUser.objects.get(phone=PHONE)
        self.assertTrue(user.permanent_password)
        self.assertTrue(user.check_password('long-enough'))
        response = StorefrontClient().post('/api/v0/users/login/', {'phone': PHONE, 'password': 'long-enough'}, format='json')
        self.assertEqual(response.status_code, 200)

    def test_empty_password_is_none(self):
        self.register(password='')
        self.register(password='', code=self.code())
        self.assertFalse(ShopUser.objects.get(phone=PHONE).has_usable_password())

    def test_flags_cannot_be_planted(self):
        self.register(email='me@example.com', email_verified=True, phone_verified=False)
        self.register(email='me@example.com', email_verified=True, phone_verified=False, code=self.code())
        user = ShopUser.objects.get(phone=PHONE)
        self.assertFalse(user.email_verified)
        self.assertTrue(user.phone_verified)

    def test_email_gets_a_link(self):
        self.register(email='me@example.com')
        self.send_email_confirmation.delay.assert_not_called()  # nothing exists yet
        self.register(email='me@example.com', code=self.code())
        user = ShopUser.objects.get(phone=PHONE)
        self.send_email_confirmation.delay.assert_called_once_with(user.id, 'me@example.com', Site.objects.get_current().id)

    def test_no_email_no_link(self):
        self.register()
        self.register(code=self.code())
        self.send_email_confirmation.delay.assert_not_called()

    def test_basket_is_kept(self):
        session = self.client.session  # saved, and its cookie set
        basket = Basket.objects.create(site=Site.objects.get_current(), session_id=session.session_key)
        self.register()
        self.register(code=self.code())
        basket.refresh_from_db()
        self.assertNotEqual(basket.session_id, session.session_key)  # login rotates the key
        self.assertEqual(basket.session_id, self.client.cookies[settings.SESSION_COOKIE_NAME].value)


class SilentRegistrationTests(Base):
    def test_checkout_still_needs_no_code(self):
        response = self.client.post('/api/v0/users/login/', {'phone': PHONE, 'ctx': 'order'}, format='json')
        self.assertEqual(response.status_code, 200)
        self.send_phone_code.delay.assert_not_called()
        self.send_password.delay.assert_not_called()
        self.assertFalse(ShopUser.objects.get(phone=PHONE).phone_verified)
