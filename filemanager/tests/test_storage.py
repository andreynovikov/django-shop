import os
import shutil
import tempfile

from django.core.exceptions import SuspiciousFileOperation
from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage
from django.test import SimpleTestCase

from filemanager.storage import FileExists, FileManagerError, FileSystemStore, clean_path


class Base(SimpleTestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.root)
        self.store = FileSystemStore(FileSystemStorage(self.root, '/media/'), protected=['products'])
        os.makedirs(os.path.join(self.root, 'images', 'janome'))
        os.makedirs(os.path.join(self.root, 'products'))
        self.write('images/janome/a b.jpg', b'old')
        self.write('products/p.jpg', b'p')

    def write(self, path, data):
        with open(os.path.join(self.root, path), 'wb') as f:
            f.write(data)

    def read(self, path):
        with open(os.path.join(self.root, path), 'rb') as f:
            return f.read()


class PathTests(SimpleTestCase):
    def test_clean(self):
        self.assertEqual(clean_path(''), '')
        self.assertEqual(clean_path('/images/Швейные машины/a b.jpg/'), 'images/Швейные машины/a b.jpg')
        for path in ('../etc', 'a/../b', 'a/./b', 'a//b', '.hidden', 'a/.git', 'a\\b', 'a\x00b', 'a\nb', 'x' * 256):
            with self.subTest(path=path), self.assertRaises(FileManagerError):
                clean_path(path)


class StoreTests(Base):
    def test_list(self):
        self.write('images/.ftpquota', b'')
        self.write('images/top.pdf', b'pdf')
        folders, files = self.store.list('images')
        self.assertEqual([entry.name for entry in folders], ['janome'])
        self.assertEqual([(entry.name, entry.size, entry.kind, entry.url) for entry in files], [('top.pdf', 3, 'file', '/media/images/top.pdf')])
        folders, files = self.store.list('images/janome')
        self.assertEqual(files[0].url, '/media/images/janome/a%20b.jpg')
        self.assertEqual(files[0].kind, 'image')
        self.assertIsNotNone(files[0].modified.tzinfo)

    def test_list_skips_names_that_are_not_utf8(self):
        with open(os.path.join(os.fsencode(self.root), b'images', 'файл.txt'.encode('cp1251')), 'wb'):
            pass
        self.assertEqual([entry.name for entry in self.store.list('images')[1]], [])

    def test_save_new_and_overwrite(self):
        self.assertEqual(self.store.save('images', 'Новый файл.png', ContentFile(b'new')), 'images/Новый файл.png')
        self.assertEqual(self.read('images/Новый файл.png'), b'new')
        with self.assertRaises(FileExists):
            self.store.save('images/janome', 'a b.jpg', ContentFile(b'new'))
        self.assertEqual(self.read('images/janome/a b.jpg'), b'old')
        self.assertEqual(self.store.save('images/janome', 'a b.jpg', ContentFile(b'new'), overwrite=True), 'images/janome/a b.jpg')
        self.assertEqual(self.read('images/janome/a b.jpg'), b'new')
        self.assertEqual(sorted(os.listdir(os.path.join(self.root, 'images', 'janome'))), ['a b.jpg'])  # no temporary file left

    def test_save_refusals(self):
        for folder, name in (('images', 'janome'), ('missing', 'a.jpg'), ('products', 'a.jpg'), ('images', '.htaccess')):
            with self.subTest(folder=folder, name=name), self.assertRaises(FileManagerError):
                self.store.save(folder, name, ContentFile(b'x'))

    def test_mkdir(self):
        self.assertEqual(self.store.mkdir('images', 'singer'), 'images/singer')
        self.assertEqual(self.store.kind('images/singer'), 'dir')
        for folder, name in (('images', 'singer'), ('images', 'janome'), ('', 'products'), ('products', 'x'), ('nowhere', 'x')):
            with self.subTest(folder=folder, name=name), self.assertRaises(FileManagerError):
                self.store.mkdir(folder, name)

    def test_rename(self):
        self.store.rename('images/janome/a b.jpg', 'images/janome/c.jpg')
        self.assertEqual(self.read('images/janome/c.jpg'), b'old')
        self.store.rename('images/janome', 'pictures/new/janome')  # missing folders are made
        self.assertEqual(self.read('pictures/new/janome/c.jpg'), b'old')
        self.write('images/d.jpg', b'd')
        for source, target in (
            ('images/d.jpg', 'pictures'),  # exists
            ('pictures', 'pictures/new/x'),  # into itself
            ('images/missing.jpg', 'images/x.jpg'),
            ('images/d.jpg', 'products/d.jpg'),  # protected
            ('products/p.jpg', 'images/p.jpg'),
            ('images/d.jpg', 'images/d.jpg/x'),  # parent is a file
        ):
            with self.subTest(source=source, target=target), self.assertRaises(FileManagerError):
                self.store.rename(source, target)

    def test_delete(self):
        self.store.delete('images/janome/a b.jpg')
        self.assertIsNone(self.store.kind('images/janome/a b.jpg'))
        self.write('images/janome/x.jpg', b'x')
        self.assertEqual(self.store.count_files('images'), 1)
        self.store.delete('images')
        self.assertIsNone(self.store.kind('images'))
        for path in ('', 'products', 'products/p.jpg', 'missing'):
            with self.subTest(path=path), self.assertRaises(FileManagerError):
                self.store.delete(path)

    def test_delete_symlink_keeps_its_target(self):
        os.symlink(os.path.join(self.root, 'images'), os.path.join(self.root, 'link'))
        self.store.delete('link')
        self.assertEqual(self.store.kind('images/janome/a b.jpg'), 'file')

    def test_paths_outside_root(self):
        with self.assertRaises(SuspiciousFileOperation):
            self.store.kind('../outside')
