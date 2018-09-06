from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from shop.models import Product, ProductRelation, Manufacturer, Supplier, Country, Currency, Category

import pprint


class Command(BaseCommand):
    help = 'Imports products from basset'

    def handle(self, *args, **options):
        cursor = connection.cursor()
        # get discount values
        cursor.execute('SELECT id, value FROM discounts')
        rows = cursor.fetchall()
        discounts = dict()
        discounts[0] = 0
        for k,v in rows:
            discounts[k] = v
        # get manufacturer short names
        cursor.execute('SELECT id, code FROM manufacturers')
        rows = cursor.fetchall()
        manufacturers = dict()
        manufacturers[0] = 'undefined'
        for k,v in rows:
            manufacturers[k] = v
        # cache dictionaries
        shop_manufacturers = Manufacturer.objects.all()
        bool(shop_manufacturers)
        currencies = Currency.objects.all()
        bool(currencies)
        # get products
        cursor.execute('SELECT * FROM products')
        num = 0
        missing_cats = set()
        for row in cursor.fetchall():
            columns = (x[0] for x in cursor.description)
            row = dict(zip(columns, row))
            product, created = Product.objects.get_or_create(pk=row['id'])
            if created:
                product.gtin = ''
            product.title = row['name']
            product.save()
            categories = list(product.categories.all())
            ccursor = connection.cursor()
            ccursor.execute("select cid from sj_cats where sid = %s and tab = 'products'", [row['id']])
            for crow in ccursor.fetchall():
                try:
                    category = Category.objects.get(basset_id=crow[0])
                    if category in categories:
                        categories.remove(category)
                    else:
                        product.categories.add(category)
                except Category.DoesNotExist:
                    if crow[0] not in missing_cats:
                        self.stdout.write("Django does not contain category with basset id %d" % crow[0])
                        missing_cats.add(crow[0])
            for category in categories:
                if category.basset_id:
                    product.categories.remove(category)
            ccursor.close()
            num = num + 1
        self.stdout.write('Successfully imported %d product(s)' % num)

        cursor.close()
