import datetime

from django.conf import settings
from django.db.models import Count
from django.utils import timezone

from rest_framework import views, viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.exceptions import MethodNotAllowed
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.response import Response

from tagging.models import Tag, TaggedItem
from tagging.utils import get_tag

from .models import Entry, Category
from .serializers import EntrySerializer, EntryListSerializer, TagListSerializer, CategorySerializer


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response({
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'count': self.page.paginator.count,
            'totalPages': self.page.paginator.num_pages,
            'currentPage': self.page.number,
            'pageSize': self.get_page_size(self.request),
            'results': data
        })


class EntryViewSet(viewsets.ReadOnlyModelViewSet):
    lookup_value_regex = '.*'
    pagination_class = StandardResultsSetPagination
    filtering_fields = [f.name for f in Entry._meta.get_fields()]

    def get_serializer_class(self):
        if self.action == 'list':
            return EntryListSerializer
        return EntrySerializer

    def get_queryset(self):
        queryset = Entry.objects.filter(sites=self.request.site, status=Entry.PUBLISHED)

        for field, values in self.request.query_params.lists():
            base_field = field.split('__', 1)[0]
            if base_field not in self.filtering_fields:
                continue

            if field == 'tags':
                tag = get_tag(values[0])
                if tag is None:
                    pass  # TODO: deside what to do in this case
                queryset = TaggedItem.objects.get_by_model(queryset, tag)
            elif field == 'categories':
                queryset = queryset.filter(categories__in=values)

        return queryset

    def get_object(self):
        """
        Retrive object by pk, short link and full link
        """
        key = self.kwargs.get(self.lookup_field)
        if not key.isdigit():
            if key.isalnum():  # short link
                self.kwargs[self.lookup_field] = int(key, 36)
            else:
                try:
                    year, month, day, slug = key.split('/')
                    date = datetime.datetime.strptime('{}__{}__{}'.format(year,month,day), '%Y__%m__%d').date()
                    since = self._make_date_lookup_arg(date)
                    until = self._make_date_lookup_arg(date + datetime.timedelta(days=1))
                    lookup_kwargs = {
                        "publication_date__gte": since,
                        "publication_date__lt": until,
                        "slug": slug
                    }
                    instance = self.get_queryset().filter(**lookup_kwargs).first()
                    if instance is not None:
                        self.kwargs[self.lookup_field] = instance.pk
                except (IndexError, ValueError) as e:
                    pass  # let DRF issue the error
        return super().get_object()

    def _make_date_lookup_arg(self, value):
        value = datetime.datetime.combine(value, datetime.time.min)
        if settings.USE_TZ:
            value = timezone.make_aware(value)
        return value


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    lookup_value_regex = '.*'

    def get_serializer_class(self):
        return TagListSerializer

    def get_queryset(self):
        queryset = Entry.objects.filter(sites=self.request.site, status=Entry.PUBLISHED)
        return Tag.objects.usage_for_queryset(queryset, counts=True)


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    lookup_value_regex = '.*'

    def get_serializer_class(self):
        return CategorySerializer

    def get_queryset(self):
        return Category.objects.filter(entries__sites=self.request.site, entries__status=Entry.PUBLISHED).annotate(count=Count('entries'))

    def get_object(self):
        key = self.kwargs.get(self.lookup_field)
        if not key.isdigit():
            instance = self.get_queryset().filter(slug=key).first()
            if instance is not None:
                self.kwargs[self.lookup_field] = instance.pk
        return super().get_object()
