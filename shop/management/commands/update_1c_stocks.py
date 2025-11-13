from django.core.management.base import BaseCommand

from shop.tasks import update_1c_stocks


class Command(BaseCommand):
    help = 'Update 1C stock'

    def handle(self, *args, **options):
        update_1c_stocks.delay()
        self.stdout.write('Initiated update')
