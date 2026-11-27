"""
Account endpoints the other test modules leave out: the user list and other accounts read with the api_read_users
permission, bonuses and the profile form.
See settings.py on how to run.
"""
from django.test import TestCase
from django.utils import timezone

from shop.models import Bonus, ShopUser

from .clients import StorefrontClient, add_storefront_key, api_reader, signed_in, token_client

PHONE = '+79161234567'


class Base(TestCase):
    def setUp(self):
        add_storefront_key()
        self.user = ShopUser.objects.create(phone=PHONE)
        self.client = signed_in(self.user)
        self.superuser = signed_in(ShopUser.objects.create(phone='+79160000001', name='Админ', is_superuser=True))


class ListTests(Base):
    def test_reader_lists_whole_accounts(self):
        self.user.set_password('secret-password')
        self.user.save()
        reader, client = api_reader('api_read_users')
        response = client.get('/api/v0/users/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['count'], 3)
        self.assertEqual([user['phone'] for user in data['results']], [PHONE, '+79160000001', reader.phone])
        # first_name and last_name are aliases of name
        self.assertEqual(set(data['results'][0]),
                         {field.name for field in ShopUser._meta.concrete_fields} - {'password', 'first_name', 'last_name'})
        self.assertNotIn(self.user.password, response.content.decode())  # the hash

    def test_reader_through_a_group(self):
        _, client = api_reader('api_read_users', through_group=True)
        self.assertEqual(client.get('/api/v0/users/').json()['count'], 3)

    def test_others_cannot(self):
        _, orders_reader = api_reader('api_read_orders')
        self.assertEqual(orders_reader.get('/api/v0/users/').status_code, 403)
        self.assertEqual(orders_reader.get(f'/api/v0/users/{self.user.id}/').status_code, 403)
        # the superuser too: the permission has to be given, it is not implied
        for client in (self.client, self.superuser, StorefrontClient(), token_client(ShopUser.objects.get(is_superuser=True))):
            self.assertEqual(client.get('/api/v0/users/').status_code, 403)

    def test_users_are_not_deleted(self):
        _, reader = api_reader('api_read_users')
        for client in (self.client, self.superuser, reader):
            self.assertEqual(client.delete(f'/api/v0/users/{self.user.id}/').status_code, 403)
        self.assertTrue(ShopUser.objects.filter(pk=self.user.pk).exists())


class AnotherAccountTests(Base):
    def url(self, key=None):
        return f'/api/v0/users/{key or self.user.id}/'

    def test_reader_reads_any_account_whole(self):
        _, client = api_reader('api_read_users')
        for key in (self.user.id, PHONE):
            data = client.get(self.url(key)).json()
            self.assertEqual((data['id'], data['phone'], data['is_active']), (self.user.id, PHONE, True))
            self.assertNotIn('password', data)

    def test_reader_reads_itself_as_a_customer_does(self):
        reader, client = api_reader('api_read_users')
        data = client.get('/api/v0/users/current/').json()
        self.assertEqual((data['id'], data['full_name']), (reader.id, 'Аналитика'))
        self.assertNotIn('is_active', data)

    def test_reader_changes_nothing(self):
        _, client = api_reader('api_read_users')
        self.assertEqual(client.patch(self.url(), {'name': 'Чужое'}, format='json').status_code, 403)
        self.assertEqual(client.post(self.url() + 'email-link/').status_code, 403)
        self.user.refresh_from_db()
        self.assertEqual(self.user.name, '')

    def test_superuser_neither_reads_nor_changes(self):
        self.assertEqual(self.superuser.get(self.url()).status_code, 403)
        self.assertEqual(self.superuser.patch(self.url(), {'name': 'Чужое'}, format='json').status_code, 403)
        self.user.refresh_from_db()
        self.assertEqual(self.user.name, '')

    def test_inactive_reader(self):
        reader, client = api_reader('api_read_users')
        reader.is_active = False
        reader.save()
        self.assertEqual(client.get(self.url()).status_code, 403)


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
