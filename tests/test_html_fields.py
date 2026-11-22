"""
The admin fields whose HTML the storefronts render with dangerouslySetInnerHTML get the file manager's HTMLTextarea,
and only those. See settings.py on how to run.
"""
from django.contrib.admin.sites import site as admin_site
from django.contrib.auth import get_user_model
from django.contrib.flatpages.models import FlatPage
from django.test import RequestFactory, TestCase

from blog.models import Entry
from filemanager.widgets import HTMLTextarea
from shop.models import Advert, Category, News, Product, SalesAction, Store

HTML_FIELDS = {
    Product: {'spec', 'descr', 'shortdescr', 'manuals', 'stitches', 'complect', 'dealertxt'},
    Category: {'description'},
    SalesAction: {'brief', 'description'},
    Advert: {'content'},
    News: {'content'},
    Store: {'description'},
    FlatPage: {'content'},
    Entry: {'content'},
}


class HTMLFieldTests(TestCase):
    def test_widgets(self):
        request = RequestFactory().get('/admin/')
        request.user = get_user_model()(is_active=True, is_staff=True, is_superuser=True)
        for model, expected in HTML_FIELDS.items():
            form = admin_site._registry[model].get_form(request)
            with self.subTest(model=model.__name__):
                found = {name for name, field in form.base_fields.items() if isinstance(field.widget, HTMLTextarea)}
                self.assertEqual(found, expected)
