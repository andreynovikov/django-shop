from django.contrib.admin import AdminSite
from django.contrib.auth import get_user_model
from django.test import Client, RequestFactory, TestCase, override_settings
from django.utils import translation

from errors.admin import ErrorAdmin
from errors.models import Error

MASK = '********************'


@override_settings(ROOT_URLCONF='errors.tests.urls')
class AdminTests(TestCase):
    def setUp(self):
        Client(raise_request_exception=False).get('/boom/?password=hunter2')
        self.error = Error.objects.get()
        self.model_admin = ErrorAdmin(Error, AdminSite())

    def get(self, view, *args):
        request = RequestFactory().get('/admin/errors/error/')
        request.user = get_user_model()(is_active=True, is_staff=True, is_superuser=True)
        return view(request, *args).render()

    def test_pages(self):
        self.assertContains(self.get(self.model_admin.changelist_view), 'errors/tests/urls.py in boom')
        page = self.get(self.model_admin.change_view, str(self.error.pk))
        self.assertContains(page, '<details open')
        self.assertContains(page, 'raise ValueError')
        self.assertContains(page, MASK)
        self.assertNotContains(page, 'hunter2')

    def test_translations(self):
        for language, texts in (
            ('en', ['Kind', 'Frequency, per day', 'Variable', 'line', 'ValueError in GET boom']),
            ('ru', ['Вид', 'Частота, в день', 'Переменная', 'строка', 'ValueError в GET boom']),
        ):
            with translation.override(language):
                page = self.get(self.model_admin.change_view, str(self.error.pk))
            for text in texts:
                self.assertContains(page, text, msg_prefix=language)
