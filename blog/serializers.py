from collections import OrderedDict

from django.contrib.auth import get_user_model

from rest_framework import serializers

from tagging.utils import parse_tag_input

from sewingworld.serializers import UserListSerializer

from .models import Entry, Category


class NonNullModelSerializer(serializers.ModelSerializer):
    def to_representation(self, instance):
        def keep(value):
            return not (value is None or (isinstance(value, str) and len(value) == 0) or (hasattr(value, '__len__') and len(value) == 0))

        result = super().to_representation(instance)
        return OrderedDict([(key, result[key]) for key in result if keep(result[key])])


class BaseEntrySerializer(NonNullModelSerializer):
    author = UserListSerializer()
    urls = serializers.SerializerMethodField()
    tags = serializers.SerializerMethodField()

    def get_urls(self, obj):
        return {
            'canonical': obj.get_absolute_url(),
            'short': obj.short_url
        }

    def get_tags(self, obj):
        return parse_tag_input(obj.tags)


class EntryNavSerializer(BaseEntrySerializer):
    class Meta:
        model = Entry
        fields = ('title', 'urls', 'author')


class EntryListSerializer(BaseEntrySerializer):
    content = serializers.SerializerMethodField()

    class Meta:
        model = Entry
        exclude = ('sites', 'status')

    def get_content(self, obj):
        preview = obj.html_preview
        return {
            'preview': preview.preview,
            'total_words': preview.total_words,
            'remaining_words': preview.remaining_words,
            'remaining_percent': int(preview.remaining_percent)
        }


class EntrySerializer(BaseEntrySerializer):
    navigation = serializers.SerializerMethodField()

    class Meta:
        model = Entry
        exclude = ('sites', 'status')

    def get_navigation(self, obj):
        request = self.context.get('request')
        entries = list(Entry.objects.filter(sites=request.site, status=Entry.PUBLISHED).values_list('id', flat=True))
        index = entries.index(obj.pk)
        try:
            entry = Entry.objects.get(pk=entries[index + 1])
            _previous = EntryNavSerializer(entry, context=self.context).data
        except IndexError:
            _previous = None
        if index:
            entry = Entry.objects.get(pk=entries[index - 1])
            _next = EntryNavSerializer(entry, context=self.context).data
        else:
            _next = None
        return {
            'previous': _previous,
            'next': _next
        }


class TagListSerializer(serializers.Serializer):
    name = serializers.CharField()
    count = serializers.IntegerField()


class CategorySerializer(NonNullModelSerializer):
    count = serializers.IntegerField()

    class Meta:
        model = Category
        exclude = ('description',)
