"""
Account endpoints the other test modules leave out: the user list, bonuses and the profile form.
See settings.py on how to run.
"""
from django.test import TestCase
from django.utils import timezone

from shop.models import Bonus, ShopUser

from .clients import StorefrontClient, add_storefront_key, signed_in

PHONE = '+79161234567'


class Base(TestCase):
    def setUp(self):
        add_storefront_key()
        self.user = ShopUser.objects.create(phone=PHONE)
        self.client = signed_in(self.user)
        self.superuser = signed_in(ShopUser.objects.create(phone='+79160000001', name='Админ', is_superuser=True))


class ListTests(Base):
    def test_superuser_lists_users_without_their_phones(self):
        response = self.superuser.get('/api/v0/users/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['count'], 2)
        self.assertEqual(sorted(user['full_name'] for user in data['results']), ['+7 (916) 1**-**-67', 'Админ'])
        self.assertNotIn(PHONE, response.content.decode())

    def test_others_cannot(self):
        for client in (self.client, StorefrontClient()):
            self.assertEqual(client.get('/api/v0/users/').status_code, 403)

    def test_users_are_not_deleted(self):
        self.assertEqual(self.client.delete(f'/api/v0/users/{self.user.id}/').status_code, 403)
        self.assertEqual(self.superuser.delete(f'/api/v0/users/{self.user.id}/').status_code, 405)
        self.assertTrue(ShopUser.objects.filter(pk=self.user.pk).exists())


class BonusTests(Base):
    def bonus(self, client=None):
        return (client or self.client).get('/api/v0/users/bonus/')

    def test_unknown_balance(self):
        self.assertEqual(self.bonus().json(), {'value': 0, 'is_fresh': False, 'is_undefined': True, 'is_updating': False})

    def test_fresh_balance(self):
        Bonus.objects.create(user=self.user, value=150, status=Bonus.STATUS_OK, updated=timezone.now())
        self.assertEqual(self.bonus().json(), {'value': 150, 'is_fresh': True, 'is_undefined': False, 'is_updating': False})

    def test_anonymous(self):
        self.assertEqual(self.bonus(StorefrontClient()).status_code, 403)


class FormTests(Base):
    def test_profile_fields(self):
        fields = StorefrontClient().get('/api/v0/users/form/').json()
        self.assertEqual([(field['name'], field['required']) for field in fields],
                         [('name', False), ('phone', True), ('email', False), ('address', False), ('username', False)])
