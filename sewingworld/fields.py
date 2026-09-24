from django import forms
from django.apps import apps


class ConstanceModelChoiceField(forms.ModelChoiceField):
    def __init__(self, *args, **kwargs):
        model_string = kwargs.pop('model_string', None)
        model_filters = kwargs.pop('model_filters', None)
        if model_string:
            model_class = apps.get_model(model_string)
            if model_filters:
                kwargs['queryset'] = model_class.objects.filter(**model_filters)
            else:
                kwargs['queryset'] = model_class.objects.all()
        super().__init__(*args, **kwargs)

    def prepare_value(self, value):
        """
        Ensures the admin form renders the choice correctly.
        If a model instance is passed, extract its primary key.
        """
        if hasattr(value, 'pk'):
            return value.pk
        return value

    def to_python(self, value):
        """
        Executed when saving the form. Instead of returning the full
        model instance object, we return just the ID (integer/string)
        so Constance can easily serialize it to JSON.
        """
        instance = super().to_python(value)
        if instance:
            return instance.pk
        return None
