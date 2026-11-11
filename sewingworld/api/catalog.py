from django.http import HttpResponse
from django.shortcuts import redirect

from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter

from qrcode import QRCode
from qrcode.image.svg import SvgPathImage

from shop.models import Category, ProductKind, Product, ProductSet, Stock, Basket, Store

from sewingworld.filters import ProductFilterSet
from sewingworld.serializers.catalog import CategoryTreeSerializer, CategorySerializer, ProductSerializer, \
    ProductListSerializer, ProductKindSerializer, ProductImagesSerializer
from sewingworld.serializers.content import StoreListSerializer
from sewingworld.serializers.integrations import IntegrationProductSerializer

from .common import FilterBackend, StandardResultsSetPagination, id_params


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    lookup_value_regex = '.*'

    def get_serializer_class(self):
        if self.action == 'list':
            return CategoryTreeSerializer
        return CategorySerializer

    def get_queryset(self):
        if self.action == 'list':
            root_category = self.request.site.profile.root_category
            queryset = root_category.get_active_children()
            feed = self.request.query_params.get('feed')
            if feed is not None:
                value = feed in ('1', 'on', 't', 'true', 'y', 'yes')
                queryset = queryset.filter(feed=value)
            return queryset
        return Category.objects.filter(active=True)

    def get_object(self):
        key = self.kwargs.get(self.lookup_field)

        if not key.isdigit():
            root_category = self.request.site.profile.root_category
            # instance select taken from mptt_urls
            instance = None
            path = key  # path = '{}/'.format(key)  # we add trailing slash to conform .get_path() from mptt_urls
            try:
                instance_slug = path.split('/')[-1]  # [-2]  # slug of the instance
                candidates = Category.objects.filter(slug=instance_slug)  # candidates to be the instance
                for candidate in candidates:
                    # here we compare each candidate's path to the path passed to this view
                    if candidate.get_api_path() == path:
                        if root_category != candidate.get_root():
                            continue
                        instance = candidate
                        break
                if instance:
                    self.kwargs[self.lookup_field] = instance.pk
            except IndexError:
                pass  # let DRF issue the error
        return super().get_object()


class ProductKindViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ProductKindSerializer

    def get_queryset(self):
        queryset = ProductKind.objects.all()
        products = id_params(self.request, 'product')
        if len(products) > 0:
            queryset = queryset.filter(product__in=products)
        return queryset.distinct()


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    lookup_value_regex = '[^/]+'
    queryset = Product.objects.all()
    pagination_class = StandardResultsSetPagination
    filter_backends = [FilterBackend, filters.OrderingFilter]
    filterset_class = ProductFilterSet
    filterset = None  # see FilterBackend
    ordering_fields = '__all__'

    def get_serializer_class(self):
        if self.action in ('list', 'info'):
            if self.request.query_params.get('for_xml') == 'true':
                return IntegrationProductSerializer
            return ProductListSerializer
        if self.action == 'images':
            return ProductImagesSerializer
        return ProductSerializer

    def requested_fields(self):
        """
        The fields of the products that the list or a product's entry in it asks for, fields=id,code, or None for
        all of them. Feeds for integrations always have all of theirs.
        """
        fields = self.request.query_params.get('fields')
        if fields and self.action in ('list', 'info') and self.get_serializer_class() is ProductListSerializer:
            return fields.split(',')
        return None

    def get_serializer(self, *args, **kwargs):
        fields = self.requested_fields()
        if fields is not None:
            kwargs['fields'] = fields
        return super().get_serializer(*args, **kwargs)

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action == 'list':
            queryset = queryset.filter(sites=self.request.site)
        if self.action in ('list', 'info', 'retrieve', 'bycode'):
            fields = self.requested_fields()
            if fields is not None:
                queryset = ProductListSerializer.prefetch(queryset, fields)
            else:
                queryset = self.get_serializer_class().prefetch(queryset)
        return queryset

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        # Products of the same price or title come by id: without an order of their own, pages of them may repeat
        # or skip some.
        ordering = list(queryset.query.order_by) or (list(Product._meta.ordering) if queryset.query.default_ordering else [])
        if not {'pk', 'id', '-pk', '-id'} & {item for item in ordering if isinstance(item, str)}:
            queryset = queryset.order_by(*ordering, 'pk')
        return queryset

    @extend_schema(parameters=[
        OpenApiParameter('fields', str, description='Fields of the products to bring, separated by commas'),
        OpenApiParameter('ta', OpenApiTypes.INT, description='With any value, titles of the products for typeahead'),
        OpenApiParameter('for_xml', bool, description='Products as feeds of the integrations need them'),
    ])
    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        # titles for typeahead need no facets
        if self.filterset is not None and request.query_params.get('ta') is None:
            facets = self.filterset.facets()
            if facets:
                response.data['filters'] = facets
        return response

    @action(detail=False)
    def fields(self, request):
        return Response({f.name: f.verbose_name.capitalize() for f in Product._meta.get_fields() if hasattr(f, 'verbose_name')})

    @action(detail=True)
    def bycode(self, request, pk=None):
        product = self.get_queryset().filter(code=pk).first()
        if product is None:
            raise NotFound()
        return Response(self.get_serializer(product, context=self.get_serializer_context()).data)

    @action(detail=True)
    def info(self, request, pk=None):
        product = self.get_object()
        return Response(self.get_serializer(product, context=self.get_serializer_context()).data)

    @action(detail=True)
    def images(self, request, pk=None):
        product = self.get_object()
        return Response(self.get_serializer(product.images, context=self.get_serializer_context()).data)

    @action(detail=True, permission_classes=[IsAuthenticated])
    def price(self, request, pk=None):
        product = self.get_object()
        product_price = product.site_price(request.site)
        user = request.user
        return Response({
            'user': user.pk,
            'user_discount': user.discount,
            'price': product_price,
            'cost': Basket.product_cost_for_user(request.site, product, product_price, user)
        })

    @action(detail=True)
    def stock(self, request, pk=None):
        product = self.get_object()
        parts = list(ProductSet.objects.filter(declaration=product))
        stores = Store.objects.filter(enabled=True).select_related('city__country').order_by('city__country__ename', 'city__name')
        # what each supplier has of the product, or of each part of a set, read at once
        stocks = {
            (stock.product_id, stock.supplier_id): stock.quantity + stock.correction
            for stock in Stock.objects.filter(product__in=[item.constituent_id for item in parts] if parts else [product.pk])
        }
        if not parts:  # stores of the suppliers that have it
            stores = stores.filter(supplier__in=[supplier for _, supplier in stocks])
        results = []
        for store in stores:
            if not parts:
                quantity = stocks[product.pk, store.supplier_id]
            else:
                quantity = 32767
                for item in parts:
                    q = stocks.get((item.constituent_id, store.supplier_id))
                    if q is None:
                        q = 0.0
                    elif item.quantity > 1:
                        q = int(q / item.quantity)
                    if q < quantity:
                        quantity = q
            if quantity > 0.0:
                results.append(store)
        return Response(StoreListSerializer(results, many=True, context=self.get_serializer_context()).data)

    @action(detail=True)
    def video(self, request, pk=None):
        product = self.get_queryset().filter(code=pk).first()
        if product is None or not product.video_url:
            raise NotFound()
        return redirect(product.video_url)

    @action(detail=True, url_path='video/qr')
    def video_qr(self, request, pk=None):
        product = self.get_object()
        qr = QRCode(border=0, image_factory=SvgPathImage)
        qr.add_data('https://www.sewing-world.ru/products/{}/video/'.format(product.code))
        img = qr.make_image()
        return HttpResponse(img.to_string(encoding='unicode').encode(), content_type='image/svg+xml')
