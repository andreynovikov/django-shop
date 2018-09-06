import uuid

import json

from django.core.urlresolvers import reverse
from django.contrib.admin import widgets
from django.contrib.staticfiles.storage import staticfiles_storage
from django.forms import Media
from django.forms.widgets import TextInput
from django.utils.safestring import mark_safe

from tagging.models import Tag


BOOTSTRAP_INPUT_TEMPLATE = {
    2: """
       <div id="%(id)s_wrapper" class="input-append">
           %(rendered_widget)s
           <a class="button add-on related-widget-wrapper-link" href="%(popup)s?_popup=1"><i class="icon-%(glyphicon)s"></i></a>
       </div>
       <script>
           $( "#%(id)s_wrapper a" ).click(function() {
               var phone = $( "#%(id)s" ).val();
               if (! /^\+\d+$/.test(phone))
                   return false;
               var href = $(this).attr("href");
               $(this).attr("href", href.replace(/\+\d+/, phone));
           });
       </script>
       """,
    3: """
       <div id="%(id)s_wrapper" class="input-group">
           %(rendered_widget)s
           <a class="button input-group-addon related-widget-wrapper-link" href="%(popup)s?_popup=1"><span class="glyphicon %(glyphicon)s"></span></a>
       </div>
       <script>
           $( "#%(id)s_wrapper a" ).click(function() {
              var href = $(this).attr("href");
              $(this).attr("href", href.replace(/\+\d+/, $( "#%(id)s" ).val()));
           });
       </script>
       """
    }

class PhoneWidget(TextInput):
    def __init__(self, attrs=None, bootstrap_version=None):
        if bootstrap_version in [2,3]:
            self.bootstrap_version = bootstrap_version
        else:
            # default 2 to mantain support to old implemetation of django-datetime-widget
            self.bootstrap_version = 2

        self.glyphicon = 'envelope'

        super(PhoneWidget, self).__init__(attrs)

    def render(self, name, value, attrs=None):
        final_attrs = self.build_attrs(attrs)
        rendered_widget = super(PhoneWidget, self).render(name, value, final_attrs)

        # Use provided id or generate hex to avoid collisions in document
        id = final_attrs.get('id', uuid.uuid4().hex)

        return mark_safe(
            BOOTSTRAP_INPUT_TEMPLATE[self.bootstrap_version]
                % dict(
                    id=id,
                    rendered_widget=rendered_widget,
                    glyphicon=self.glyphicon,
                    popup=reverse('admin:shop_order_send_sms', args=['+0'])
                    )
        )


"""Widgets from Zinnia admin"""

class TagAutoComplete(widgets.AdminTextInputWidget):
    """
    Tag widget with autocompletion based on select2.
    """

    def get_tags(self):
        """
        Returns the list of tags to auto-complete.
        """
        return [tag.name for tag in
                Tag.objects.all()]
        #        Tag.objects.usage_for_model(Entry)]

    def render(self, name, value, attrs=None, renderer=None):
        """
        Render the default widget and initialize select2.
        """
        output = [super(TagAutoComplete, self).render(name, value, attrs)]
        output.append('<script type="text/javascript">')
        output.append('(function($) {')
        output.append('  $(document).ready(function() {')
        output.append('    $("#id_%s").select2({' % name)
        output.append('       width: "element",')
        output.append('       maximumInputLength: 50,')
        output.append('       tokenSeparators: [",", " "],')
        output.append('       tags: %s' % json.dumps(self.get_tags()))
        output.append('     });')
        output.append('    });')
        output.append('}(django.jQuery));')
        output.append('</script>')
        return mark_safe('\n'.join(output))

    @property
    def media(self):
        """
        TagAutoComplete's Media.
        """
        def static(path):
            return staticfiles_storage.url(
                'zinnia/admin/select2/%s' % path)
        return Media(
            css={'all': (static('css/select2.css'),)},
            js=(static('js/select2.js'),)
        )
