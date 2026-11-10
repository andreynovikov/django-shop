"""
What the storefronts show besides the catalog: pages, news, sales actions, adverts, stores, service centers
and the sites themselves. See settings.py on how to run.
"""
from django.contrib.flatpages.models import FlatPage
from django.contrib.sites.models import Site
from django.test import TestCase

from sewingworld.models import SiteProfile
from shop.models import Advert, Category, News, SalesAction, ServiceCenter, ShopUser, Store, StoreImage

from .clients import StorefrontClient, add_storefront_key, signed_in
from .fixtures import add_city, add_product


class Base(TestCase):
    def setUp(self):
        add_storefront_key()
        self.site = Site.objects.get_current()
        self.other_site = Site.objects.create(domain='other.test', name='other')
        self.client = StorefrontClient()

    def get(self, path, **params):
        return self.client.get(f'/api/v0/{path}', params)


class PageTests(Base):
    def setUp(self):
        super().setUp()
        for url, title, site in (('/about/', 'О нас', self.site), ('/help/delivery/', 'Доставка', self.site),
                                 ('/other/', 'Чужая', self.other_site)):
            FlatPage.objects.create(url=url, title=title, content=f'<p>{title}</p>').sites.add(site)

    def test_pages_of_the_site(self):
        self.assertEqual(sorted(page['url'] for page in self.get('pages/').json()), ['/about/', '/help/delivery/'])

    def test_by_path(self):
        self.assertEqual(self.get('pages/about/').json()['content'], '<p>О нас</p>')
        self.assertEqual(self.get('pages/help/delivery/').json()['title'], 'Доставка')
        self.assertEqual(self.get('pages/other/').status_code, 404)
        self.assertEqual(self.get('pages/nope/').status_code, 404)


class NewsTests(Base):
    def test_active_news_of_the_site(self):
        shown = News.objects.create(title='Открытие', content='...', active=True)
        shown.sites.add(self.site)
        News.objects.create(title='Черновик', content='...', active=False).sites.add(self.site)
        News.objects.create(title='Чужая', content='...', active=True).sites.add(self.other_site)
        self.assertEqual([news['title'] for news in self.get('news/').json()], ['Открытие'])
        self.assertEqual(self.get(f'news/{shown.id}/').json()['content'], '...')
        for hidden in News.objects.exclude(pk=shown.pk):
            self.assertEqual(self.get(f'news/{hidden.id}/').status_code, 404)


class SalesActionTests(Base):
    def action(self, slug, site=None, **fields):
        fields.setdefault('active', True)
        action = SalesAction.objects.create(name=slug, slug=slug, order=0, **fields)
        action.sites.add(site or self.site)
        return action

    def test_list_and_retrieve(self):
        self.action('sale', notice='Скидка')
        self.action('secret', show_in_list=False)
        self.action('over', active=False)
        self.action('elsewhere', site=self.other_site)
        self.assertEqual([action['slug'] for action in self.get('salesactions/').json()], ['sale'])
        self.assertEqual(self.get('salesactions/sale/').json()['notice'], 'Скидка')
        self.assertEqual(self.get('salesactions/secret/').json()['slug'], 'secret')  # its link still works
        self.assertEqual(self.get('salesactions/over/').status_code, 404)
        self.assertEqual(self.get('salesactions/elsewhere/').status_code, 404)

    def test_enabled_products_dearest_first(self):
        action = self.action('sale')
        for pk, price, enabled in ((1, 300, True), (2, 20000, True), (3, 5000, False)):
            add_product(pk, price=price, enabled=enabled).sales_actions.add(action)
        data = self.get('salesactions/sale/products/').json()
        self.assertEqual([product['id'] for product in data['results']], [2, 1])
        self.assertEqual(data['count'], 2)


class AdvertTests(Base):
    def advert(self, name, place='main', site=None, active=True):
        advert = Advert.objects.create(name=name, place=place, active=active, content=name, order=0)
        advert.sites.add(site or self.site)
        return advert

    def names(self, **params):
        return sorted(advert['name'] for advert in self.get('adverts/', **params).json())

    def test_active_adverts_of_the_site(self):
        self.advert('Баннер')
        self.advert('Старый', active=False)
        self.advert('Чужой', site=self.other_site)
        self.assertEqual(self.names(), ['Баннер'])

    def test_by_place_and_category(self):
        category = Category.objects.create(name='Машины', slug='machines')
        self.advert('Главная')
        self.advert('Подвал', place='footer')
        self.advert('В категории', place='category').categories.add(category)
        self.assertEqual(self.names(place=['main', 'footer']), ['Главная', 'Подвал'])
        self.assertEqual(self.names(category=category.id), ['В категории'])
        response = self.get('adverts/', category='abc')
        self.assertEqual((response.status_code, response.json()), (400, {'category': ['Неверное значение']}))


class StoreTests(Base):
    def setUp(self):
        super().setUp()
        moscow, tula = add_city('Москва'), add_city('Тула')
        # without Store.save(), which asks the storefront to revalidate its pages
        self.tula, self.moscow, *_ = Store.objects.bulk_create([
            Store(city=tula, site=self.site, address='Советская, 1', name='Тула', lottery=True),
            Store(city=moscow, site=self.site, address='Тверская, 1', name='Москва', marketplace=True,
                  phone='+7 495 111-11-11, +7 495 222-22-22', phone2='+7 999 333-33-33'),
            Store(city=moscow, site=self.site, address='Арбат, 1', name='Закрыт', enabled=False),
            Store(city=moscow, site=self.other_site, address='Невский, 1', name='Чужой'),
        ])

    def names(self, **params):
        return [store['name'] for store in self.get('stores/', **params).json()]

    def test_enabled_stores_of_the_site_by_city(self):
        self.assertEqual(self.names(), ['Москва', 'Тула'])
        self.assertEqual(self.names(marketplace=1), ['Москва'])
        self.assertEqual(self.names(lottery=1), ['Тула'])

    def test_retrieve(self):
        StoreImage.objects.create(store=self.moscow, image='stores/moscow.jpg', image_width=800, image_height=600, order=1)
        data = self.get(f'stores/{self.moscow.id}/').json()
        self.assertEqual(data['phones'], ['+7 495 111-11-11', '+7 495 222-22-22', '+7 999 333-33-33'])
        self.assertEqual(data['city']['name'], 'Москва')
        self.assertEqual([(image['image'], image['image_width']) for image in data['images']], [('http://testserver/media/stores/moscow.jpg', 800)])
        self.assertEqual(self.get(f'stores/{Store.objects.get(name="Закрыт").id}/').status_code, 404)
        self.assertEqual(self.get(f'stores/{Store.objects.get(name="Чужой").id}/').status_code, 404)


class ServiceCenterTests(Base):
    def test_enabled_centers(self):
        city = add_city()
        center = ServiceCenter.objects.create(city=city, address='Ленина, 1', phone='+7 495 111-11-11')
        off = ServiceCenter.objects.create(city=city, address='Мира, 1', enabled=False)
        self.assertEqual([center['address'] for center in self.get('servicecenters/').json()], ['Ленина, 1'])
        self.assertEqual(self.get(f'servicecenters/{center.id}/').json()['city']['name'], 'Москва')
        self.assertEqual(self.get(f'servicecenters/{off.id}/').status_code, 404)


class SiteTests(Base):
    def setUp(self):
        super().setUp()
        SiteProfile.objects.filter(site=self.site).update(title='Швейный Мир', phone='+7 495 766-56-75')
        SiteProfile.objects.create(site=self.other_site, title='Другой', wholesale=True)

    def test_superuser_sees_all_sites(self):
        client = signed_in(ShopUser.objects.create(phone='+79160000001', is_superuser=True))
        sites = client.get('/api/v0/sites/').json()
        self.assertEqual(sorted(site['title'] for site in sites), ['Другой', 'Швейный Мир'])
        data = client.get(f'/api/v0/sites/{self.other_site.id}/').json()
        self.assertEqual(data, {'id': self.other_site.id, 'url_prefix': 'https://other.test', 'title': 'Другой', 'wholesale': True})

    def test_others_see_only_the_current_one(self):
        for client in (self.client, signed_in(ShopUser.objects.create(phone='+79161234567'))):
            self.assertEqual(client.get('/api/v0/sites/').status_code, 403)
            self.assertEqual(client.get(f'/api/v0/sites/{self.site.id}/').status_code, 403)
            self.assertEqual(client.get('/api/v0/sites/current/').json()['title'], 'Швейный Мир')
