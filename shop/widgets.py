import uuid

from django.core.urlresolvers import reverse
from django.forms.widgets import TextInput
from django.utils.safestring import mark_safe

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
