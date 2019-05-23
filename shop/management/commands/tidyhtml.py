from hashlib import md5
from tidylib import tidy_fragment

from django.core.management.base import BaseCommand, CommandError
from shop.models import Product


class Command(BaseCommand):
    help = 'Clean HTML in product description fields'

    def handle(self, *args, **options):
        num = 0
        for product in Product.objects.all():
            changed = False
            for field in ['shortdescr', 'yandexdescr', 'descr', 'spec', 'state', 'complect', 'stitches', 'sm_display', 'sm_software']:
                value = product.__dict__[field]
                if not value:
                    continue
                fragment, errors = tidy_fragment(value, options={'indent':0})
                if not fragment:
                    self.stdout.write('{}: {}'.format(str(product), field))
                    continue
                if md5(value.encode('utf-8')).hexdigest() != md5(fragment.encode('utf-8')).hexdigest():
                    product.__dict__[field] = fragment
                    changed = True
            if changed:
                product.save()
                num = num + 1

        self.stdout.write('Successfully updated %d products' % num)
