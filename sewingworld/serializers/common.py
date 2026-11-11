from collections import OrderedDict

from rest_framework import serializers

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field, inline_serializer


@extend_schema_field(OpenApiTypes.NUMBER)
class NumberReadOnlyField(serializers.ReadOnlyField):
    # A Decimal or int property, rendered as a JSON number. The API schema can't tell the type of a property.
    pass


@extend_schema_field(OpenApiTypes.INT)
class IntegerReadOnlyField(serializers.ReadOnlyField):
    # An int property, see NumberReadOnlyField
    pass


class ErrorDetailSerializer(serializers.Serializer):
    # Body of DRF exceptions in the API schema, e.g. 403 Forbidden or 404 Not Found
    detail = serializers.CharField()


def validation_error_serializer(serializer_class):
    # Body of validation errors in the API schema: messages for each invalid field,
    # and messages of validate() under non_field_errors
    names = [name for name, field in serializer_class().fields.items() if not field.read_only]
    return inline_serializer(
        name=serializer_class.__name__.removesuffix('Serializer') + 'ValidationError',
        fields={
            name: serializers.ListField(child=serializers.CharField(), required=False)
            for name in [*names, 'non_field_errors']
        },
    )


class NonNullModelSerializer(serializers.ModelSerializer):
    def to_representation(self, instance):
        def keep(value):
            return not (value is None or (isinstance(value, str) and len(value) == 0) or (hasattr(value, '__len__') and len(value) == 0))

        result = super().to_representation(instance)
        return OrderedDict([(key, result[key]) for key in result if keep(result[key])])


class DynamicFieldsModelSerializer(NonNullModelSerializer):
    def __init__(self, *args, **kwargs):
        fields = kwargs.pop('fields', None)
        super().__init__(*args, **kwargs)

        if fields is not None:
            # Drop any fields that are not specified in the `fields` argument.
            allowed = set(fields)
            existing = set(self.fields)
            for field_name in existing - allowed:
                self.fields.pop(field_name)
