from django import forms
from django.contrib.admin.widgets import AdminTextareaWidget
from django.utils.safestring import mark_safe


class AutosizedTextarea(AdminTextareaWidget):
    """
    AutoSized TextArea - TextArea height dynamically grows based on user input
    https://github.com/jackmoore/autosize
    """
    def __init__(self, attrs=None):
        new_attrs = {'rows': 2}
        if attrs:
            new_attrs.update(attrs)
        super(AutosizedTextarea, self).__init__(new_attrs)

    @property
    def media(self):
        return forms.Media(js=('js/autosize.min.js',))

    def render(self, name, value, attrs=None, renderer=None):
        output = super(AutosizedTextarea, self).render(name, value, attrs, renderer)
        output += mark_safe(
            """
            <script type="text/javascript">
            django.jQuery(function() {
                var el = document.getElementById('id_%s');
                autosize(el);
                el.addEventListener('focus', function(){ autosize.update(el); });
            });
            </script>
            """ % name
        )
        return output
