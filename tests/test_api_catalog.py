"""
The catalog: categories, product kinds and products. See settings.py on how to run.
"""
from django.contrib.sites.models import Site
from django.test import TestCase

from shop.models import Category, Manufacturer, ProductImage, ProductKind, ProductSet, ShopUser, Stock, Store, Supplier

from .clients import StorefrontClient, add_storefront_key, signed_in
from .fixtures import add_catalog, add_city, add_product

BAD_PARAMETER = ['Неверное значение']


class Base(TestCase):
    def setUp(self):
        add_storefront_key()
        self.site = Site.objects.get_current()
        self.root = add_catalog()
        self.machines = Category.objects.create(name='Швейные машины', slug='machines', parent=self.root)
        self.janome = Category.objects.create(name='Janome', slug='janome', parent=self.machines)
        self.client = StorefrontClient()

    def get(self, path, **params):
        return self.client.get(f'/api/v0/{path}', params)


class CategoryTests(Base):
    def setUp(self):
        super().setUp()
        Category.objects.create(name='Спрятанная', slug='hidden', parent=self.root, hidden=True)
        self.off = Category.objects.create(name='Выключенная', slug='off', parent=self.root, active=False)
        Category.objects.create(name='Ткани', slug='fabrics', parent=self.root, feed=False)

    def test_tree_of_the_sites_catalog(self):
        response = self.get('categories/')
        self.assertEqual(response.status_code, 200)
        tree = {category['slug']: [child['slug'] for child in category.get('children', [])] for category in response.json()}
        self.assertEqual(tree, {'machines': ['janome'], 'fabrics': []})

    def test_feed_filter(self):
        self.assertEqual([category['slug'] for category in self.get('categories/', feed='true').json()], ['machines'])
        self.assertEqual([category['slug'] for category in self.get('categories/', feed='false').json()], ['fabrics'])

    def test_by_id(self):
        data = self.get(f'categories/{self.janome.id}/').json()
        self.assertEqual(data['name'], 'Janome')
        self.assertEqual(data['path'], {'uri': 'machines/janome', 'breadcrumbs': [
            {'id': self.machines.id, 'slug': 'machines', 'name': 'Швейные машины'},
            {'id': self.janome.id, 'slug': 'janome', 'name': 'Janome'},
        ]})

    def test_by_path(self):
        self.assertEqual(self.get('categories/machines/janome/').json()['id'], self.janome.id)
        self.assertEqual([child['slug'] for child in self.get('categories/machines/').json()['children']], ['janome'])

    def test_inactive_is_not_found(self):
        self.assertEqual(self.get(f'categories/{self.off.id}/').status_code, 404)
        self.assertEqual(self.get('categories/off/').status_code, 404)

    def test_path_in_another_catalog_is_not_found(self):
        other_root = Category.objects.create(name='Другой каталог', slug='other')
        Category.objects.create(name='Столы', slug='tables', parent=other_root)
        self.assertEqual(self.get('categories/tables/').status_code, 404)

    def test_filters_of_the_category(self):
        self.janome.filters = 'manufacturer'
        self.janome.save()
        [manufacturer] = self.get(f'categories/{self.janome.id}/').json()['filters']
        self.assertEqual((manufacturer['name'], manufacturer['class']), ('manufacturer', 'MultipleChoiceField'))


class KindTests(Base):
    def test_list_and_kinds_of_products(self):
        ProductKind.objects.create(name='Швейная машина', comparison=[])
        overlock = ProductKind.objects.create(name='Оверлок', comparison=[])
        add_product(1).kind.add(overlock)
        self.assertEqual({kind['name'] for kind in self.get('kinds/').json()}, {'Швейная машина', 'Оверлок'})
        self.assertEqual([kind['id'] for kind in self.get('kinds/', product=1).json()], [overlock.id])
        self.assertEqual(self.get(f'kinds/{overlock.id}/').json()['name'], 'Оверлок')

    def test_malformed_product(self):
        response = self.get('kinds/', product='abc')
        self.assertEqual((response.status_code, response.json()), (400, {'product': BAD_PARAMETER}))


class ProductListTests(Base):
    def setUp(self):
        super().setUp()
        self.brand = Manufacturer.objects.create(code='janome', name='Janome')
        self.kind = ProductKind.objects.create(name='Швейная машина', comparison=[])
        machine = add_product(1, title='Janome 1225s', price=20000, enabled=True, manufacturer=self.brand,
                              sites=[self.site], categories=[self.janome])
        machine.kind.add(self.kind)
        add_product(2, title='Иглы', price=300, num=0, sites=[self.site], categories=[self.machines])
        add_product(3, title='С другого сайта', sites=[Site.objects.create(domain='other.test', name='other')])

    def ids(self, **params):
        response = self.get('products/', **params)
        self.assertEqual(response.status_code, 200, response.content)
        return sorted(product['id'] for product in response.json()['results'])

    def test_products_of_the_site_in_pages(self):
        self.assertEqual(self.ids(), [1, 2])
        data = self.get('products/', page_size=1).json()
        self.assertEqual((data['count'], data['totalPages'], data['currentPage'], data['pageSize']), (2, 2, 1, 1))
        self.assertIsNotNone(data['next'])
        self.assertEqual(len(data['results']), 1)

    def test_prices_and_stock(self):
        [product] = self.get('products/', id=1).json()['results']
        self.assertEqual((product['price'], product['cost'], product['instock']), (20000, 20000, 5))

    def test_chosen_fields(self):
        self.assertEqual(self.get('products/', id=1, fields='id,title').json()['results'], [{'id': 1, 'title': 'Janome 1225s'}])

    def test_typeahead_gets_titles(self):
        self.assertEqual(self.get('products/', id=1, ta='1').json()['results'], ['Janome 1225s'])

    def test_feed_fields(self):
        [product] = self.get('products/', id=1, for_xml='true').json()['results']
        self.assertEqual(product['categories'], [self.janome.id])
        self.assertEqual(product['manufacturer']['code'], 'janome')
        self.assertNotIn('stock', product)  # only feeds of integrations have it

    def test_filters(self):
        self.assertEqual(self.ids(id=[1, 2]), [1, 2])
        self.assertEqual(self.ids(id=2), [2])
        self.assertEqual(self.ids(title='JANOME'), [1])
        self.assertEqual(self.ids(enabled='true'), [1])
        self.assertEqual(self.ids(enabled='false'), [2])
        self.assertEqual(self.ids(instock=1), [1])
        self.assertEqual(self.ids(instock=0), [2])
        self.assertEqual(self.ids(price='10000-30000'), [1])
        self.assertEqual(self.ids(kind=self.kind.id), [1])
        self.assertEqual(self.ids(manufacturer=self.brand.id), [1])
        self.assertEqual(self.ids(manufacturer=[self.brand.id, 49]), [1, 2])
        self.assertEqual(self.ids(code='p2'), [2])
        self.assertEqual(self.ids(unknown='x'), [1, 2])

    def test_ordering(self):
        self.assertEqual([product['id'] for product in self.get('products/', ordering='-price').json()['results']], [1, 2])
        self.assertEqual([product['id'] for product in self.get('products/', ordering='price').json()['results']], [2, 1])

    def test_category_brings_its_filters(self):
        self.janome.filters = 'manufacturer'
        self.janome.save()
        data = self.get('products/', categories=self.janome.id).json()
        self.assertEqual([product['id'] for product in data['results']], [1])
        self.assertEqual(data['filters']['manufacturer']['choices'], [[self.brand.id, 'Janome']])

    def test_category_without_filters(self):
        data = self.get('products/', categories=self.machines.id).json()
        self.assertEqual([product['id'] for product in data['results']], [2])
        self.assertNotIn('filters', data)

    def test_in_category_takes_subcategories(self):
        self.assertEqual(self.ids(in_category=self.machines.id), [1, 2])
        self.assertEqual(self.ids(in_category=self.janome.id), [1])

    def test_unknown_category_finds_nothing(self):
        self.assertEqual(self.ids(categories=999), [])
        self.assertEqual(self.ids(in_category=999), [])

    def test_full_text_search(self):
        for product in self.site.products.all():
            product.update_fts_vector()
        data = self.get('products/', text='janome').json()
        self.assertEqual([product['id'] for product in data['results']], [1])
        self.assertGreater(data['results'][0]['rank'], 0)
        self.assertEqual(set(data['filters']), {'manufacturer', 'price'})

    def test_malformed_values(self):
        for name, value in (('instock', 'abc'), ('categories', 'abc'), ('in_category', 'abc'), ('id', 'abc'), ('kind', 'abc'),
                            ('manufacturer', 'abc'), ('price', 'a-b'), ('order', 'abc'), ('title__nope', 'x')):
            with self.subTest(name):
                response = self.get('products/', **{name: value})
                self.assertEqual((response.status_code, response.json()), (400, {name: BAD_PARAMETER}))


class ProductTests(Base):
    def setUp(self):
        super().setUp()
        self.product = add_product(1, title='Janome 1225s', price=20000, video_url='https://video.test/1',
                                   sites=[self.site], categories=[self.machines])
        add_product(2, sites=[self.site])  # in no category of the site's catalog

    def test_retrieve(self):
        data = self.get('products/1/').json()
        self.assertEqual((data['title'], data['price']), ('Janome 1225s', 20000))
        self.assertEqual(data['categories'], [{
            'id': self.machines.id, 'name': 'Швейные машины', 'slug': 'machines',
            'path': {'uri': 'machines', 'breadcrumbs': [{'id': self.machines.id, 'slug': 'machines', 'name': 'Швейные машины'}]},
        }])

    def test_outside_the_sites_catalog_is_not_found(self):
        self.assertEqual(self.get('products/2/').status_code, 404)
        self.assertEqual(self.get('products/999/').status_code, 404)

    def test_by_code(self):
        self.assertEqual(self.get('products/p1/bycode/').json()['id'], 1)
        self.assertEqual(self.get('products/p2/bycode/').status_code, 404)
        self.assertEqual(self.get('products/nope/bycode/').status_code, 404)

    def test_info_is_the_list_entry(self):
        self.assertEqual(self.get('products/1/info/', fields='id,price').json(), {'id': 1, 'price': 20000})

    def test_field_names(self):
        self.assertEqual(self.get('products/fields/').json()['title'], 'Название')

    def test_images(self):
        ProductImage.objects.create(product=self.product, image='products/test/p1/2.jpg', order=2)
        ProductImage.objects.create(product=self.product, image='products/test/p1/1.jpg', order=1)
        self.assertEqual(self.get('products/1/images/').json(), [
            {'src': 'http://testserver/media/products/test/p1/1.jpg'},
            {'src': 'http://testserver/media/products/test/p1/2.jpg'},
        ])

    def test_price_with_the_users_discount(self):
        self.assertEqual(self.get('products/1/price/').status_code, 403)
        user = ShopUser.objects.create(phone='+79161234567', discount=5)
        data = signed_in(user).get('/api/v0/products/1/price/').json()
        self.assertEqual(data, {'user': user.id, 'user_discount': 5, 'price': 20000, 'cost': 19000})

    def test_video(self):
        self.assertRedirects(self.get('products/p1/video/'), 'https://video.test/1', fetch_redirect_response=False)
        self.assertEqual(self.get('products/p2/video/').status_code, 404)

    def test_video_qr_code(self):
        response = self.get('products/1/video/qr/')
        self.assertEqual(response['Content-Type'], 'image/svg+xml')
        self.assertIn(b'<svg', response.content)


class StoreStockTests(Base):
    def setUp(self):
        super().setUp()
        city = add_city()
        self.suppliers = Supplier.objects.bulk_create(Supplier(code=f's{n}', code1c=f's{n}', name=f'Склад {n}', order=n) for n in (1, 2))
        # without Store.save(), which asks the storefront to revalidate its pages
        self.stores = Store.objects.bulk_create(
            Store(city=city, site=self.site, supplier=supplier, address=f'Адрес {n}', name=f'Магазин {n}')
            for n, supplier in enumerate(self.suppliers, 1)
        )
        self.machine, self.table, self.bundle = add_product(1), add_product(2), add_product(3)

    def stores_with(self, product):
        return [store['id'] for store in self.get(f'products/{product.id}/stock/').json()]

    def stock(self, product, store, quantity, correction=0):
        Stock.objects.create(product=product, supplier=self.suppliers[store], quantity=quantity, correction=correction)

    def test_stores_that_have_the_product(self):
        self.stock(self.machine, 0, 2)
        self.stock(self.machine, 1, 1, correction=-1)
        self.assertEqual(self.stores_with(self.machine), [self.stores[0].id])

    def test_set_is_in_stores_that_have_all_its_parts(self):
        ProductSet.objects.create(declaration=self.bundle, constituent=self.machine)
        ProductSet.objects.create(declaration=self.bundle, constituent=self.table, quantity=2)
        self.stock(self.machine, 0, 1)
        self.stock(self.table, 0, 2)
        self.stock(self.machine, 1, 5)
        self.stock(self.table, 1, 1)  # less than the set needs
        self.assertEqual(self.stores_with(self.bundle), [self.stores[0].id])

    def test_set_without_stock_of_a_part(self):
        ProductSet.objects.create(declaration=self.bundle, constituent=self.machine)
        ProductSet.objects.create(declaration=self.bundle, constituent=self.table)
        self.stock(self.machine, 0, 1)
        self.assertEqual(self.stores_with(self.bundle), [])
