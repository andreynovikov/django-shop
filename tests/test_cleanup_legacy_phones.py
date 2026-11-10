"""
The command that repairs or removes accounts with phones that are not +7. See settings.py on how to run.
"""
from datetime import timedelta
from io import StringIO

from django.contrib.admin.models import ADDITION, LogEntry
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from shop.management.commands.cleanup_legacy_phones import is_unreal
from rest_framework.authtoken.models import Token

from shop.models import Bonus, Order, Serial, ShopUser


class UnrealTests(TestCase):
    def test_unreal(self):
        for phone in ('+7150', '+79161234', '+7916123456789', '+70000000000', '+71234567890', '+79876543210', '12345'):
            self.assertTrue(is_unreal(phone), phone)

    def test_real_enough(self):
        for phone in ('+375291234567', '+79161234567', '+380501234567'):
            self.assertFalse(is_unreal(phone), phone)


class CommandTests(TestCase):
    def setUp(self):
        self.site = Site.objects.get_current()

    def run_command(self, apply=False):
        out = StringIO()
        call_command('cleanup_legacy_phones', apply=apply, stdout=out)
        return out.getvalue()

    def user(self, phone, **kwargs):
        return ShopUser.objects.create(phone=phone, phone_verified=True, **kwargs)

    def order(self, user, status=Order.STATUS_NEW):
        order = Order.objects.create(user=user, site=self.site)
        Order.objects.filter(pk=order.pk).update(status=status)
        return order

    def exists(self, user):
        return ShopUser.objects.filter(pk=user.pk).exists()

    def test_dry_run_changes_nothing(self):
        mistyped = self.user('+789161234567')
        empty = self.user('+375291234567')
        out = self.run_command()
        self.assertIn('repair  +789161234567 (id %d): → +79161234567' % mistyped.id, out)
        self.assertIn('remove  +375291234567 (id %d): holds nothing' % empty.id, out)
        self.assertIn('Dry run, nothing changed: remove 1, repair 1', out)
        mistyped.refresh_from_db()
        self.assertEqual(mistyped.phone, '+789161234567')
        self.assertTrue(self.exists(empty))

    def test_valid_phones_are_left_alone(self):
        self.user('+79161234567')
        self.assertIn('no legacy phones', self.run_command(apply=True))

    def test_repair(self):
        user = self.user('+789161234567', email='me@example.com', email_verified=True)
        self.order(user)
        self.run_command(apply=True)
        user.refresh_from_db()
        self.assertEqual(user.phone, '+79161234567')
        self.assertFalse(user.phone_verified)  # proven by the first SMS login, which resets the email too
        self.assertTrue(user.email_verified)

    def test_repair_to_a_taken_number(self):
        self.user('+79161234567')
        with_orders = self.user('+779161234567')
        self.order(with_orders)
        empty = self.user('+789161234567')
        out = self.run_command(apply=True)
        self.assertIn('keep    +779161234567 (id %d): orders 1; +79161234567 is taken' % with_orders.id, out)
        self.assertTrue(self.exists(with_orders))
        self.assertFalse(self.exists(empty))

    def test_most_recent_login_gets_the_repaired_number(self):
        old = self.user('+789161234567', last_login=timezone.now() - timedelta(days=400))
        recent = self.user('+779161234567', last_login=timezone.now())
        self.order(old)
        self.run_command(apply=True)
        recent.refresh_from_db()
        old.refresh_from_db()
        self.assertEqual(recent.phone, '+79161234567')
        self.assertEqual(old.phone, '+789161234567')

    def test_real_phone_with_any_data_is_kept(self):
        users = [self.user('+3752912345%02d' % n) for n in range(3)]
        self.order(users[0], Order.STATUS_CANCELED)
        Token.objects.create(user=users[1])
        self.order(users[2])
        self.run_command(apply=True)
        for user in users:
            self.assertTrue(self.exists(user), user.phone)

    def test_unreal_phone_goes_with_its_canceled_orders(self):
        user = self.user('+7150')
        canceled = self.order(user, Order.STATUS_CANCELED)
        out = self.run_command(apply=True)
        self.assertIn('unreal phone, canceled orders 1', out)
        self.assertFalse(self.exists(user))
        self.assertFalse(Order.objects.filter(pk=canceled.pk).exists())

    def test_unreal_phone_with_a_real_order_is_kept(self):
        user = self.user('+7150')
        self.order(user, Order.STATUS_CANCELED)
        self.order(user, Order.STATUS_DONE)
        self.run_command(apply=True)
        self.assertEqual(Order.objects.filter(user=user).count(), 2)

    def test_blockers_keep_even_an_unreal_phone(self):
        serial = self.user('+7151')
        Serial.objects.create(number='SN-1', user=serial)
        bonus = self.user('+7152')
        Bonus.objects.create(user=bonus, value=100)
        editor = self.user('+7153')
        LogEntry.objects.create(user=editor, content_type=ContentType.objects.get_for_model(ShopUser),
                                object_id='1', object_repr='x', action_flag=ADDITION)
        owner = self.user('+7154')
        Order.objects.create(user=self.user('+79160000000'), site=self.site, owner=owner)
        out = self.run_command(apply=True)
        for user, kind in ((serial, 'shop.Serial 1'), (bonus, 'shop.Bonus 1'), (editor, 'admin.LogEntry 1'),
                           (owner, 'shop.Order.owner 1')):
            self.assertTrue(self.exists(user), kind)
            self.assertIn('(id %d): %s' % (user.id, kind), out)

    def test_technical_accounts_and_staff_are_skipped(self):
        technical = [self.user(phone) for phone in ('000', '0001', '00002')]  # looked up by phone in code
        staff = self.user('+7150', is_staff=True)
        out = self.run_command(apply=True)
        for user in technical:
            self.assertIn('skip    %s (id %d): technical account' % (user.phone, user.id), out)
            self.assertTrue(self.exists(user))
        self.assertIn('skip    +7150 (id %d): staff' % staff.id, out)
        self.assertTrue(self.exists(staff))

    def test_phones_typed_without_plus_are_repaired(self):
        users = [self.user(phone) for phone in ('89161234567', '7-916-765-43-21')]
        self.run_command(apply=True)
        self.assertEqual([ShopUser.objects.get(pk=user.pk).phone for user in users], ['+79161234567', '+79167654321'])

    def test_name_typed_as_phone(self):
        user = self.user('Татьяна')
        self.order(user, Order.STATUS_CANCELED)
        self.assertIn('unreal phone, canceled orders 1', self.run_command(apply=True))
        self.assertFalse(self.exists(user))
