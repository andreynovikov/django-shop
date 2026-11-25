"""
Revalidation of the storefronts' pages, see shop/revalidation.py: a change becomes the tags of the data it touches,
sent once the transaction commits, a batch per site. See settings.py on how to run.
"""
import logging

from decimal import Decimal
from unittest import mock

import requests

from django.contrib.admin.sites import site as admin_site
from django.contrib.flatpages.models import FlatPage
from django.contrib.sites.models import Site
from django.db import transaction
from django.test import RequestFactory, TestCase

from sewingworld.models import SiteProfile
from shop.models import Category, Currency, News, Product, ProductRelation, ProductSet, SalesAction, Stock, Supplier
from shop.tasks.stocks import count_stocks
from shop.tasks.workflow import StorefrontUnavailable, revalidate_nextjs

from .fixtures import add_marketplace_sites, add_product


class Rollback(Exception):
    pass


class RevalidationTestCase(TestCase):
    def setUp(self):
        self.main = Site.objects.get_current()
        self.other = Site.objects.create(domain='other.test', name='Другой')
        self.untokened = Site.objects.create(domain='untokened.test', name='Без токена')
        self.main_root = Category.objects.create(name='Каталог', slug='main')
        self.other_root = Category.objects.create(name='Каталог', slug='other')
        SiteProfile.objects.create(site=self.main, revalidation_token='main-token', root_category=self.main_root)
        SiteProfile.objects.create(site=self.other, revalidation_token='other-token', root_category=self.other_root)
        SiteProfile.objects.create(site=self.untokened)
        patcher = mock.patch('shop.tasks.workflow.revalidate_nextjs')
        self.task = patcher.start()
        self.addCleanup(patcher.stop)

    def commit(self, change=lambda: None):
        """
        Commits what the test did so far, then runs the change and commits it as a transaction would; returns what
        the change sent. TestCase never commits, and captureOnCommitCallbacks() leaves callbacks added before it.
        """
        self.run_commit_hooks()
        self.task.reset_mock()
        change()
        self.task.s.assert_not_called()  # nothing before the commit
        self.run_commit_hooks()
        return self.sent()

    @staticmethod
    def run_commit_hooks():
        """ As the connection does after a commit: the failure of a robust hook is logged, of another one raised """
        connection = transaction.get_connection()
        while connection.run_on_commit:
            hooks, connection.run_on_commit = connection.run_on_commit, []
            for _, hook, robust in hooks:
                try:
                    hook()
                except Exception as error:
                    if not robust:
                        raise
                    logging.getLogger('django.db.backends.base').exception('Error calling %s in on_commit() (%s).', hook.__qualname__, error)

    def sent(self):
        """ {(domain, background): tags} of the requests that the commit queued """
        tokens = {self.main.domain: 'main-token', self.other.domain: 'other-token'}
        requests = {}
        for call in self.task.s.call_args_list:
            domain, token, payload = call.args
            self.assertEqual(token, tokens[domain])
            requests.setdefault((domain, payload.get('background', False)), set()).update(payload['tags'])
        return requests


class ContentTests(RevalidationTestCase):
    def test_new_news_revalidates_the_sites_saved_after_it(self):
        def change():
            news = News.objects.create(title='Новость', content='Текст', active=True)
            news.sites.set([self.main, self.untokened])  # as save_related() saves them
        self.assertEqual(self.commit(change), {(self.main.domain, False): {'news'}})

    def test_news_moved_to_another_site_revalidates_both(self):
        news = News.objects.create(title='Новость', content='Текст', active=True)
        news.sites.set([self.main])
        self.commit()

        def change():
            news.title = 'Новость о другом'
            news.save()
            news.sites.set([self.other])
        self.assertEqual(self.commit(change), {(self.main.domain, False): {'news'}, (self.other.domain, False): {'news'}})

    def test_page_moved_to_another_url_revalidates_both(self):
        page = FlatPage.objects.create(url='/about/', title='О нас', content='Текст')
        page.sites.set([self.main])
        self.commit()

        def change():
            page.url = '/company/'
            page.save()
        self.assertEqual(self.commit(change), {(self.main.domain, False): {'pages', 'page:/about/', 'page:/company/'}})

    def test_rolled_back_change_is_not_sent_and_the_next_one_is(self):
        news = News.objects.create(title='Новость', content='Текст', active=True)
        news.sites.set([self.main])
        self.commit()

        def change():
            with self.assertRaises(Rollback), transaction.atomic():
                news.save()
                raise Rollback
        self.assertEqual(self.commit(change), {})
        self.assertEqual(self.commit(news.save), {(self.main.domain, False): {'news'}})

    def test_changes_of_a_transaction_go_in_one_request_per_site(self):
        news = News.objects.create(title='Новость', content='Текст', active=True)
        news.sites.set([self.main])
        page = FlatPage.objects.create(url='/about/', title='О нас', content='Текст')
        page.sites.set([self.main])
        self.commit()

        def change():
            news.save()
            page.save()
            news.save()
        self.commit(change)
        self.task.s.assert_called_once_with(self.main.domain, 'main-token', {'tags': ['news', 'page:/about/', 'pages']})

    def test_many_tags_are_split(self):
        from shop.revalidation import revalidate
        self.commit(lambda: revalidate({f'product:{n}' for n in range(1200)}, [self.main]))
        self.assertEqual([len(call.args[2]['tags']) for call in self.task.s.call_args_list], [500, 500, 200])


class CategoryTests(RevalidationTestCase):
    def setUp(self):
        super().setUp()
        self.sewing = Category.objects.create(name='Шитьё', slug='sewing', parent=self.main_root)
        self.machines = Category.objects.create(name='Машины', slug='machines', parent=self.sewing)
        self.commit()

    def test_description_revalidates_the_category_on_its_site(self):
        def change():
            self.machines.description = 'Статья'
            self.machines.save()
        self.assertEqual(self.commit(change), {
            (self.main.domain, False): {f'category:{self.machines.pk}', 'category-path:sewing/machines'},
        })

    def test_new_name_revalidates_the_menu_of_every_page(self):
        def change():
            self.machines.name = 'Швейные машины'
            self.machines.save()
        self.assertEqual(self.commit(change), {
            (self.main.domain, False): {f'category:{self.machines.pk}', 'category-path:sewing/machines', 'catalog'},
        })

    def test_product_taken_out_of_a_category_revalidates_its_lists(self):
        product = add_product(1, sites=[self.main], categories=[self.machines])
        self.commit()
        self.assertEqual(self.commit(lambda: product.categories.set([])), {(self.main.domain, False): {
            'product:p1', f'category:{self.machines.pk}',
            f'category-tree:{self.machines.pk}', f'category-tree:{self.sewing.pk}', f'category-tree:{self.main_root.pk}',
        }})


class ProductTests(RevalidationTestCase):
    def setUp(self):
        super().setUp()
        add_marketplace_sites()  # integrations look them up when a product is saved
        self.machines = Category.objects.create(name='Машины', slug='machines', parent=self.main_root)
        self.product = add_product(1, sites=[self.main, self.other], categories=[self.machines], firstpage=True)
        self.action = SalesAction.objects.create(name='Скидки', slug='discounts', active=True, notice='Скидка', order=1)
        self.action.sites.set([self.main])
        self.product.sales_actions.set([self.action])
        self.commit()
        self.lists = {f'category:{self.machines.pk}', f'category-tree:{self.machines.pk}', f'category-tree:{self.main_root.pk}'}

    def save_in_admin(self, **fields):
        for name, value in fields.items():
            setattr(self.product, name, value)
        admin_site._registry[Product].save_model(RequestFactory().post('/'), self.product, form=None, change=True)

    def test_admin_save_revalidates_the_pages_with_the_product_at_once(self):
        tags = {'product:p1', 'firstpage', 'action:discounts'} | self.lists
        self.assertEqual(self.commit(self.save_in_admin), {(self.main.domain, False): tags, (self.other.domain, False): tags})

    def test_new_code_and_removal_from_home_revalidate_where_it_was(self):
        sent = self.commit(lambda: self.save_in_admin(code='p1-new', firstpage=False))
        self.assertEqual(sent[(self.main.domain, False)], {'product:p1', 'product:p1-new', 'firstpage', 'action:discounts'} | self.lists)

    def test_site_the_product_leaves_revalidates_its_pages(self):
        sent = self.commit(lambda: self.product.sites.set([self.main]))
        self.assertIn('product:p1', sent[(self.other.domain, False)])

    def test_new_notice_of_an_action_revalidates_its_products(self):
        def change():
            self.action.notice = 'Распродажа'
            self.action.save()
        sent = self.commit(change)
        self.assertEqual(sent[(self.main.domain, False)], {'actions', 'product:p1', 'firstpage', 'action:discounts'} | self.lists)
        self.assertEqual(sent[(self.other.domain, False)], {'product:p1', 'firstpage', 'action:discounts'} | self.lists)

    def test_new_description_of_an_action_revalidates_the_action_only(self):
        def change():
            self.action.description = 'Статья'
            self.action.save()
        self.assertEqual(self.commit(change), {(self.main.domain, False): {'actions', 'action:discounts'}})

    def test_products_that_show_the_product_are_revalidated(self):
        machine = add_product(2, sites=[self.main])
        kit = add_product(3, sites=[self.main])
        ProductRelation.objects.create(parent_product=machine, child_product=self.product, kind=ProductRelation.KIND_ACCESSORY)
        ProductSet.objects.create(declaration=kit, constituent=self.product)
        self.commit()
        sent = self.commit(self.save_in_admin)[(self.main.domain, False)]
        self.assertIn('product:p2', sent)  # its page shows the accessory
        self.assertIn('product:p3', sent)  # the set costs what its parts do

    def test_new_rate_revalidates_the_products_in_the_currency(self):
        currency = Currency.objects.get(code=643)  # the product's, see add_products()
        currency.rate = Decimal('1.00')
        currency.save()

        def change(rate):
            def save():
                currency.rate = rate  # as update_cbrf_currencies() sets it
                currency.save()
            return save
        self.assertEqual(self.commit(change(1.0)), {})
        self.assertIn('product:p1', self.commit(change(1.5))[(self.main.domain, False)])

    def test_manufacturer_revalidates_the_pages_of_its_products(self):
        manufacturer = self.product.manufacturer
        self.assertEqual(self.commit(manufacturer.save), {(self.main.domain, False): {'product:p1'}, (self.other.domain, False): {'product:p1'}})

    def test_broker_down_fails_no_save(self):
        """ The batch is sent once the save has committed: a failure is logged, the admin's answer stays a success """
        self.task.s.return_value.apply_async.side_effect = OSError('broker down')
        with self.assertLogs('django.db.backends.base', 'ERROR'):
            self.commit(self.save_in_admin)


class StockTests(RevalidationTestCase):
    def setUp(self):
        super().setUp()
        add_marketplace_sites()
        self.supplier = Supplier.objects.create(code='s1', code1c='s1', name='Склад', order=1, count_in_stock=Supplier.COUNT_STOCK)
        self.plenty = add_product(1, sites=[self.main], num=-1)
        self.last = add_product(2, sites=[self.main], num=-1)
        Stock.objects.create(product=self.plenty, supplier=self.supplier, quantity=8)
        Stock.objects.create(product=self.last, supplier=self.supplier, quantity=1)
        self.commit()

    def test_import_revalidates_in_the_background_the_products_whose_stock_shows_otherwise(self):
        # before the import: 9 and 2 in stock, now 8 and 1. 9 and 8 both show as more than five, 1 shows as the last one.
        self.assertEqual(self.commit(lambda: count_stocks([[1, 9], [2, 2]])), {(self.main.domain, True): {'product:p2'}})
        self.assertEqual(Product.objects.get(pk=1).num, 8)

    def test_stock_not_counted_before_is_revalidated(self):
        self.assertEqual(self.commit(lambda: count_stocks([[2, -1]])), {(self.main.domain, True): {'product:p2'}})


class TaskTests(TestCase):
    def post(self, status, body=None):
        response = mock.Mock(status_code=status, ok=status < 400, text='')
        response.json.return_value = body
        return mock.patch('shop.tasks.workflow.requests.post', return_value=response)

    def test_storefront_gets_the_tags(self):
        with self.post(200, {'revalidated': True}) as post:
            self.assertEqual(revalidate_nextjs.run('shop.test', 'token', {'tags': ['news']}), {'revalidated': True})
        post.assert_called_once_with('https://shop.test/api/revalidate', json={'secret': 'token', 'tags': ['news']}, timeout=30)

    def test_failing_storefront_is_tried_again(self):
        with self.post(502), self.assertRaises(StorefrontUnavailable):
            revalidate_nextjs.run('shop.test', 'token', {'tags': ['news']})
        self.assertIn(StorefrontUnavailable, revalidate_nextjs.autoretry_for)
        self.assertIn(requests.RequestException, revalidate_nextjs.autoretry_for)

    def test_refused_request_is_not_tried_again(self):
        with self.post(401, {'revalidated': False}), self.assertLogs('shop', 'ERROR'):
            self.assertEqual(revalidate_nextjs.run('shop.test', 'token', {'tags': ['news']}), {'revalidated': False})
