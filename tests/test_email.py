"""
Email confirmation, and mail that goes only to confirmed addresses. SMS, Celery and Unisender are mocked,
mail goes to Django's test outbox. See settings.py on how to run.
"""
from datetime import timedelta
from importlib import import_module
from types import SimpleNamespace
from unittest import mock

from django.apps import apps
from django.contrib.admin.sites import site as admin_site
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.backends.db import SessionStore
from django.contrib.sites.models import Site
from django.core import mail
from django.core.cache import cache
from django.forms.models import model_to_dict
from django.test import RequestFactory, TestCase, override_settings
from django.utils import timezone

from shop import email_confirmation, tasks
from shop.models import Basket, Order, ShopUser

from .clients import StorefrontClient, add_storefront_key

PHONE = '+79161234567'
EMAIL = 'buyer@example.com'
CACHES = {'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}}


def token_for(user):
    return email_confirmation.make_token(user)


def mock_constance(test):
    # Constance refuses the local-memory cache that the throttles need, and the senders are all the tasks read from it
    config = SimpleNamespace(sw_email_from='shop@example.com', sw_email_unisender='shop@example.com')
    patcher = mock.patch('shop.tasks.config', new=config)  # given, so that mock does not look into the lazy original
    patcher.start()
    test.addCleanup(patcher.stop)


@override_settings(CACHES=CACHES)
class ApiBase(TestCase):
    def setUp(self):
        cache.clear()
        patcher = mock.patch('sewingworld.api.send_email_confirmation')
        self.link = patcher.start()
        self.addCleanup(patcher.stop)
        add_storefront_key()
        self.site = Site.objects.get_current()
        self.user = ShopUser.objects.create(phone=PHONE, phone_verified=True)
        self.client = StorefrontClient()
        self.client.force_login(self.user)

    def put(self, **body):
        body.setdefault('phone', self.user.phone)
        return self.client.put(f'/api/v0/users/{self.user.id}/', body, format='json')

    def send_link(self, client=None, user=None):
        return (client or self.client).post(f'/api/v0/users/{(user or self.user).id}/email-link/')

    def confirm(self, token, client=None):
        return (client or StorefrontClient()).post('/api/v0/users/confirm-email/', {'token': token}, format='json')


class ProfileTests(ApiBase):
    def test_new_email_is_unconfirmed_and_gets_a_link(self):
        self.user.email, self.user.email_verified = 'old@example.com', True
        self.user.save()
        response = self.put(email=EMAIL)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()['email_verified'])
        self.user.refresh_from_db()
        self.assertFalse(self.user.email_verified)
        self.link.delay.assert_called_once_with(self.user.id, EMAIL, self.site.id)

    def test_same_email_stays_confirmed(self):
        self.user.email, self.user.email_verified = EMAIL, True
        self.user.save()
        self.put(email=EMAIL, name='Иван')
        self.user.refresh_from_db()
        self.assertTrue(self.user.email_verified)
        self.link.delay.assert_not_called()

    def test_removed_email_gets_no_link(self):
        self.user.email, self.user.email_verified = EMAIL, True
        self.user.save()
        self.put(email='')
        self.user.refresh_from_db()
        self.assertFalse(self.user.email_verified)
        self.link.delay.assert_not_called()


class LinkTests(ApiBase):
    def setUp(self):
        super().setUp()
        self.user.email = EMAIL
        self.user.save()

    def test_link_again(self):
        self.assertEqual(self.send_link().status_code, 204)
        self.link.delay.assert_called_once_with(self.user.id, EMAIL, self.site.id)

    def test_own_account_only(self):
        self.assertEqual(self.send_link(client=StorefrontClient()).status_code, 403)
        other = ShopUser.objects.create(phone='+79160000000', email='other@example.com')
        self.assertEqual(self.send_link(user=other).status_code, 403)
        self.link.delay.assert_not_called()

    def test_nothing_to_confirm(self):
        self.user.email_verified = True
        self.user.save()
        self.assertEqual(self.send_link().status_code, 400)
        self.user.email, self.user.email_verified = '', False
        self.user.save()
        self.assertEqual(self.send_link().status_code, 400)
        self.link.delay.assert_not_called()

    def test_links_per_user_are_limited(self):
        for _ in range(3):
            self.assertEqual(self.send_link().status_code, 204)
        self.assertEqual(self.send_link().status_code, 429)
        self.assertEqual(self.link.delay.call_count, 3)

    def test_automatic_links_count_too_and_saving_goes_on(self):
        for n in range(4):
            self.assertEqual(self.put(email=f'{n}@example.com').status_code, 200)
        self.assertEqual(self.link.delay.call_count, 3)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, '3@example.com')

    def test_links_per_client_are_limited(self):
        for n in range(10):
            user = ShopUser.objects.create(phone=f'+7916000000{n}', email=f'{n}@example.com')
            client = StorefrontClient()
            client.force_login(user)
            self.assertEqual(self.send_link(client=client, user=user).status_code, 204)
        self.assertEqual(self.send_link().status_code, 429)


class ConfirmTests(ApiBase):
    def setUp(self):
        super().setUp()
        self.user.email = EMAIL
        self.user.save()

    def test_link_confirms_without_a_session(self):
        response = self.confirm(token_for(self.user))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'email': EMAIL})
        self.user.refresh_from_db()
        self.assertTrue(self.user.email_verified)

    def test_used_again(self):
        token = token_for(self.user)
        self.confirm(token)
        self.assertEqual(self.confirm(token).status_code, 200)

    def test_bad_tokens(self):
        for token in ('', 'garbage', token_for(self.user)[:-2] + 'xx', None):
            response = self.confirm(token)
            self.assertEqual(response.status_code, 400, token)
            self.assertEqual(response.json(), {'token': ['Ссылка недействительна или устарела']})
        self.user.refresh_from_db()
        self.assertFalse(self.user.email_verified)

    def test_expired(self):
        token = token_for(self.user)
        later = timezone.now() + email_confirmation.LIFETIME + timedelta(minutes=1)
        with mock.patch('django.core.signing.time.time', return_value=later.timestamp()):
            self.assertEqual(self.confirm(token).status_code, 400)

    def test_address_changed_since(self):
        token = token_for(self.user)
        self.user.email = 'new@example.com'
        self.user.save()
        self.assertEqual(self.confirm(token).status_code, 400)
        self.user.refresh_from_db()
        self.assertFalse(self.user.email_verified)

    def test_token_of_another_purpose_is_refused(self):
        from django.core import signing
        token = signing.dumps({'user': self.user.pk, 'email': EMAIL})  # no salt, as other signed values have
        self.assertEqual(self.confirm(token).status_code, 400)


class OrderEmailTests(ApiBase):
    def order(self, **kwargs):
        return Order.objects.create(user=self.user, site=self.site, **kwargs)

    def put_order(self, order, email):
        return self.client.put(f'/api/v0/orders/{order.id}/', {'email': email}, format='json')

    def test_address_typed_for_the_order_becomes_the_buyers(self):
        order = self.order()
        self.assertEqual(self.put_order(order, EMAIL).status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, EMAIL)
        self.assertFalse(self.user.email_verified)
        self.link.delay.assert_called_once_with(self.user.id, EMAIL, self.site.id)

    def test_buyer_with_an_address_keeps_it(self):
        self.user.email = 'own@example.com'
        self.user.save()
        self.put_order(self.order(), EMAIL)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'own@example.com')
        self.link.delay.assert_not_called()

    def test_address_of_another_user_is_not_taken(self):
        ShopUser.objects.create(phone='+79160000000', email=EMAIL.upper())
        self.put_order(self.order(), EMAIL)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, '')
        self.link.delay.assert_not_called()


@override_settings(CACHES=CACHES)
class ConfirmationMailTests(TestCase):
    def setUp(self):
        mock_constance(self)
        add_storefront_key()
        self.site = Site.objects.get_current()
        self.user = ShopUser.objects.create(phone=PHONE, email=EMAIL)

    def test_sends_the_link_to_the_storefront(self):
        tasks.send_email_confirmation(self.user.id, EMAIL, self.site.id)
        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertEqual(message.to, [EMAIL])
        self.assertIn(f'https://{self.site.domain}/confirm-email/?token=', message.body)
        token = message.body.split('?token=')[1].split()[0]
        self.assertEqual(StorefrontClient().post('/api/v0/users/confirm-email/', {'token': token.replace('%3A', ':')},
                                                 format='json').status_code, 200)

    def test_skips_changed_or_confirmed_address(self):
        tasks.send_email_confirmation(self.user.id, 'old@example.com', self.site.id)
        self.user.email_verified = True
        self.user.save()
        tasks.send_email_confirmation(self.user.id, EMAIL, self.site.id)
        tasks.send_email_confirmation(0, EMAIL, self.site.id)
        self.assertEqual(len(mail.outbox), 0)


@override_settings(CACHES=CACHES, UNISENDER_KEY='key', UNISENDER_PRODUCT_REVIEW_LIST=1, UNISENDER_ABANDONED_BASKET_LIST=2)
class OrderMailTests(TestCase):
    def setUp(self):
        mock_constance(self)
        add_storefront_key()
        self.site = Site.objects.get_current()
        self.user = ShopUser.objects.create(phone=PHONE, email=EMAIL, email_verified=True)
        patcher = mock.patch('shop.tasks.send_sms')
        self.sms = patcher.start()
        self.addCleanup(patcher.stop)

    def order(self, **kwargs):
        kwargs.setdefault('email', EMAIL)
        return Order.objects.create(user=self.user, site=self.site, phone=PHONE, **kwargs)

    def unconfirm(self):
        self.user.email_verified = False
        self.user.save()

    def test_confirmed_address_gets_mail(self):
        order = self.order(email=EMAIL.upper())  # the same address
        tasks.notify_user_order_new_mail(order.id)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [EMAIL.upper()])

    def test_unconfirmed_address_postpones_mail(self):
        self.unconfirm()
        order = self.order()
        with mock.patch.object(tasks.notify_user_order_new_mail, 'apply_async') as later:
            self.assertEqual(tasks.notify_user_order_new_mail(order.id), 'postponed')
        self.assertEqual(len(mail.outbox), 0)
        args, kwargs = later.call_args.args, later.call_args.kwargs
        self.assertEqual(args[0], (order.id,))
        self.assertEqual(kwargs['countdown'], 600)
        since = args[1]['since']

        # confirmed meanwhile: the postponed run sends it
        self.user.email_verified = True
        self.user.save()
        tasks.notify_user_order_new_mail(order.id, since=since)
        self.assertEqual(len(mail.outbox), 1)

    def test_waiting_grows_up_to_six_hours(self):
        self.unconfirm()
        order = self.order()
        for waited, delay in ((timedelta(0), 600), (timedelta(minutes=40), 2400), (timedelta(days=2), 6 * 3600)):
            since = (timezone.now() - waited).isoformat()
            with mock.patch.object(tasks.notify_user_order_new_mail, 'apply_async') as later:
                tasks.notify_user_order_new_mail(order.id, since=since)
            self.assertAlmostEqual(later.call_args.kwargs['countdown'], delay, delta=5)
            self.assertEqual(later.call_args.args[1], {'since': since})

    def test_dropped_when_the_link_would_have_expired(self):
        self.unconfirm()
        order = self.order()
        since = (timezone.now() - email_confirmation.LIFETIME).isoformat()
        with mock.patch.object(tasks.notify_user_order_new_mail, 'apply_async') as later:
            self.assertIsNone(tasks.notify_user_order_new_mail(order.id, since=since))
        later.assert_not_called()
        self.assertEqual(len(mail.outbox), 0)

    def test_no_address_nothing_to_wait_for(self):
        order = self.order(email='')
        with mock.patch.object(tasks.notify_user_order_new_mail, 'apply_async') as later:
            self.assertIsNone(tasks.notify_user_order_new_mail(order.id))
        later.assert_not_called()

    def test_address_other_than_the_buyers_waits(self):
        # It may still become the buyer's confirmed one, in the profile
        order = self.order(email='other@example.com')
        with mock.patch.object(tasks.notify_user_order_new_mail, 'apply_async') as later:
            tasks.notify_user_order_new_mail(order.id)
        later.assert_called_once()
        self.assertEqual(len(mail.outbox), 0)

    def test_status_mail_sends_sms_once(self):
        self.unconfirm()
        order = self.order(delivery=Order.DELIVERY_TRANSPORT)
        for task in (tasks.notify_user_order_collected, tasks.notify_user_order_delivered):
            self.sms.reset_mock()
            with mock.patch.object(task, 'apply_async') as later:
                task(order.id)
                self.sms.assert_called_once()
                task(order.id, since=later.call_args.args[1]['since'])
                self.sms.assert_called_once()  # not again
            self.assertEqual(later.call_count, 2)
        self.assertEqual(len(mail.outbox), 0)

    def test_status_mail_to_confirmed_address(self):
        order = self.order(delivery=Order.DELIVERY_TRANSPORT)
        tasks.notify_user_order_collected(order.id)
        tasks.notify_user_order_delivered(order.id)
        self.assertEqual([message.to for message in mail.outbox], [[EMAIL], [EMAIL]])

    def test_review_request(self):
        order = self.order()
        with mock.patch('shop.tasks.Unisender') as unisender:
            unisender.return_value.errorMessage = None
            unisender.return_value.sendEmail.return_value = {'result': [{'index': 0, 'id': 'sent'}]}
            self.assertEqual(tasks.notify_user_review_products(order.id), 'sent')
            self.assertEqual(unisender.return_value.sendEmail.call_args.args[0], EMAIL)

            self.unconfirm()
            unisender.reset_mock()
            with mock.patch.object(tasks.notify_user_review_products, 'apply_async') as later:
                self.assertEqual(tasks.notify_user_review_products(order.id), 'postponed')
            later.assert_called_once()
            unisender.return_value.sendEmail.assert_not_called()

    def abandoned_basket(self):
        session = SessionStore()
        session['_auth_user_id'] = str(self.user.id)
        session.create()
        basket = Basket.objects.create(site=self.site, session_id=session.session_key)
        Basket.objects.filter(pk=basket.pk).update(created=timezone.now() - timedelta(hours=3, minutes=30))
        # Not empty: saving a real product sets off integrations' signals
        patcher = mock.patch.object(Basket, 'items', new_callable=mock.PropertyMock,
                                    return_value=mock.Mock(count=mock.Mock(return_value=1)))
        patcher.start()
        self.addCleanup(patcher.stop)
        return basket

    def test_abandoned_basket_only_to_confirmed_address(self):
        basket = self.abandoned_basket()
        with mock.patch.object(tasks.notify_abandoned_basket, 'delay') as notify:
            self.unconfirm()
            self.assertEqual(tasks.notify_abandoned_baskets(), 0)
            notify.assert_not_called()
            self.user.email_verified = True
            self.user.save()
            self.assertEqual(tasks.notify_abandoned_baskets(), 1)
            notify.assert_called_once_with(basket.id, EMAIL, PHONE)


class FirstSmsProofTests(TestCase):
    """ See also test_login_codes.SilentRegistrationTests """

    def test_migration_trusts_existing_users_once(self):
        with_email = ShopUser.objects.create(phone=PHONE, email=EMAIL)
        without = ShopUser.objects.create(phone='+79160000000')
        migration = import_module('shop.migrations.0266_shopuser_email_verified_phone_verified')
        migration.trust_existing(apps, None)
        with_email.refresh_from_db()
        without.refresh_from_db()
        self.assertEqual((with_email.email_verified, with_email.phone_verified), (True, True))
        self.assertEqual((without.email_verified, without.phone_verified), (False, True))
        self.assertFalse(ShopUser.objects.create(phone='+79161111111', email='new@example.com').email_verified)


class AdminTests(TestCase):
    def setUp(self):
        self.staff = ShopUser.objects.create(phone='+79990000000', is_staff=True, is_superuser=True)
        self.user = ShopUser.objects.create(phone=PHONE)

    def request(self):
        request = RequestFactory().post('/')
        request.user = self.staff
        request.session = SessionStore()
        request._messages = FallbackStorage(request)
        return request

    def change_user(self, **changes):
        model_admin = admin_site._registry[ShopUser]
        request = self.request()
        form_class = model_admin.get_form(request, self.user, change=True)
        data = {key: value for key, value in model_to_dict(self.user).items() if value is not None}
        data.update(changes)
        form = form_class(data, instance=self.user)
        self.assertTrue(form.is_valid(), form.errors)
        return form.save()

    def test_staff_entered_email_and_phone_are_confirmed(self):
        user = self.change_user(email=EMAIL, phone='+79167654321')
        self.assertTrue(user.email_verified)
        self.assertTrue(user.phone_verified)

    def test_staff_can_leave_them_unconfirmed(self):
        user = self.change_user(email=EMAIL, email_verified=True)
        self.assertTrue(user.email_verified)
        self.user.refresh_from_db()
        user = self.change_user(email='other@example.com', email_verified=False)
        self.assertFalse(user.email_verified)

    def test_other_edits_keep_the_flags(self):
        user = self.change_user(name='Иван')
        self.assertFalse(user.email_verified)
        self.assertFalse(user.phone_verified)

    def add_user(self, **data):
        model_admin = admin_site._registry[ShopUser]
        form_class = model_admin.get_form(self.request(), None, change=False)
        return form_class({'phone': '+79161111111', 'name': '', **data})

    def test_technical_user_without_password(self):
        form = self.add_user()
        self.assertTrue(form.is_valid(), form.errors)
        user = form.save()
        self.assertFalse(user.has_usable_password())
        self.assertTrue(user.phone_verified)

    def test_short_password_is_refused(self):
        self.assertFalse(self.add_user(password1='short', password2='short').is_valid())
        self.assertFalse(self.add_user(password1='long-enough', password2='other-one').is_valid())
        form = self.add_user(password1='long-enough', password2='long-enough')
        self.assertTrue(form.is_valid(), form.errors)
        self.assertTrue(form.save().check_password('long-enough'))

    def test_order_email_entered_by_staff(self):
        order = Order.objects.create(user=self.user, site=Site.objects.get_current(), email=EMAIL)
        request = self.request()
        admin_site._registry[Order].confirm_user_email(request, order)
        self.user.refresh_from_db()
        self.assertEqual((self.user.email, self.user.email_verified), (EMAIL, True))

    def test_order_email_of_another_user(self):
        ShopUser.objects.create(phone='+79160000000', email=EMAIL)
        self.user.email = 'own@example.com'
        self.user.save()
        order = Order.objects.create(user=self.user, site=Site.objects.get_current(), email=EMAIL)
        request = self.request()
        admin_site._registry[Order].confirm_user_email(request, order)
        self.user.refresh_from_db()
        self.assertEqual((self.user.email, self.user.email_verified), ('own@example.com', False))
        self.assertEqual(len(request._messages), 1)

    def test_order_of_a_marketplace_account(self):
        service = ShopUser.objects.create(phone='0001')
        order = Order.objects.create(user=service, site=Site.objects.get_current(), email=EMAIL)
        admin_site._registry[Order].confirm_user_email(self.request(), order)
        service.refresh_from_db()
        self.assertEqual(service.email, '')
