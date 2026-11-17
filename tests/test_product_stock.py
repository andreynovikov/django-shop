"""
Stock of products: Product.get_stocks() counts it, Product.instock counts it when an import or an order has reset it
(num < 0), and count_stocks() counts it after the import, before storefronts ask. See settings.py on how to run.
"""
from django.contrib.sites.models import Site
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext

from shop.models import Integration, Order, OrderItem, Product, ProductSet, ShopUser, Stock, Supplier
from shop.tasks.stocks import count_stocks

from .fixtures import add_product


class StockTests(TestCase):
    def setUp(self):
        self.counted, self.on_request = Supplier.objects.bulk_create([
            Supplier(code='s1', code1c='s1', name='Склад', order=1, count_in_stock=Supplier.COUNT_STOCK),
            Supplier(code='s2', code1c='s2', name='Под заказ', order=2, count_in_stock=Supplier.COUNT_DEFER),
        ])
        self.machine = add_product(1, num=-1)

    def stock(self, product, supplier, quantity, correction=0):
        Stock.objects.create(product=product, supplier=supplier, quantity=quantity, correction=correction)

    def integration(self, domain, *suppliers):
        """ An integration that sells from these suppliers on a site of its own """
        site = Site.objects.create(domain=domain, name=domain)
        integration = Integration.objects.create(name=domain, utm_source=domain, site=site, output_template='market')
        integration.suppliers.set(suppliers)
        return integration

    def order(self, site, *items, status=Order.STATUS_ACCEPTED):
        """ An order on the site with (product, quantity) items, made without save() and its signals """
        user, _ = ShopUser.objects.get_or_create(phone='+79160000001')
        [order] = Order.objects.bulk_create([Order(user=user, site=site, status=status)])
        OrderItem.objects.bulk_create(OrderItem(order=order, product=product, quantity=quantity) for product, quantity in items)

    def test_stock_of_the_suppliers_that_count(self):
        self.stock(self.machine, self.counted, 3, correction=-1)
        self.stock(self.machine, self.on_request, 10)
        self.assertEqual(Product.objects.get(pk=1).instock, 2)
        self.assertEqual(Product.objects.get(pk=1).num, 2)

    def test_no_stock(self):
        self.stock(self.machine, self.on_request, 10)
        self.assertEqual(Product.objects.get(pk=1).instock, 0)

    def test_corrections_take_the_stock_down_to_none(self):
        self.stock(self.machine, self.counted, 1, correction=-3)
        self.assertEqual(Product.objects.get(pk=1).instock, 0)
        self.assertEqual(Product.objects.get(pk=1).num, 0)  # counted, not reset again

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

    def test_orders_in_progress_hold_stock(self):
        self.stock(self.machine, self.counted, 5)
        main = Site.objects.get_current()
        self.order(main, (self.machine, 1))
        self.order(main, (self.machine, 2), status=Order.STATUS_DONE)
        self.assertEqual(self.machine.get_stock(), 4)

    def test_orders_hold_stock_on_the_sites_that_sell_from_its_suppliers(self):
        self.stock(self.machine, self.counted, 10)
        shop = Site.objects.create(domain='shop.ru', name='Магазин')  # without integrations, sells what counts in stock
        marketplace = self.integration('ozon.ru', self.counted)
        other = self.integration('wildberries.ru', self.on_request)
        self.order(Site.objects.get_current(), (self.machine, 1))
        self.order(shop, (self.machine, 2))
        self.order(marketplace.site, (self.machine, 3))
        self.order(other.site, (self.machine, 4))  # sells from another supplier
        self.assertEqual(self.machine.get_stock(), 4)
        self.assertEqual(self.machine.get_stock(integration=marketplace), 4)

    def test_integration_counts_its_own_suppliers(self):
        self.stock(self.machine, self.counted, 3)
        self.stock(self.machine, self.on_request, 10)
        marketplace = self.integration('ozon.ru', self.on_request)
        self.assertEqual(self.machine.get_stock(integration=marketplace), 10)
        self.assertEqual(self.machine.get_stock(), 3)

    def test_express_counts_the_suppliers_of_express_delivery(self):
        express = Supplier.objects.create(code='s3', code1c='s3', name='Экспресс', order=3, count_in_stock=Supplier.COUNT_STOCK,
                                          express_count_in_stock=Supplier.COUNT_STOCK)
        self.stock(self.machine, self.counted, 3)
        self.stock(self.machine, express, 2)
        self.assertEqual(self.machine.get_stock(express=True), 2)
        self.assertEqual(self.machine.get_stock(), 5)

    def test_set_counts_its_parts_at_the_integrations_suppliers(self):
        table, bundle = add_product(2), add_product(3)
        ProductSet.objects.create(declaration=bundle, constituent=self.machine)
        ProductSet.objects.create(declaration=bundle, constituent=table, quantity=2)
        self.stock(self.machine, self.counted, 3)
        self.stock(table, self.counted, 4)
        self.stock(table, self.on_request, 10)
        marketplace = self.integration('ozon.ru', self.on_request)  # has tables, but no machines
        self.assertEqual(bundle.get_stock(), 2)
        self.assertEqual(bundle.get_stock(integration=marketplace), 0)
        marketplace.suppliers.add(self.counted)
        self.assertEqual(bundle.get_stock(integration=marketplace), 3)

    def test_more_products_take_no_more_queries(self):
        products = [self.machine, *(add_product(pk) for pk in range(2, 7))]
        bundles = [add_product(pk) for pk in (7, 8)]
        for product in products:
            self.stock(product, self.counted, 5)
            self.order(Site.objects.get_current(), (product, 1))
        for bundle, part in zip(bundles, products):
            ProductSet.objects.create(declaration=bundle, constituent=part)

        def queries(*products):
            with CaptureQueriesContext(connection) as context:
                stocks = Product.get_stocks(product.pk for product in products)
            self.assertEqual(set(stocks.values()), {4})
            return len(context.captured_queries)

        self.assertEqual(queries(*products, *bundles), queries(products[0], bundles[0]))
