from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from django.contrib.flatpages.models import FlatPage

from shop.models import News, SalesAction, Advert, Store, ServiceCenter

from sewingworld.models import SiteProfile
from sewingworld.serializers.catalog import ProductListSerializer
from sewingworld.serializers.content import FlatPageListSerializer, FlatPageSerializer, NewsSerializer, \
    SalesActionSerializer, AdvertSerializer, StoreListSerializer, StoreSerializer, ServiceCenterSerializer, \
    SiteProfileSerializer

from .common import IsSuperUser, StandardResultsSetPagination, id_params


class FlatPageViewSet(viewsets.ReadOnlyModelViewSet):
    lookup_field = 'url'
    lookup_value_regex = '.*'
    ordering = ('url',)

    def get_serializer_class(self):
        if self.action == 'list':
            return FlatPageListSerializer
        return FlatPageSerializer

    def get_queryset(self):
        return FlatPage.objects.filter(sites=self.request.site)

    def get_object(self):
        # TODO: add support for authorization and template
        key = self.kwargs.get(self.lookup_field)
        self.kwargs[self.lookup_field] = '/{}/'.format(key)
        return super().get_object()


class NewsViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NewsSerializer
    queryset = News.objects.none()  # model for the API schema, get_queryset() needs a request

    def get_queryset(self):
        return News.objects.filter(sites=self.request.site, active=True)


class SalesActionViewSet(viewsets.ReadOnlyModelViewSet):
    lookup_field = 'slug'
    ordering = ('order',)
    serializer_class = SalesActionSerializer
    queryset = SalesAction.objects.none()  # model for the API schema, get_queryset() needs a request

    def get_queryset(self):
        queryset = SalesAction.objects.filter(active=True, sites=self.request.site)
        if self.action == 'list':
            queryset = queryset.filter(show_in_list=True)
        return queryset

    @action(detail=True)
    def products(self, request, slug=None):
        action = self.get_object()
        queryset = ProductListSerializer.prefetch(action.products.filter(enabled=True).order_by('-price'))
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(queryset, request, view=self)

        if page is not None:
            serializer = ProductListSerializer(page, many=True, context=self.get_serializer_context())
            return paginator.get_paginated_response(serializer.data)

        serializer = ProductListSerializer(queryset, many=True, context=self.get_serializer_context())
        return Response(serializer.data)


class AdvertViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AdvertSerializer
    queryset = Advert.objects.none()  # model for the API schema, get_queryset() needs a request

    def get_queryset(self):
        queryset = Advert.objects.filter(sites=self.request.site, active=True)
        places = self.request.query_params.getlist('place')
        if len(places) > 0:
            queryset = queryset.filter(place__in=places)
        category = id_params(self.request, 'category')
        if len(category) > 0:
            queryset = queryset.filter(categories__pk__exact=category[0])
        return queryset


class StoreViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Store.objects.none()  # model for the API schema, get_queryset() needs a request

    def get_serializer_class(self):
        if self.action == 'list':
            return StoreListSerializer
        return StoreSerializer

    def get_queryset(self):
        stores = Store.objects.filter(site=self.request.site, enabled=True).select_related('city__country').order_by('city__country__ename', 'city__name')
        if self.request.query_params.get('marketplace', None) is not None:
            stores = stores.filter(marketplace=True)
        if self.request.query_params.get('lottery', None) is not None:
            stores = stores.filter(lottery=True)
        return stores


class ServiceCenterViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ServiceCenterSerializer

    def get_queryset(self):
        return ServiceCenter.objects.filter(enabled=True).select_related('city__country').order_by('city__country__ename', 'city__name')


class SiteProfileViewSet(viewsets.ReadOnlyModelViewSet):
    lookup_field = 'site'
    lookup_value_regex = r'(:?\d+|current)'
    serializer_class = SiteProfileSerializer
    queryset = SiteProfile.objects.all()

    def get_permissions(self):
        self.permission_classes = [IsSuperUser]
        if self.action == 'retrieve':
            key = self.kwargs.get(self.lookup_field)
            if key == 'current':
                self.permission_classes = []

        return super().get_permissions()

    def get_object(self):
        key = self.kwargs.get(self.lookup_field)

        if key == 'current':
            return self.request.site.profile

        return super().get_object()
