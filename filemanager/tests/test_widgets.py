from django.test import SimpleTestCase, override_settings
from django.utils import translation

from filemanager.widgets import HTMLTextarea

urlpatterns = []  # a URLconf without the admin


@override_settings(ROOT_URLCONF='filemanager.tests.urls')
class HTMLTextareaTests(SimpleTestCase):
    def test_render(self):
        widget = HTMLTextarea(attrs={'rows': 5, 'style': 'width: 95%'})
        with translation.override('en'):
            html = widget.render('content', '<p>Hi</p>', attrs={'id': 'id_content'})
        self.assertInHTML(
            '<textarea name="content" id="id_content" rows="5" cols="40" class="vLargeTextField" style="width: 95%" data-autosize>'
            '&lt;p&gt;Hi&lt;/p&gt;</textarea>',
            html,
        )
        self.assertInHTML(
            '<button type="button" class="button filemanager-insert-file" data-url="/admin/filemanager/file/">Insert file</button>',
            html,
        )
        self.assertEqual(widget.media._js, ['filemanager/html_textarea.js'])

    @override_settings(ROOT_URLCONF=__name__)
    def test_no_button_without_admin(self):
        html = HTMLTextarea().render('content', '', attrs={'id': 'id_content'})
        self.assertIn('data-autosize', html)
        self.assertNotIn('filemanager-insert-file', html)
