"""
Admin index page: the app groups of SWAdminSite.get_app_list() and the tabs of SWAdminSite.index().
"""
from django.contrib import admin
from django.contrib.auth.models import Permission
from django.test import RequestFactory, TestCase, override_settings
from django.urls import path

from shop.models import ShopUser

urlpatterns = [path('admin/', admin.site.urls)]


@override_settings(ROOT_URLCONF=__name__)
class AdminIndexTests(TestCase):
    def setUp(self):
        self.request = RequestFactory().get('/admin/')
        self.request.user = ShopUser.objects.create(phone='+79990000000', is_staff=True, is_superuser=True)
        self.request.user.is_verified = lambda: True  # as the OTP middleware sets it

    def test_shop_lists_flat_pages_and_files(self):
        apps = {app['app_label']: app for app in admin.site.get_app_list(self.request)}
        self.assertNotIn('flatpages', apps)
        self.assertNotIn('filemanager', apps)
        shop = [model['object_name'] for model in apps['shop']['models']]
        self.assertIn('FlatPage', shop)
        self.assertIn('File', shop)
        names = [model['name'] for model in apps['shop']['models']]
        self.assertEqual(names, sorted(names))
        self.assertEqual([model['object_name'] for model in apps['sewingworld']['models']], ['Config', 'Site'])
        self.assertEqual(apps['django_comments']['name'], 'Комментарии')

    def test_tabs(self):
        response = admin.site.index(self.request)
        tabs = {tab['id']: [app['app_label'] for app in tab['apps']] for tab in response.context_data['tabs']}
        self.assertEqual(list(tabs), ['shop', 'access', 'system'])
        self.assertEqual(tabs['shop'], ['shop', 'sewingworld', 'django_comments', 'blog'])  # in index_tabs order
        self.assertEqual(tabs['access'][0], 'auth')
        self.assertIn('errors', tabs['system'])
        # Every app is in one tab only, the last one takes those the others leave
        placed = [label for labels in tabs.values() for label in labels]
        self.assertCountEqual(placed, [app['app_label'] for app in response.context_data['app_list']])
        # The shop spans its tab, the other apps go beside it
        shop_tab = response.context_data['tabs'][0]
        self.assertEqual([app['app_label'] for app in shop_tab['main']], ['shop'])
        self.assertEqual([app['app_label'] for app in shop_tab['side']], tabs['shop'][1:])
        self.assertNotIn('side', response.context_data['tabs'][1])

        content = response.render().content.decode()
        self.assertEqual(content.count('role="tab"'), 3)
        self.assertIn('id="panel-access"', content)
        self.assertIn('<details class="sw-recent">', content)
        self.assertNotIn('id="content-related"', content)
        self.assertIn('class="sw-tab-panel sw-split"', content)

    def test_app_page_has_no_tabs(self):
        # admin/app_index.html extends the index
        content = admin.site.app_index(self.request, 'shop').render().content.decode()
        self.assertIn('class="sw-tab-panel"', content)
        self.assertIn('class="app-shop module', content)
        self.assertNotIn('sw-index-bar', content)
        self.assertNotIn('admin-index.js', content)

    def test_one_tab_has_no_tab_bar(self):
        staff = ShopUser.objects.create(phone='+79990000001', is_staff=True)
        staff.user_permissions.add(Permission.objects.get(content_type__app_label='shop', codename='view_order'))
        self.request.user = ShopUser.objects.get(pk=staff.pk)
        self.request.user.is_verified = lambda: True
        response = admin.site.index(self.request)
        self.assertEqual([tab['id'] for tab in response.context_data['tabs']], ['shop'])
        self.assertEqual([app['app_label'] for app in response.context_data['tabs'][0]['apps']], ['shop'])
        content = response.render().content.decode()
        self.assertNotIn('role="tab"', content)
        self.assertIn('id="panel-shop"', content)
