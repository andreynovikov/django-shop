from django.core.management.base import BaseCommand, CommandError
from shop.models import Product

class Command(BaseCommand):
    help = 'Imports gtin numbers'

    def add_arguments(self, parser):
        parser.add_argument('file', nargs=1, type=str)

    def handle(self, *args, **options):
        file = options['file'][0]
        self.stdout.write(file)
        num = 0
        with open(file, 'rU') as f:
            for line in f:
                article, gtin = line.split('\t')
                gtin_num = int(gtin)
                self.stdout.write(gtin)
                try:
                    product = Product.objects.get(article=article)
                except Product.DoesNotExist:
                    continue
                self.stdout.write(str(product))
                if not product.gtin or int(product.gtin) < gtin_num:
                    product.gtin = gtin
                product.save()
                num = num + 1
        self.stdout.write('Successfully updated %d products' % num)
