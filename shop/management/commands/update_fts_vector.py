from django.core.management.base import BaseCommand
from shop.models import Product


class Command(BaseCommand):
    help = 'Update product search vectors'

    def handle(self, *args, **options):
        num = 0
        for product in Product.objects.all():
            product.update_fts_vector()
            num = num + 1

        self.stdout.write('Successfully indexed %d products' % num)
