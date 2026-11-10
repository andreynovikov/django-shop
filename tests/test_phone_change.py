"""
Moving an account to another phone needs a code sent to that phone. SMS and mail are mocked. See settings.py on how to run.
"""
from unittest import mock

from django.core.cache import cache
from django.db.models import F
from django.test import TestCase, override_settings

from shop.models import PhoneCode, ShopUser

from .clients import StorefrontClient, add_storefront_key

PHONE = '+79161234567'
NEW = '+79167654321'


@override_settings(CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}})
class Base(TestCase):
    def setUp(self):
        cache.clear()
        for name in ('send_phone_code', 'send_email_confirmation'):
            patcher = mock.patch(f'sewingworld.api.{name}')
            setattr(self, name, patcher.start())
            self.addCleanup(patcher.stop)
        add_storefront_key()
        self.user = ShopUser.objects.create(phone=PHONE, name='Иван', phone_verified=True)
        self.client = StorefrontClient()
        self.client.force_login(self.user)

    def put(self, client=None, user=None, **body):
        user = user or self.user
        body.setdefault('phone', user.phone)
        return (client or self.client).put(f'/api/v0/users/{user.id}/', body, format='json')

    def patch(self, **body):
        return self.client.patch(f'/api/v0/users/{self.user.id}/', body, format='json')

    def code(self):
        return self.send_phone_code.delay.call_args.args[1]


class ChangeTests(Base):
    def test_other_fields_are_saved_at_once(self):
        response = self.put(name='Пётр', address='Москва')
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual((self.user.name, self.user.address), ('Пётр', 'Москва'))
        self.send_phone_code.delay.assert_not_called()

    def test_same_phone_in_another_form_needs_no_code(self):
        self.assertEqual(self.put(phone='(916) 123-45-67', name='Пётр').status_code, 200)
        self.send_phone_code.delay.assert_not_called()

    def test_new_phone_saves_nothing_until_the_code(self):
        response = self.put(phone=NEW, name='Пётр')
        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.json(), {'phone': NEW, 'retry_after': 240, 'attempts_left': 5})
        self.assertEqual(self.send_phone_code.delay.call_args.args[0], NEW)
        self.user.refresh_from_db()
        self.assertEqual((self.user.phone, self.user.name), (PHONE, 'Иван'))

    def test_good_code_saves_everything(self):
        self.user.phone_verified = False  # created at checkout
        self.user.save()
        self.put(phone=NEW, name='Пётр')
        response = self.put(phone=NEW, name='Пётр', code=self.code())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['phone'], NEW)
        self.assertNotIn('code', response.json())
        self.user.refresh_from_db()
        self.assertEqual((self.user.phone, self.user.name), (NEW, 'Пётр'))
        self.assertTrue(self.user.phone_verified)
        self.assertFalse(PhoneCode.objects.exists())

    def test_patch_works_the_same(self):
        self.assertEqual(self.patch(phone=NEW).status_code, 202)
        self.assertEqual(self.patch(phone=NEW, code=self.code()).status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.phone, NEW)

    def test_wrong_code(self):
        self.put(phone=NEW)
        response = self.put(phone=NEW, code='wrong')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'code': ['Неверный или устаревший код']})
        self.assertEqual(PhoneCode.objects.get().attempts, 1)
        self.user.refresh_from_db()
        self.assertEqual(self.user.phone, PHONE)

    def test_code_is_bound_to_its_phone(self):
        self.put(phone=NEW)
        self.assertEqual(self.put(phone='+79160000000', code=self.code()).status_code, 400)
        self.user.refresh_from_db()
        self.assertEqual(self.user.phone, PHONE)

    def test_code_is_bound_to_its_user(self):
        self.put(phone=NEW)
        code = self.code()
        other = ShopUser.objects.create(phone='+79160000000')
        client = StorefrontClient()
        client.force_login(other)
        self.assertEqual(self.put(client=client, user=other, phone=NEW, code=code).status_code, 400)
        other.refresh_from_db()
        self.assertEqual(other.phone, '+79160000000')

    def test_registration_code_does_not_move_an_account(self):
        StorefrontClient().post('/api/v0/users/', {'phone': NEW}, format='json')
        self.assertEqual(self.put(phone=NEW, code=self.code()).status_code, 400)
        self.user.refresh_from_db()
        self.assertEqual(self.user.phone, PHONE)

    def test_taken_or_foreign_phone_sends_nothing(self):
        ShopUser.objects.create(phone=NEW)
        for phone in (NEW, '+375291234567'):
            response = self.put(phone=phone)
            self.assertEqual(response.status_code, 400, phone)
            self.assertIn('phone', response.json())
        self.send_phone_code.delay.assert_not_called()

    def test_resubmit_within_delay_sends_nothing(self):
        self.put(phone=NEW)
        self.put(phone=NEW)
        self.send_phone_code.delay.assert_called_once()
        PhoneCode.objects.update(expires=F('expires') - PhoneCode.RESEND_DELAY)
        self.put(phone=NEW)
        self.assertEqual(self.send_phone_code.delay.call_count, 2)

    def test_only_own_account(self):
        other = ShopUser.objects.create(phone='+79160000000')
        self.assertEqual(self.put(user=other, phone=NEW).status_code, 403)
        self.send_phone_code.delay.assert_not_called()

    def test_flags_are_read_only(self):
        self.put(email='me@example.com', email_verified=True, phone_verified=False)
        self.user.refresh_from_db()
        self.assertFalse(self.user.email_verified)
        self.assertTrue(self.user.phone_verified)
