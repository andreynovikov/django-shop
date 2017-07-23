from django.core.management.base import BaseCommand, CommandError
from django.db import connection

class Command(BaseCommand):
    help = 'Updates discounts of basset users based on their old orders'

    def handle(self, *args, **options):
        ucursor = connection.cursor()
        cursor = connection.cursor()
        cursor.execute('SELECT id, phone, phoneaux FROM users WHERE phone IS NOT NULL OR phoneaux IS NOT NULL')
        num = 0
        for row in cursor.fetchall():
            columns = (x[0] for x in cursor.description)
            row = dict(zip(columns, row))
            phone = self.normalize_phone(row['phone'])
            phoneaux = self.normalize_phone(row['phoneaux'])
            if phone and phoneaux:
                self.stdout.write('Guess: %s or %s' % (phone, phoneaux))
                phone = self.guess_better(phone, phoneaux)
                phoneaux = None
            if phoneaux:
                phone = phoneaux
            if phone:
                self.stdout.write('Save: %s' % phone)
                ucursor.execute('UPDATE users SET phone = %s WHERE id = %s', (phone, row['id']))
            num = num + 1
        cursor.close()
        ucursor.close()
        self.stdout.write('Successfully normalized %d user(s)' % num)

    def guess_better(self, phone_a, phone_b):
        if phone_a.startswith('+79') and len(phone_a) == 12:
            return phone_a
        if phone_b.startswith('+79') and len(phone_b) == 12:
            return phone_b
        if not phone_b.startswith('+7'):
            return phone_a
        if not phone_a.startswith('+7'):
            return phone_b
        if len(phone_b) > 12:
            return phone_a
        if len(phone_a) > 12:
            return phone_b

    def normalize_phone(self, phone):
        if phone is None:
            return None
        orig = phone
        if areacode_re.search(phone):
            return None
        phone = aux_re.sub('', phone)
        phone = phone_re.sub('', phone)
        if not phone:
            return None
        if phone.startswith('00'):
            phone = '+' + phone[2:]
        if phone.startswith('8'):
            phone = phone[1:]
        if not phone.startswith('+'):
            phone = '+7' + phone
        if len(phone) < 12:
            return None
        return phone

