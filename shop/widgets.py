import uuid

import json

from django import forms
from django.urls import reverse
from django.contrib.admin import widgets
from django.contrib.staticfiles.storage import staticfiles_storage
from django.forms.utils import flatatt
from django.forms.widgets import Widget, TextInput
from django.utils.safestring import mark_safe
from django.utils.encoding import force_text
from django.utils.translation import get_language
from django.utils.html import format_html, escape
from django.conf import settings

from tagging.models import Tag


BOOTSTRAP_INPUT_TEMPLATE = {
    2: """
       %(rendered_widget)s
       <a id="%(id)s_link" class="button related-widget-wrapper-link" style="display: inline-block" href="%(popup)s?_popup=1"><i class="fas fa-%(glyphicon)s"></i></a>
       <script>
           (function($) {
               $("#%(id)s_link").click(function() {
                   var phone = $( "#%(id)s" ).val();
                   if (! /^\+\d+$/.test(phone))
                       return false;
                   var href = $(this).attr("href");
                   $(this).attr("href", href.replace(/\+\d+/, phone));
               });
           }(django.jQuery));
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

    def render(self, name, value, attrs=None, renderer=None):
        final_attrs = self.build_attrs(attrs)
        rendered_widget = super(PhoneWidget, self).render(name, value, final_attrs, renderer)

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


class TagAutoComplete(widgets.AdminTextInputWidget):
    """
    Tag widget with autocompletion based on select2.
    """
    def __init__(self, *args, **kwargs):
        self.model = kwargs.pop('model', None)
        super().__init__(*args, **kwargs)

    def get_tags(self):
        """
        Returns the list of tags to auto-complete.
        """
        if self.model is None:
            return [tag.name for tag in Tag.objects.all()]
        else:
            return [tag.name for tag in Tag.objects.usage_for_model(self.model)]

    def render(self, name, value, attrs=None, renderer=None):
        """
        Render the default widget and initialize select2.
        https://jsfiddle.net/lingceng/h5baz3bo/13/
        """
        output = [super(TagAutoComplete, self).render(name, value, attrs, renderer)]
        output.append('''
            <script type="text/javascript">
            (function($) {{
                function select2InputTags(queryStr) {{
                    var $input = $(queryStr);
                    var $select = $('<select class="'+ $input.attr('class') + '" multiple="multiple"><select>');
                    if ($input.val() != "") {{
                        $input.val().split(',').forEach(function(item) {{
                            $select.append('<option value="' + item + '" selected="selected">' + item + '</option>');
                        }});
                    }}
                    $select.insertAfter($input);
                    $input.hide();
                    $select.change(function() {{
                        $input.val($select.val().join(","));
                    }});
                    return $select;
                }}

                $(document).ready(function() {{
                    select2InputTags("#id_{0}").select2({{
                        width: "element",
                        maximumInputLength: {1},
                        tokenSeparators: [",", "|"],
                        multiple: "multiple",
                        tags: true,
                        data: {2}
                    }});
                }});
            }}(django.jQuery));
            </script>'''.format(name, self.attrs.get('maxlength', '50'), json.dumps(self.get_tags())))
        return mark_safe('\n'.join(output))

    @property
    def media(self):
        extra = '' if settings.DEBUG else '.min'
        return forms.Media(
            js=(
                'admin/js/vendor/jquery/jquery%s.js' % extra,
                'admin/js/vendor/select2/select2.full%s.js' % extra,
            ),
            css={
                'screen': (
                    'admin/css/vendor/select2/select2%s.css' % extra,
                    #'admin/css/autocomplete.css',
                ),
            },
        )

    """
    @property
    def media(self):
        def static(path):
            return staticfiles_storage.url('zinnia/admin/select2/%s' % path)

        return forms.Media(
            css = {'all': (static('css/select2.css'),)},
            js = (
                'admin/js/jquery.init.js',
                static('js/select2.js'),
                )
        )
    """


class StockInlineForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['supplier'].widget = ReadOnlyInput(self.instance.supplier)
            self.fields['quantity'].widget = ReadOnlyInput(self.instance.quantity)


class ReadOnlyInput(Widget):
    def __init__(self, value, attrs=None):
        self.value = value
        super().__init__(attrs)

    def render(self, name, value, attrs=None, renderer=None):
        if value is None:
            value = ''
        final_attrs = self.build_attrs(attrs, extra_attrs={'name': name, 'value': value, 'type': 'hidden'})
        return mark_safe('<input{} />{}'.format(flatatt(final_attrs), self.value))


class OrderItemProductLink(Widget):
    def __init__(self, obj, attrs=None):
        self.object = obj
        super().__init__(attrs)

    def render(self, name, value, attrs=None, renderer=None):
        final_attrs = self.build_attrs(attrs, extra_attrs={'name': name, 'value': value, 'type': 'hidden'})
        return format_html(
            '<p><a href="{}" target="_blank" style="margin-right: 8px"><i class="fas fa-external-link-alt"></i></a>' + \
            '<input{} /><a href="{}?_popup=1" class="related-widget-wrapper-link">{}</a>' + \
                ' <a href="{}?_popup=1" class="related-widget-wrapper-link" title="Гарантийный талон"><i class="fas fa-envelope-open-text"></i></a>' + \
                '&nbsp;<span class="tiny">{}</span></p>', self.object.product.get_absolute_url(), flatatt(final_attrs),
            reverse('admin:shop_product_stock', args=[self.object.product.id]), str(self.object.product),
            reverse('admin:print-warranty-card', args=[self.object.order.id, self.object.pk]), self.object.serial_number)


class DisablePluralText(forms.TextInput):
    def __init__(self, obj, attrs=None):
        self.object = obj
        super().__init__(attrs)

    def render(self, name, value, attrs=None, renderer=None):
        if value is None:
            value = ''
        final_attrs = self.build_attrs(attrs, extra_attrs={'type': self.input_type, 'name': name, **self.attrs})
        if value != '':
            final_attrs['value'] = force_text(self.format_value(value))
        if self.object.total > 0:
            return mark_safe('<input{0} readonly="readonly" />'.format(flatatt(final_attrs)))
        else:
            return mark_safe('<input{0} />'.format(flatatt(final_attrs)))


class OrderItemTotalText(forms.TextInput):
    def __init__(self, obj, attrs=None):
        self.object = obj
        super().__init__(attrs)

    def render(self, name, value, attrs=None, renderer=None):
        if value is None:
            value = ''
        final_attrs = self.build_attrs(attrs, extra_attrs={'type': self.input_type, 'name': name, **self.attrs})
        if value != '':
            final_attrs['value'] = force_text(self.format_value(value))
        if self.object.total > 0:
            return mark_safe('<input{0} />'.format(flatatt(final_attrs)))
        else:
            final_attrs['type'] = 'hidden'
            return mark_safe('<p><input{0} />{1}<span style="color: grey">\u20BD</span></p>'.format(flatatt(final_attrs), self.object.quantity * self.object.cost))


class ListTextWidget(forms.TextInput):
    def __init__(self, data_list, *args, **kwargs):
        super(ListTextWidget, self).__init__(*args, **kwargs)
        self._list = data_list

    def render(self, name, value, attrs=None, renderer=None):
        _id = attrs.get('id', uuid.uuid4().hex)
        attrs.update({'list':'list__%s' % _id})
        text_html = super(ListTextWidget, self).render(name, value, attrs=attrs)
        data_list = '<datalist id="list__%s">' % _id
        for item in self._list:
            data_list += '<option value="%s">' % escape(item)
        data_list += '</datalist>'
        return (text_html + data_list)
