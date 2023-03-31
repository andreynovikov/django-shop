import datetime

from django.conf import settings
from django.utils import timezone

from rest_framework import views, viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.exceptions import MethodNotAllowed
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.response import Response

from .models import Entry
from .serializers import EntrySerializer, EntryListSerializer


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
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

    def get_serializer_class(self):
        if self.action == 'list':
            return EntryListSerializer
        return EntrySerializer

    def get_queryset(self):
        return Entry.objects.filter(sites=self.request.site, status=Entry.PUBLISHED)

    def get_object(self):
        key = self.kwargs.get(self.lookup_field)
        if not key.isdigit():
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
