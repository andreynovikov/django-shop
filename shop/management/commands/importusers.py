import re

from django.core.management.base import BaseCommand, CommandError
from django.db import connection

from shop.models import ShopUser

class Command(BaseCommand):
    help = 'Imports basset users to django'

    def handle(self, *args, **options):
        cursor = connection.cursor()
        cursor.execute('SELECT phone, passwd, fio, email, cities.name AS city, ' +
                       'paddress, zipcode, discount FROM users INNER JOIN cities ' +
                       'ON (city = cities.id) WHERE phone LIKE \'+%\'')
        num = 0
        for row in cursor.fetchall():
            columns = (x[0] for x in cursor.description)
            row = dict(zip(columns, row))
            phone = row['phone']
            if phone.startswith('+77'):
                phone = '+7' + phone[3:]
            user, created = ShopUser.objects.get_or_create(phone=phone)
            if not created:
                continue
            user.set_password(row['passwd'])
            user.name = row['fio']
            user.email = row['email']
            if row['city']:
                user.city = row['city']
            if row['paddress']:
                user.address = row['paddress']
            if row['zipcode'] and row['zipcode'] != '000000':
                user.postcode = row['zipcode']
            if row['discount']:
                user.discount = int(row['discount'])
            self.stdout.write('Import: %s' % phone)
            user.save()
            num = num + 1
        cursor.close()
        self.stdout.write('Successfully imported %d user(s)' % num)
