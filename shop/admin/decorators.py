from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe

"""
https://medium.com/@hakibenita/things-you-must-know-about-django-admin-as-your-app-gets-bigger-6be0b0ee9614
"""


def admin_changelist_url(model):
    app_label = model._meta.app_label
    model_name = model.__name__.lower()
    return reverse('admin:{}_{}_changelist'.format(app_label, model_name))


def admin_changelist_link(attr, short_description, empty_description="-", model=None, query_string=None):
    """Decorator used for rendering a link to the list display of
    a related model in the admin detail page.

    attr (str):
        Name of the related field.
    short_description (str):
        Field display name.
    empty_description (str):
        Value to display if the related field is None.
    query_string (function):
        Optional callback for adding a query string to the link.
        Receives the object and should return a query string.

    The wrapped method receives the related object and
    should return the link text.

    Usage:
        @admin_changelist_link('credit_card', _('Credit Card'))
        def credit_card_link(self, credit_card):
            return credit_card.name
    """
    def wrap(func):
        def field_func(self, obj):
            if model is None:
                related_obj = getattr(obj, attr)
                if related_obj is None:
                    return empty_description
                url = admin_changelist_url(related_obj.model)
                title = func(self, related_obj)
            else:
                url = admin_changelist_url(model)
                title = func(self, None)
            if query_string:
                url += '?' + query_string(obj)
            return format_html('<a href="{}">{}</a>', url, mark_safe(title))
        field_func.short_description = short_description
        field_func.allow_tags = True
        return field_func
    return wrap
