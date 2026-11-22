from django.contrib.admin.widgets import AdminTextareaWidget
from django.urls import NoReverseMatch, reverse


class HTMLTextarea(AdminTextareaWidget):
    """
    A text area for HTML that grows with its text. Its "Insert file" button opens the file browser of the admin site
    in a popup, and puts the chosen file into the text at the cursor as <img>, <video> or <a>.

    The button is left out where the admin site's URLs aren't installed. The browser checks the user's permissions.
    """
    template_name = 'filemanager/widgets/html_textarea.html'

    class Media:
        js = ['filemanager/html_textarea.js']

    def __init__(self, attrs=None, admin_site='admin'):
        super().__init__({'rows': 3, **(attrs or {})})
        self.admin_site = admin_site

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        try:
            context['widget']['browse_url'] = reverse(f'{self.admin_site}:filemanager_file_changelist')
        except NoReverseMatch:
            pass
        return context
