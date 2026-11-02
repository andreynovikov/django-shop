"""
SMS login through the real endpoints and PostgreSQL, only SMS sending is mocked. See settings.py on how to run.
"""
import threading
from datetime import timedelta
from unittest import mock

from django.core.cache import cache
from django.db import connection
from django.test import TestCase, TransactionTestCase, override_settings
from django.utils import timezone

from rest_framework.test import APIClient

from shop.models import LoginCode, ShopUser

PHONE = '+79161234567'
OTHER = '+79167654321'
WRONG_CODE = 'wrong'


# Throttles count attempts in cache and tests clear it, so that they never touch the shared memcached
@override_settings(CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}})
class Base(TestCase):
    def setUp(self):
        cache.clear()
        patcher = mock.patch('sewingworld.api.send_password')
        self.sms = patcher.start()
        self.addCleanup(patcher.stop)
        self.client = APIClient()

    def check(self, phone=PHONE, client=None, **body):
        return (client or self.client).post(f'/api/v0/users/{phone}/check/', body, format='json')

    def login(self, client=None, **body):
        body.setdefault('phone', PHONE)
        return (client or self.client).post('/api/v0/users/login/', body, format='json')

    def code(self):
        return self.sms.delay.call_args.args[1]

    def current(self, client=None):
        return (client or self.client).get('/api/v0/users/current/').json()['id']

    def customer(self, phone=PHONE, **kwargs):
        return ShopUser.objects.create(phone=phone, **kwargs)

    def permanent(self, password='old-secret', **kwargs):
        user = self.customer(permanent_password=True, **kwargs)
        user.set_password(password)
        user.save()
        return user


class CodeTests(Base):
    def test_six_digits_and_only_hash_stored(self):
        user = self.customer()
        self.assertEqual(self.check().status_code, 200)
        self.assertRegex(self.code(), r'^\d{6}$')
        stored = LoginCode.objects.get(user=user)
        self.assertNotIn(self.code(), stored.code_hash)
        self.assertEqual(len(stored.code_hash), 64)

    def test_generated_with_secrets_and_leading_zeros_survive(self):
        self.customer()
        with mock.patch('shop.models.user.secrets.randbelow', return_value=42) as randbelow:
            self.check()
        randbelow.assert_called_once_with(10 ** 6)
        self.assertEqual(self.code(), '000042')
        self.assertEqual(self.login(password='000042').status_code, 200)

    def test_good_code_logs_in(self):
        user = self.customer()
        self.check()
        response = self.login(password=self.code())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'id': user.id, 'registered': False})
        self.assertEqual(self.current(), user.id)

    def test_single_use(self):
        self.customer()
        self.check()
        code = self.code()
        self.assertEqual(self.login(password=code).status_code, 200)
        self.assertEqual(self.login(client=APIClient(), password=code).status_code, 403)

    def test_expires_after_five_minutes(self):
        user = self.customer()
        self.check()
        stored = LoginCode.objects.get(user=user)
        self.assertAlmostEqual(stored.expires, timezone.now() + timedelta(minutes=5), delta=timedelta(seconds=5))
        LoginCode.objects.filter(user=user).update(expires=timezone.now() - timedelta(seconds=1))
        self.assertEqual(self.login(password=self.code()).status_code, 403)
        self.assertFalse(LoginCode.objects.filter(user=user).exists())

    def test_valid_just_before_expiry(self):
        user = self.customer()
        self.check()
        LoginCode.objects.filter(user=user).update(expires=timezone.now() + timedelta(seconds=5))
        self.assertEqual(self.login(password=self.code()).status_code, 200)

    def test_attempts_are_counted_and_cap_kills_the_code(self):
        user = self.customer()
        self.check()
        for attempt in range(1, 5):
            self.assertEqual(self.login(password=WRONG_CODE).status_code, 403)
            self.assertEqual(LoginCode.objects.get(user=user).attempts, attempt)
        self.assertEqual(self.login(password=WRONG_CODE).status_code, 403)
        self.assertFalse(LoginCode.objects.filter(user=user).exists())
        self.assertEqual(self.login(password=self.code()).status_code, 403)

    def test_good_code_on_last_attempt(self):
        self.customer()
        self.check()
        for _ in range(4):
            self.login(password=WRONG_CODE)
        self.assertEqual(self.login(password=self.code()).status_code, 200)

    def test_new_code_replaces_old_and_resets_attempts(self):
        user = self.customer()
        with mock.patch('shop.models.user.secrets.randbelow', side_effect=[111111, 222222]):
            self.check()
            self.login(password=WRONG_CODE)
            self.check()
        self.assertEqual(LoginCode.objects.get(user=user).attempts, 0)
        self.assertEqual(self.login(password='111111').status_code, 403)
        self.assertEqual(self.login(password='222222').status_code, 200)

    def test_code_of_another_user_is_refused(self):
        self.customer()
        self.customer(phone=OTHER)
        with mock.patch('shop.models.user.secrets.randbelow', side_effect=[111111, 222222]):
            self.check(OTHER)
            self.check()
        self.assertEqual(self.login(password='111111').status_code, 403)

    def test_inactive_user_cannot_log_in(self):
        self.customer(is_active=False)
        self.check()
        self.assertEqual(self.login(password=self.code()).status_code, 403)

    def test_missing_password(self):
        self.customer()
        self.check()
        self.assertEqual(self.login().status_code, 403)


class SeparationTests(Base):
    def test_check_changes_nothing_on_the_account(self):
        user = self.customer()
        user.set_password('anything')
        user.save()
        before = ShopUser.objects.get(pk=user.pk).password
        self.check()
        self.assertEqual(ShopUser.objects.get(pk=user.pk).password, before)

    def test_code_stored_as_password_before_login_codes_is_dead(self):
        user = self.customer()
        user.set_password('1234')
        user.save()
        self.assertEqual(self.login(password='1234').status_code, 403)

    def test_check_does_not_log_user_out(self):
        self.customer()
        self.check()
        self.login(password=self.code())
        self.assertIsNotNone(self.current())
        self.check(client=APIClient())
        self.assertIsNotNone(self.current())


class LookupTests(Base):
    def test_user_id_does_not_reveal_phone(self):
        user = self.customer()
        response = self.check(user.id)
        self.assertEqual(response.status_code, 404)
        self.assertNotIn(PHONE, response.content.decode())
        self.assertNotIn(PHONE[1:], response.content.decode())
        self.sms.delay.assert_not_called()
        self.assertFalse(LoginCode.objects.filter(user=user).exists())

    def test_user_id_of_staff_does_not_reveal_phone(self):
        user = self.customer(is_staff=True, is_superuser=True)
        self.assertEqual(self.check(user.id).status_code, 404)
        self.sms.delay.assert_not_called()

    def test_current_is_not_a_phone(self):
        self.assertEqual(self.check('current').status_code, 404)
        self.customer()
        self.check()
        self.login(password=self.code())
        self.assertEqual(self.check('current').status_code, 404)

    def test_any_form_of_phone_finds_user(self):
        self.customer()
        for phone in (PHONE, '79161234567', '9161234567'):
            self.assertEqual(self.check(phone).json(), {'phone': PHONE, 'permanent_password': False})

    def test_unregistered_phone(self):
        self.assertEqual(self.check().status_code, 404)
        self.sms.delay.assert_not_called()

    def test_forms_of_phone_share_rate_limit(self):
        self.customer()
        for phone in (PHONE, '79161234567', '9161234567', PHONE, '79161234567'):
            self.assertEqual(self.check(phone).status_code, 200)
        self.assertEqual(self.check('9161234567').status_code, 429)
        self.assertEqual(self.sms.delay.call_count, 5)


class PermanentPasswordTests(Base):
    def test_password_login_sends_no_code(self):
        user = self.permanent()
        response = self.check()
        self.assertEqual(response.json(), {'phone': PHONE, 'permanent_password': True})
        self.sms.delay.assert_not_called()
        self.assertEqual(self.login(password='old-secret').status_code, 200)
        self.assertEqual(self.current(), user.id)

    def test_wrong_password(self):
        self.permanent()
        self.assertEqual(self.login(password='nope-nope').status_code, 403)

    def test_password_can_be_changed_with_password(self):
        self.permanent()
        self.assertEqual(self.login(password='old-secret', permanent_password='new-secret').status_code, 200)
        self.assertEqual(self.login(client=APIClient(), password='new-secret').status_code, 200)

    def test_reset_keeps_password_and_sessions_until_code_is_proven(self):
        user = self.permanent()
        self.login(password='old-secret')
        response = self.check(reset=True, client=APIClient())
        self.assertEqual(response.json(), {'phone': PHONE, 'permanent_password': False})
        self.sms.delay.assert_called_once()
        user.refresh_from_db()
        self.assertTrue(user.permanent_password)
        self.assertEqual(self.current(), user.id)
        self.assertEqual(self.login(client=APIClient(), password='old-secret').status_code, 200)

    def test_proven_reset_drops_password_and_other_sessions(self):
        user = self.permanent()
        other = APIClient()
        self.login(client=other, password='old-secret')
        self.check(reset=True)
        self.assertEqual(self.login(password=self.code()).status_code, 200)
        user.refresh_from_db()
        self.assertFalse(user.permanent_password)
        self.assertFalse(user.has_usable_password())
        self.assertIsNone(self.current(other))
        self.assertEqual(self.current(), user.id)
        self.assertEqual(self.login(client=APIClient(), password='old-secret').status_code, 403)

    def test_reset_can_set_new_password_in_one_request(self):
        user = self.permanent()
        self.check(reset=True)
        self.assertEqual(self.login(password=self.code(), permanent_password='new-secret').status_code, 200)
        user.refresh_from_db()
        self.assertTrue(user.permanent_password)
        self.assertEqual(self.current(), user.id)
        self.assertEqual(self.login(client=APIClient(), password='new-secret').status_code, 200)
        self.assertEqual(self.login(client=APIClient(), password='old-secret').status_code, 403)

    def test_remembered_password_works_while_reset_code_is_pending(self):
        self.permanent()
        self.check(reset=True)
        self.assertEqual(self.login(password='old-secret').status_code, 200)

    def test_code_can_set_permanent_password(self):
        user = self.customer()
        self.check()
        self.assertEqual(self.login(password=self.code(), permanent_password='my-secret').status_code, 200)
        self.assertEqual(self.current(), user.id)
        self.assertEqual(self.login(client=APIClient(), password='my-secret').status_code, 200)


class SilentRegistrationTests(Base):
    def test_gets_unusable_password_and_no_sms(self):
        response = self.login(ctx='order')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['registered'])
        user = ShopUser.objects.get(phone=PHONE)
        self.assertEqual(self.current(), user.id)
        self.assertFalse(user.has_usable_password())
        self.assertFalse(user.permanent_password)
        self.sms.delay.assert_not_called()

    def test_all_contexts(self):
        for n, ctx in enumerate(('order', 'preorder', 'warranty')):
            self.assertEqual(self.login(client=APIClient(), phone=f'+7916000000{n}', ctx=ctx).status_code, 200)

    def test_other_context_does_not_register(self):
        self.assertEqual(self.login(ctx='reg').status_code, 403)
        self.assertFalse(ShopUser.objects.filter(phone=PHONE).exists())

    def test_cannot_plant_permanent_password(self):
        self.assertEqual(self.login(ctx='order', permanent_password='planted').status_code, 200)
        user = ShopUser.objects.get(phone=PHONE)
        self.assertFalse(user.has_usable_password())
        self.assertFalse(user.permanent_password)
        self.assertEqual(self.login(client=APIClient(), password='planted').status_code, 403)

    def test_existing_account_needs_proof_even_with_context(self):
        self.login(ctx='order')
        self.assertEqual(self.login(client=APIClient(), ctx='order').status_code, 403)

    def test_owner_gets_a_code_later(self):
        user = ShopUser.objects.get(pk=self.login(ctx='order').json()['id'])
        client = APIClient()
        self.assertEqual(self.check(client=client).json(), {'phone': PHONE, 'permanent_password': False})
        response = self.login(client=client, password=self.code())
        self.assertEqual(response.json(), {'id': user.id, 'registered': False})

    def test_unproven_session_dies_when_owner_proves_the_phone(self):
        unproven = APIClient()
        user_id = self.login(client=unproven, ctx='order').json()['id']
        self.assertEqual(self.current(unproven), user_id)
        self.check()
        self.assertEqual(self.current(unproven), user_id)  # nothing proven yet, this is not a way to log anyone out
        self.login(password=self.code())
        self.assertEqual(self.current(), user_id)
        self.assertIsNone(self.current(unproven))


class StaffTests(Base):
    def staff(self, **kwargs):
        user = self.customer(is_staff=True, **kwargs)
        user.set_password('admin-secret')
        user.save()
        return user

    def test_check_keeps_admin_password(self):
        user = self.staff()
        self.check()
        user.refresh_from_db()
        self.assertTrue(user.check_password('admin-secret'))

    def test_sms_login_keeps_admin_password(self):
        user = self.staff()
        self.check()
        self.assertEqual(self.login(password=self.code()).status_code, 200)
        user.refresh_from_db()
        self.assertTrue(user.check_password('admin-secret'))
        self.assertEqual(self.current(), user.id)

    def test_reset_keeps_permanent_password(self):
        user = self.staff(permanent_password=True)
        self.check(reset=True)
        self.assertEqual(self.login(password=self.code()).status_code, 200)
        user.refresh_from_db()
        self.assertTrue(user.check_password('admin-secret'))
        self.assertTrue(user.permanent_password)


class RaceTests(TransactionTestCase):
    def test_parallel_verification_uses_code_once(self):
        user = ShopUser.objects.create(phone=PHONE)
        for _ in range(5):
            code = LoginCode.issue(user)
            barrier = threading.Barrier(6)
            results = []

            def attempt():
                barrier.wait()
                results.append(LoginCode.verify(user, code))
                connection.close()

            threads = [threading.Thread(target=attempt) for _ in range(6)]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()
            self.assertEqual(sorted(results), [False] * 5 + [True])
