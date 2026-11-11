"""
Stock of products: Product.instock counts it when an import or an order has reset it (num < 0), and count_stocks()
counts it after the import, before storefronts ask. See settings.py on how to run.
"""
from django.contrib.sites.models import Site
from django.test import TestCase

from shop.models import Product, ProductSet, Stock, Supplier
from shop.tasks.stocks import count_stocks

from .fixtures import add_product


class StockTests(TestCase):
    def setUp(self):
        Site.objects.create(domain='www.sewing-world.ru', name='Швейный Мир')  # get_stock() counts its orders
        self.counted, self.on_request = Supplier.objects.bulk_create([
            Supplier(code='s1', code1c='s1', name='Склад', order=1, count_in_stock=Supplier.COUNT_STOCK),
            Supplier(code='s2', code1c='s2', name='Под заказ', order=2, count_in_stock=Supplier.COUNT_DEFER),
        ])
        self.machine = add_product(1, num=-1)

    def stock(self, product, supplier, quantity, correction=0):
        Stock.objects.create(product=product, supplier=supplier, quantity=quantity, correction=correction)

    def test_stock_of_the_suppliers_that_count(self):
        self.stock(self.machine, self.counted, 3, correction=-1)
        self.stock(self.machine, self.on_request, 10)
        self.assertEqual(Product.objects.get(pk=1).instock, 2)
        self.assertEqual(Product.objects.get(pk=1).num, 2)

    def test_no_stock(self):
        self.stock(self.machine, self.on_request, 10)
        self.assertEqual(Product.objects.get(pk=1).instock, 0)

    def test_set_counts_whole_sets(self):
        table, bundle = add_product(2, num=-1), add_product(3, num=-1)
        ProductSet.objects.create(declaration=bundle, constituent=self.machine)
        ProductSet.objects.create(declaration=bundle, constituent=table, quantity=2)
        self.stock(self.machine, self.counted, 3)
        self.stock(table, self.counted, 5)
        self.assertEqual(Product.objects.get(pk=3).instock, 2)

    def test_counting_saves_only_the_stock(self):
        stale = Product.objects.get(pk=1)
        Product.objects.filter(pk=1).update(price=1200, title='Новое название')  # as an import or an editor would
        self.stock(self.machine, self.counted, 4)
        self.assertEqual(stale.instock, 4)
        product = Product.objects.get(pk=1)
        self.assertEqual((product.num, product.price, product.title), (4, 1200, 'Новое название'))

    def test_count_stocks_after_the_import(self):
        self.stock(self.machine, self.counted, 4)
        add_product(2, num=7)
        add_product(3, num=-1)
        count_stocks()
        self.assertEqual(dict(Product.objects.values_list('pk', 'num')), {1: 4, 2: 7, 3: 0})
