"""
SMS login through the real endpoints and PostgreSQL, only SMS sending is mocked. See settings.py on how to run.
"""
import threading
from datetime import timedelta
from unittest import mock

from django.core.cache import cache
from django.db import connection
from django.db.models import F
from django.test import TestCase, TransactionTestCase, override_settings
from django.utils import timezone

from shop.models import LoginCode, ShopUser

from .clients import StorefrontClient, add_storefront_key

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
        add_storefront_key()
        self.client = StorefrontClient()

    def check(self, phone=PHONE, client=None, **body):
        return (client or self.client).post(f'/api/v0/users/{phone}/check/', body, format='json')

    def login(self, client=None, **body):
        body.setdefault('phone', PHONE)
        return (client or self.client).post('/api/v0/users/login/', body, format='json')

    def code(self):
        return self.sms.delay.call_args.args[1]

    def resend_delay_passes(self):
        LoginCode.objects.update(expires=F('expires') - LoginCode.RESEND_DELAY)

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
        self.assertEqual(self.login(client=StorefrontClient(), password=code).status_code, 403)

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
            self.resend_delay_passes()
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


class ResendTests(Base):
    def test_new_code_reports_full_delay_and_attempts(self):
        self.customer()
        self.assertEqual(self.check().json(), {
            'phone': PHONE, 'permanent_password': False, 'retry_after': 240, 'attempts_left': 5
        })

    def test_recent_code_is_kept_and_delay_goes_on(self):
        user = self.customer()
        self.check()
        code = self.code()
        LoginCode.objects.filter(user=user).update(expires=F('expires') - timedelta(seconds=100))
        response = self.check()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.sms.delay.call_count, 1)
        self.assertAlmostEqual(response.json()['retry_after'], 140, delta=2)
        self.assertEqual(self.login(password=code).status_code, 200)

    def test_recent_code_keeps_attempts(self):
        self.customer()
        self.check()
        self.login(password=WRONG_CODE)
        self.login(password=WRONG_CODE)
        self.assertEqual(self.check().json()['attempts_left'], 3)

    def test_new_code_when_delay_has_passed(self):
        self.customer()
        with mock.patch('shop.models.user.secrets.randbelow', side_effect=[111111, 222222]):
            self.check()
            self.resend_delay_passes()
            response = self.check()
        self.assertEqual(self.sms.delay.call_count, 2)
        self.assertEqual(response.json()['retry_after'], 240)
        self.assertEqual(self.login(password='111111').status_code, 403)
        self.assertEqual(self.login(password='222222').status_code, 200)

    def test_new_code_at_once_when_attempts_run_out(self):
        self.customer()
        self.check()
        for _ in range(LoginCode.MAX_ATTEMPTS):
            self.login(password=WRONG_CODE)
        self.assertEqual(self.check().json()['attempts_left'], LoginCode.MAX_ATTEMPTS)
        self.assertEqual(self.sms.delay.call_count, 2)

    def test_new_code_at_once_after_code_is_used(self):
        self.customer()
        self.check()
        self.login(password=self.code())
        self.check(client=StorefrontClient())
        self.assertEqual(self.sms.delay.call_count, 2)

    def test_reset_keeps_recent_code(self):
        self.permanent()
        self.check(reset=True)
        response = self.check(reset=True).json()
        self.assertEqual(self.sms.delay.call_count, 1)
        self.assertFalse(response['permanent_password'])
        self.assertGreater(response['retry_after'], 0)
        self.assertEqual(response['attempts_left'], LoginCode.MAX_ATTEMPTS)

    def test_password_step_ignores_pending_reset(self):
        self.permanent()
        self.check(reset=True)
        self.assertEqual(self.check().json(), {
            'phone': PHONE, 'permanent_password': True, 'retry_after': 0, 'attempts_left': 0
        })

    def test_limit_counts_sent_codes_only(self):
        self.customer()
        for _ in range(8):
            self.assertEqual(self.check().status_code, 200)
        self.assertEqual(self.sms.delay.call_count, 1)

    def test_limit_does_not_apply_when_nothing_is_sent(self):
        self.permanent()
        for _ in range(8):
            self.assertEqual(self.check().status_code, 200)

    def test_over_limit_recent_code_is_still_reported(self):
        user = self.customer()
        for _ in range(4):
            self.check()
            self.resend_delay_passes()
        self.check()
        self.assertEqual(self.check().status_code, 200)
        self.resend_delay_passes()
        before = LoginCode.objects.get(user=user).code_hash
        self.assertEqual(self.check().status_code, 429)
        self.assertEqual(self.sms.delay.call_count, 5)
        self.assertEqual(LoginCode.objects.get(user=user).code_hash, before)

    def test_failed_sending_does_not_start_delay(self):
        self.customer()
        self.sms.delay.side_effect = [ConnectionError, None]
        with self.assertRaises(ConnectionError):
            self.check()
        self.assertFalse(LoginCode.objects.exists())
        self.assertEqual(self.check().json()['retry_after'], 240)
        self.assertEqual(self.sms.delay.call_count, 2)


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
        self.check(client=StorefrontClient())
        self.assertIsNotNone(self.current())


class LookupTests(Base):
    def test_user_id_does_not_reveal_phone(self):
        user = self.customer()
        response = self.check(user.id)
        self.assertEqual(response.status_code, 400)  # not a phone
        self.assertNotIn(PHONE, response.content.decode())
        self.assertNotIn(PHONE[1:], response.content.decode())
        self.sms.delay.assert_not_called()
        self.assertFalse(LoginCode.objects.filter(user=user).exists())

    def test_user_id_of_staff_does_not_reveal_phone(self):
        user = self.customer(is_staff=True, is_superuser=True)
        self.assertEqual(self.check(user.id).status_code, 400)
        self.sms.delay.assert_not_called()

    def test_current_is_not_a_phone(self):
        self.assertEqual(self.check('current').status_code, 400)
        self.customer()
        self.check()
        self.login(password=self.code())
        self.assertEqual(self.check('current').status_code, 400)

    def test_any_form_of_phone_finds_user(self):
        self.customer()
        for phone in (PHONE, '79161234567', '9161234567'):
            self.assertEqual(self.check(phone).json()['phone'], PHONE)

    def test_unregistered_phone(self):
        self.assertEqual(self.check().status_code, 404)
        self.sms.delay.assert_not_called()

    def test_only_russian_phones(self):
        # Old accounts with such phones exist, they get no SMS and can't log in
        for phone in ('+375291234567', '+79161234', '+791612345678'):
            ShopUser.objects.create(phone=phone)
            response = self.check(phone)
            self.assertEqual(response.status_code, 400, phone)
            self.assertIn('phone', response.json())
            self.assertEqual(self.login(phone=phone, ctx='order').status_code, 403, phone)
        self.sms.delay.assert_not_called()

    def test_silent_registration_needs_russian_phone(self):
        self.assertEqual(self.login(phone='+375291234567', ctx='order').status_code, 403)
        self.assertFalse(ShopUser.objects.filter(phone='+375291234567').exists())

    def test_forms_of_phone_share_rate_limit(self):
        self.customer()
        for phone in (PHONE, '79161234567', '9161234567', PHONE, '79161234567'):
            self.assertEqual(self.check(phone).status_code, 200)
            self.resend_delay_passes()
        self.assertEqual(self.check('9161234567').status_code, 429)
        self.assertEqual(self.sms.delay.call_count, 5)


class PermanentPasswordTests(Base):
    def test_password_login_sends_no_code(self):
        user = self.permanent()
        response = self.check()
        self.assertEqual(response.json(), {'phone': PHONE, 'permanent_password': True, 'retry_after': 0, 'attempts_left': 0})
        self.sms.delay.assert_not_called()
        self.assertEqual(self.login(password='old-secret').status_code, 200)
        self.assertEqual(self.current(), user.id)

    def test_wrong_password(self):
        self.permanent()
        self.assertEqual(self.login(password='nope-nope').status_code, 403)

    def test_password_can_be_changed_with_password(self):
        self.permanent()
        self.assertEqual(self.login(password='old-secret', permanent_password='new-secret').status_code, 200)
        self.assertEqual(self.login(client=StorefrontClient(), password='new-secret').status_code, 200)

    def test_reset_keeps_password_and_sessions_until_code_is_proven(self):
        user = self.permanent()
        self.login(password='old-secret')
        response = self.check(reset=True, client=StorefrontClient())
        self.assertFalse(response.json()['permanent_password'])
        self.sms.delay.assert_called_once()
        user.refresh_from_db()
        self.assertTrue(user.permanent_password)
        self.assertEqual(self.current(), user.id)
        self.assertEqual(self.login(client=StorefrontClient(), password='old-secret').status_code, 200)

    def test_proven_reset_drops_password_and_other_sessions(self):
        user = self.permanent()
        other = StorefrontClient()
        self.login(client=other, password='old-secret')
        self.check(reset=True)
        self.assertEqual(self.login(password=self.code()).status_code, 200)
        user.refresh_from_db()
        self.assertFalse(user.permanent_password)
        self.assertFalse(user.has_usable_password())
        self.assertIsNone(self.current(other))
        self.assertEqual(self.current(), user.id)
        self.assertEqual(self.login(client=StorefrontClient(), password='old-secret').status_code, 403)

    def test_reset_can_set_new_password_in_one_request(self):
        user = self.permanent()
        self.check(reset=True)
        self.assertEqual(self.login(password=self.code(), permanent_password='new-secret').status_code, 200)
        user.refresh_from_db()
        self.assertTrue(user.permanent_password)
        self.assertEqual(self.current(), user.id)
        self.assertEqual(self.login(client=StorefrontClient(), password='new-secret').status_code, 200)
        self.assertEqual(self.login(client=StorefrontClient(), password='old-secret').status_code, 403)

    def test_remembered_password_works_while_reset_code_is_pending(self):
        self.permanent()
        self.check(reset=True)
        self.assertEqual(self.login(password='old-secret').status_code, 200)

    def test_code_can_set_permanent_password(self):
        user = self.customer()
        self.check()
        self.assertEqual(self.login(password=self.code(), permanent_password='my-secret').status_code, 200)
        self.assertEqual(self.current(), user.id)
        self.assertEqual(self.login(client=StorefrontClient(), password='my-secret').status_code, 200)

    def test_short_permanent_password_is_refused_and_code_survives(self):
        user = self.customer()
        self.check()
        response = self.login(password=self.code(), permanent_password='short')
        self.assertEqual(response.status_code, 400)
        self.assertIn('permanent_password', response.json())
        self.assertIsNone(self.current())
        self.assertEqual(LoginCode.objects.get(user=user).attempts, 0)
        self.assertEqual(self.login(password=self.code(), permanent_password='long-enough').status_code, 200)

    def test_old_short_password_still_logs_in(self):
        self.permanent(password='12345')
        self.assertEqual(self.login(password='12345').status_code, 200)


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
            self.assertEqual(self.login(client=StorefrontClient(), phone=f'+7916000000{n}', ctx=ctx).status_code, 200)

    def test_other_context_does_not_register(self):
        self.assertEqual(self.login(ctx='reg').status_code, 403)
        self.assertFalse(ShopUser.objects.filter(phone=PHONE).exists())

    def test_cannot_plant_permanent_password(self):
        self.assertEqual(self.login(ctx='order', permanent_password='planted-password').status_code, 200)
        user = ShopUser.objects.get(phone=PHONE)
        self.assertFalse(user.has_usable_password())
        self.assertFalse(user.permanent_password)
        self.assertEqual(self.login(client=StorefrontClient(), password='planted-password').status_code, 403)

    def test_phone_is_unproven_until_owner_logs_in_with_a_code(self):
        user_id = self.login(ctx='order').json()['id']
        self.assertFalse(ShopUser.objects.get(pk=user_id).phone_verified)
        client = StorefrontClient()
        self.check(client=client)
        self.login(client=client, password=self.code())
        self.assertTrue(ShopUser.objects.get(pk=user_id).phone_verified)

    def test_first_proof_resets_email_confirmed_before_it(self):
        # Whoever created the account at checkout could have confirmed their own address in it
        user_id = self.login(ctx='order').json()['id']
        ShopUser.objects.filter(pk=user_id).update(email='stranger@example.com', email_verified=True)
        client = StorefrontClient()
        self.check(client=client)
        self.login(client=client, password=self.code())
        user = ShopUser.objects.get(pk=user_id)
        self.assertTrue(user.phone_verified)
        self.assertFalse(user.email_verified)
        self.assertEqual(user.email, 'stranger@example.com')  # the owner sees it in the profile and decides

    def test_later_logins_keep_confirmed_email(self):
        user = self.customer(phone_verified=True, email='owner@example.com', email_verified=True)
        self.check()
        self.login(password=self.code())
        user.refresh_from_db()
        self.assertTrue(user.email_verified)

    def test_existing_account_needs_proof_even_with_context(self):
        self.login(ctx='order')
        self.assertEqual(self.login(client=StorefrontClient(), ctx='order').status_code, 403)

    def test_owner_gets_a_code_later(self):
        user = ShopUser.objects.get(pk=self.login(ctx='order').json()['id'])
        client = StorefrontClient()
        self.assertFalse(self.check(client=client).json()['permanent_password'])
        response = self.login(client=client, password=self.code())
        self.assertEqual(response.json(), {'id': user.id, 'registered': False})

    def test_unproven_session_dies_when_owner_proves_the_phone(self):
        unproven = StorefrontClient()
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


@override_settings(CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}})
class RaceTests(TransactionTestCase):
    serialized_rollback = True  # the current Site from migrations, which an earlier TransactionTestCase flushes

    def test_parallel_verification_uses_code_once(self):
        user = ShopUser.objects.create(phone=PHONE)
        for _ in range(5):
            code = LoginCode.issue(user)[0]
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

    @mock.patch('sewingworld.api.send_password')
    def test_parallel_requests_send_one_code(self, sms):
        add_storefront_key()
        ShopUser.objects.create(phone=PHONE)
        for _ in range(5):
            cache.clear()
            LoginCode.objects.all().delete()
            sms.reset_mock()
            barrier = threading.Barrier(6)

            def request():
                barrier.wait()
                StorefrontClient().post(f'/api/v0/users/{PHONE}/check/', {}, format='json')
                connection.close()

            threads = [threading.Thread(target=request) for _ in range(6)]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()
            self.assertEqual(sms.delay.call_count, 1)
