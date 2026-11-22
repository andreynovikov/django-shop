import os
import shutil
import tempfile

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.flatpages.models import FlatPage
from django.contrib.messages import get_messages
from django.contrib.messages.storage.cookie import CookieStorage
from django.core.exceptions import PermissionDenied
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import Http404
from django.test import RequestFactory, TestCase, override_settings
from django.utils import translation

from filemanager.admin import FileAdmin
from filemanager.models import File

ALL = {'view', 'add', 'change', 'delete'}


@override_settings(ROOT_URLCONF='filemanager.tests.urls', FILEMANAGER_STORAGE='default', FILEMANAGER_PROTECTED=['products'])
class AdminTests(TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.root)
        media = override_settings(MEDIA_ROOT=self.root, MEDIA_URL='/media/')
        media.enable()
        self.addCleanup(media.disable)
        os.makedirs(os.path.join(self.root, 'images', 'janome'))
        os.makedirs(os.path.join(self.root, 'products'))
        self.write('images/janome/a.jpg', b'old')
        self.model_admin = FileAdmin(File, admin.site)
        translation.activate('en')  # the project's LANGUAGE_CODE may be another
        self.addCleanup(translation.deactivate)

    def write(self, path, data):
        with open(os.path.join(self.root, path), 'wb') as f:
            f.write(data)

    def read(self, path):
        with open(os.path.join(self.root, path), 'rb') as f:
            return f.read()

    def request(self, method='get', data=None, perms=ALL):
        request = getattr(RequestFactory(), method)('/admin/filemanager/file/', data or {})
        user = get_user_model()(is_active=True, is_staff=True)
        user.has_perm = lambda perm, obj=None: perm.startswith('filemanager.') and perm.split('.')[1].split('_')[0] in perms
        user.has_module_perms = lambda app_label: True
        user.is_verified = lambda: True  # django-otp, in a project whose admin asks for a second factor
        request.user = user
        request._messages = CookieStorage(request)
        return request

    def call(self, view, method='get', data=None, perms=ALL):
        request = self.request(method, data, perms)
        response = view(request)
        if hasattr(response, 'render'):
            response.render()
        response.messages = [str(message) for message in get_messages(request)]
        return response

    def test_browse(self):
        response = self.call(self.model_admin.browse_view, data={'dir': 'images/janome'})
        self.assertContains(response, 'a.jpg')
        self.assertContains(response, 'data-url="/media/images/janome/a.jpg"')
        self.assertContains(response, 'id="filemanager-upload"')
        self.assertNotContains(response, 'filemanager-insert"')
        root = self.call(self.model_admin.browse_view)
        self.assertContains(root, '?dir=images')
        self.assertContains(root, '?path=images')  # the images folder can be renamed
        self.assertNotContains(root, '?path=products')  # but not the protected one

    def test_browse_popup(self):
        response = self.call(self.model_admin.browse_view, data={'dir': 'images/janome', '_popup': '1', '_target': 'id_content'})
        self.assertContains(response, 'filemanager-insert')
        self.assertContains(response, 'data-kind="image"')
        self.assertContains(response, '_target=id_content')
        bad = self.call(self.model_admin.browse_view, data={'_popup': '1', '_target': '"><script>'})
        self.assertNotContains(bad, 'filemanager-insert')

    def test_browse_protected_and_missing(self):
        response = self.call(self.model_admin.browse_view, data={'dir': 'products'})
        self.assertNotContains(response, 'id="filemanager-upload"')
        for folder in ('missing', '../', 'images/janome/a.jpg'):
            with self.subTest(folder=folder), self.assertRaises(Http404):
                self.call(self.model_admin.browse_view, data={'dir': folder})

    def test_permissions(self):
        response = self.call(self.model_admin.browse_view, data={'dir': 'images/janome'}, perms={'view'})
        self.assertNotContains(response, 'id="filemanager-upload"')
        self.assertNotContains(response, '/rename/')
        self.assertNotContains(response, '/delete/?')
        for view, method, perms in (
            (self.model_admin.browse_view, 'get', set()),
            (self.model_admin.upload_view, 'post', {'view', 'change'}),
            (self.model_admin.mkdir_view, 'post', {'view', 'change'}),
            (self.model_admin.rename_view, 'get', {'view', 'add'}),
            (self.model_admin.delete_file_view, 'get', {'view', 'change'}),
        ):
            with self.subTest(view=view.__name__), self.assertRaises(PermissionDenied):
                self.call(view, method, {'dir': 'images', 'path': 'images/janome/a.jpg', 'name': 'x'}, perms=perms)
        with self.assertRaises(PermissionDenied):  # replacing needs change
            self.call(self.model_admin.upload_view, 'post', {
                'dir': 'images/janome', 'overwrite': '1', 'files': SimpleUploadedFile('a.jpg', b'new'),
            }, perms={'view', 'add'})

    def test_upload(self):
        response = self.call(self.model_admin.upload_view, 'post', {
            'dir': 'images/janome', 'files': [SimpleUploadedFile('a.jpg', b'new'), SimpleUploadedFile('b.jpg', b'b')],
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], '/admin/filemanager/file/?dir=images%2Fjanome')
        self.assertEqual(self.read('images/janome/a.jpg'), b'old')
        self.assertEqual(self.read('images/janome/b.jpg'), b'b')
        self.assertEqual(len(response.messages), 2)
        self.call(self.model_admin.upload_view, 'post', {
            'dir': 'images/janome', 'overwrite': '1', 'files': SimpleUploadedFile('a.jpg', b'new'),
        })
        self.assertEqual(self.read('images/janome/a.jpg'), b'new')
        self.call(self.model_admin.upload_view, 'post', {'dir': 'products', 'files': SimpleUploadedFile('c.jpg', b'c')})
        self.assertFalse(os.path.exists(os.path.join(self.root, 'products', 'c.jpg')))

    def test_mkdir(self):
        response = self.call(self.model_admin.mkdir_view, 'post', {'dir': 'images', 'name': ' singer ', '_popup': '1', '_target': 'id_spec'})
        self.assertEqual(response['Location'], '/admin/filemanager/file/?dir=images%2Fsinger&_popup=1&_target=id_spec')
        self.assertTrue(os.path.isdir(os.path.join(self.root, 'images', 'singer')))

    def test_rename(self):
        page = FlatPage.objects.create(url='/about/', title='About', content='<img src="/media/images/janome/a.jpg">')
        response = self.call(self.model_admin.rename_view, data={'path': 'images/janome/a.jpg'})
        self.assertContains(response, 'value="images/janome/a.jpg"')
        self.assertContains(response, page.title)
        response = self.call(self.model_admin.rename_view, 'post', {'path': 'images/janome/a.jpg', 'target': 'images/b.jpg'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.read('images/b.jpg'), b'old')
        response = self.call(self.model_admin.rename_view, 'post', {'path': 'images/b.jpg', 'target': 'products/b.jpg'})
        self.assertContains(response, 'errornote')
        self.assertEqual(self.read('images/b.jpg'), b'old')

    def test_delete(self):
        FlatPage.objects.create(url='/about/', title='About', content='<a href="https://shop.test/media/images/janome/a.jpg">')
        response = self.call(self.model_admin.delete_file_view, data={'path': 'images'})
        self.assertContains(response, 'About')
        self.assertContains(response, '1 file')
        response = self.call(self.model_admin.delete_file_view, 'post', {'path': 'images'})
        self.assertEqual(response['Location'], '/admin/filemanager/file/')
        self.assertFalse(os.path.exists(os.path.join(self.root, 'images')))

    def test_usage(self):
        self.write('images/janome/b c.jpg', b'')
        FlatPage.objects.create(url='/a/', title='Raw', content='<img src="/images/janome/b c.jpg">')
        FlatPage.objects.create(url='/b/', title='Quoted', content='<img src="/media/images/janome/b%20c.jpg">')
        FlatPage.objects.create(url='/c/', title='Other', content='<img src="/media/images/janome/a.jpg">')
        response = self.call(self.model_admin.usage_view, data={'path': 'images/janome/b c.jpg'})
        self.assertContains(response, 'Raw')
        self.assertContains(response, 'Quoted')
        self.assertNotContains(response, 'Other')
        self.assertContains(response, '/admin/flatpages/flatpage/')
        with override_settings(FILEMANAGER_USAGE_EXCLUDE=['flatpages.FlatPage']):
            response = self.call(self.model_admin.usage_view, data={'path': 'images/janome/b c.jpg'})
        self.assertNotContains(response, 'Raw')

    def test_translations(self):
        for language, texts in (('en', ['Drop files here', 'Where used', 'New folder']), ('ru', ['Где используется', 'Новая папка'])):
            with translation.override(language):
                response = self.call(self.model_admin.browse_view, data={'dir': 'images/janome'})
            for text in texts:
                self.assertContains(response, text, msg_prefix=language)
