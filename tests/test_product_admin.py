"""
Saving a product in the admin, beyond what Django does. See settings.py on how to run.
"""
from unittest import mock

from django.contrib.admin.sites import site as admin_site
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.backends.db import SessionStore
from django.contrib.sites.models import Site
from django.test import RequestFactory, TestCase, override_settings
from django.urls import path

from shop.models import Category, Currency, Integration, Product, ProductSet, ShopUser, Stock, Supplier
from shop.tasks.workflow import post_update_product

from .clients import count_queries
from .fixtures import add_marketplace_sites, add_product

# The admin is served by a process of its own (ADMIN=True), its views and templates need its URLs
urlpatterns = [path('admin/', admin_site.urls)]


class ProductSaveTests(TestCase):
    def test_update_task_is_queued_after_commit(self):
        """
        The task reads the sites that save_related() sets after save_model(). Queued inside the admin's transaction,
        the worker could read the old ones, and its insert of the task's row waited for that transaction.
        """
        add_marketplace_sites()  # integrations look them up when a product is saved
        product = add_product(1)
        with mock.patch.object(post_update_product, 'delay') as delay:
            with self.captureOnCommitCallbacks(execute=True):
                admin_site._registry[Product].save_model(RequestFactory().post('/'), product, form=None, change=True)
                delay.assert_not_called()
            delay.assert_called_once_with(1, 'admin')


@override_settings(ROOT_URLCONF=__name__)
class ProductListTests(TestCase):
    """ The list of products, with a form in each row for its checkboxes """

    def setUp(self):
        site = Site.objects.get_current()
        self.suppliers = [Supplier.objects.create(code='С%d' % i, code1c='s%d' % i, name='Склад %d' % i, order=i,
                                                  show_in_order=i < 3) for i in range(1, 4)]
        self.integrations = [Integration.objects.create(name='Канал %d' % i, utm_source='u%d' % i, source_site=site,
                                                        target_site=site, enabled=True) for i in range(2)]
        Currency.objects.get_or_create(code=840, defaults={'name': 'USD'})
        self.catalog = Category.objects.create(name='Каталог', slug='catalog')
        self.staff = ShopUser.objects.create(phone='+79990000000', is_staff=True, is_superuser=True)

    def add_products(self, first, count):
        # the filter of categories shows their paths, which tell those of the same name apart
        machines = Category.objects.create(name='Машины', slug='machines-%d' % first, parent=self.catalog)
        Category.objects.create(name='Машины', slug='used-%d' % first, parent=machines)
        for pk in range(first, first + count):
            product = add_product(pk, cur_code_id=840 if pk % 2 else 643)
            for supplier in self.suppliers:
                Stock.objects.create(product=product, supplier=supplier, quantity=pk % 3, correction=pk % 2,
                                     reason='<b>сверка</b>')
            product.integrations.add(self.integrations[pk % 2], through_defaults={'price': 0})
        # a set, whose stock its constituents make
        ProductSet.objects.create(declaration=add_product(first + count), constituent=product)

    def changelist(self):
        request = RequestFactory().get('/')
        request.user = self.staff
        request.user.is_verified = lambda: True  # passed the second factor, as OTPMiddleware tells the admin site
        request.session = SessionStore()
        request._messages = FallbackStorage(request)
        return admin_site._registry[Product].changelist_view(request).render()

    def test_queries_do_not_grow_with_the_products(self):
        self.add_products(1, 2)
        few = count_queries(self.changelist)
        self.add_products(10, 6)
        self.assertContains(self.changelist(), 'class="action-select"', count=10)
        self.assertEqual(count_queries(self.changelist), few)

    def test_stock_and_integrations_of_each_row(self):
        self.add_products(1, 1)
        html = self.changelist().content.decode()
        self.assertIn('С1:&nbsp;1<span style="color: #090" title="&lt;b&gt;сверка&lt;/b&gt;">+1</span><br/>', html)
        self.assertNotIn('С3:', html)  # not shown in orders
        self.assertIn('Каталог/Машины/Машины</option>', html)
        self.assertIn('&nbsp;USD', html)  # the price in its currency
        # each row's form has the product's integrations checked: the newest first, the set has none
        self.assertRegex(html, r'<input type="checkbox" name="form-1-integrations" value="%d"[^>]*checked' % self.integrations[1].pk)
        self.assertNotRegex(html, r'name="form-0-integrations"[^>]*checked')
        self.assertEqual(html.count(' checked>'), 3)  # and the two rows' show_on_sw


class CategoryLabelTests(TestCase):
    """ The admin shows categories by their full paths, which tell those of the same name apart """

    def setUp(self):
        catalog = Category.objects.create(name='Каталог', slug='catalog')
        self.machines = Category.objects.create(name='Машины', slug='machines', parent=catalog)
        self.used = Category.objects.create(name='Машины', slug='used', parent=self.machines)

    def test_paths(self):
        self.assertEqual(list(Category.paths().values()), ['Каталог', 'Каталог/Машины', 'Каталог/Машины/Машины'])
        self.assertEqual(str(self.used), 'Машины')  # elsewhere the name alone

    def test_product_form_reads_the_paths_once(self):
        request = RequestFactory().get('/')
        request.user = ShopUser.objects.create(phone='+79990000000', is_staff=True, is_superuser=True)
        field = admin_site._registry[Product].get_form(request)().fields['categories']
        with self.assertNumQueries(2):  # the categories, and all their paths
            labels = [label for value, label in field.choices]
        self.assertEqual(labels, ['Каталог', 'Каталог/Машины', 'Каталог/Машины/Машины'])
