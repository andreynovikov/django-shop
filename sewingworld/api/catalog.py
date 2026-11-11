from django.contrib.admin.utils import lookup_spawns_duplicates
from django.contrib.postgres.search import SearchQuery, SearchRank
from django.core.exceptions import FieldDoesNotExist, FieldError, ValidationError as DjangoValidationError
from django.db.models import F
from django.http import HttpResponse
from django.shortcuts import redirect

from rest_framework import viewsets, filters, serializers
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from django_filters.fields import ChoiceIterator

from qrcode import QRCode
from qrcode.image.svg import SvgPathImage

from shop.filters import get_product_filter
from shop.models import Category, ProductKind, Product, ProductSet, Stock, Basket, Store

from sewingworld.serializers.catalog import CategoryTreeSerializer, CategorySerializer, ProductSerializer, \
    ProductListSerializer, ProductKindSerializer, ProductImagesSerializer
from sewingworld.serializers.content import StoreListSerializer
from sewingworld.serializers.integrations import IntegrationProductSerializer

from .common import BAD_PARAMETER, StandardResultsSetPagination, id_params


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
    filter_backends = [filters.OrderingFilter]
    ordering_fields = '__all__'
    filtering_fields = [f.name for f in Product._meta.get_fields()] + ['text', 'instock']
    product_filter = None

    def get_serializer_class(self):
        if self.action in ('list', 'info'):
            if self.request.query_params.get('for_xml') == 'true':
                return IntegrationProductSerializer
            return ProductListSerializer
        if self.action == 'images':
            return ProductImagesSerializer
        return ProductSerializer

    def get_serializer(self, *args, **kwargs):
        if self.action in ('list', 'info'):
            fields = self.request.query_params.get('fields')
            if fields:
                kwargs['fields'] = fields.split(',')
        return super().get_serializer(*args, **kwargs)

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action == 'list':
            queryset = queryset.filter(sites=self.request.site)

        # DISTINCT compares all the columns of a product, it is costly: only for filters that may repeat products
        distinct = False
        # A value of the wrong type, or a lookup the field lacks, fails while the filter is built
        try:
            for field, values in self.request.query_params.lists():
                if field == 'in_category':
                    categories = []
                    for category in Category.objects.filter(pk__in=values):  # unknown ones find no products
                        categories.append(category)
                        categories.extend(category.get_descendants().filter(active=True))
                    # a subquery: a join repeats the products that are in several of the categories
                    in_categories = Product.categories.through.objects.filter(category__in=categories)
                    queryset = queryset.filter(pk__in=in_categories.values('product_id'))
                    continue
                base_field = field.split('__', 1)[0]
                if base_field not in self.filtering_fields:
                    continue
                try:
                    field_type = Product._meta.get_field(field).get_internal_type()
                except FieldDoesNotExist:
                    field_type = None
                if field == 'id':
                    queryset = queryset.filter(pk__in=values)
                elif field == 'text':  # full text search
                    language = 'russian'
                    search_query = SearchQuery(values[0], config=language)
                    search_rank = SearchRank(F('fts_vector'), search_query, weights=[0.1, 0.2, 0.4, 1.0])
                    queryset = queryset.annotate(
                        rank=search_rank
                    ).filter(
                        fts_vector=search_query,
                        rank__gte=0.001
                    ).order_by(
                        '-enabled',
                        '-rank'
                    )
                    filter_fields = ['manufacturer', 'price']
                    self.product_filter = get_product_filter(self.request.query_params, queryset=queryset, fields=filter_fields, request=self.request)
                    queryset = self.product_filter.qs
                elif field_type == 'BooleanField':
                    key = '{}__exact'.format(field)
                    value = values[0].lower() in ('1', 'on', 't', 'true', 'y', 'yes')
                    queryset = queryset.filter(**{key: value})
                elif field == 'title':
                    key = '{}__icontains'.format(field)
                    queryset = queryset.filter(**{key: values[0]})
                elif field == 'instock':
                    if int(values[0]) > 0:
                        queryset = queryset.filter(num__gt=0)
                    else:
                        queryset = queryset.filter(num__exact=0)
                elif field == 'price':
                    price = values[0].split('-')  # TODO Combine with filters after upgrade
                    if len(price) == 2:
                        queryset = queryset.filter(price__gte=price[0], price__lte=price[1])
                elif field == 'categories':
                    key = '{}__pk__exact'.format(field)
                    queryset = queryset.filter(**{key: values[0]})

                    category = Category.objects.filter(pk=values[0]).first()
                    if category is not None and category.filters:
                        fields = category.filters.split(',')
                        self.product_filter = get_product_filter(self.request.query_params, queryset=queryset, fields=fields, request=self.request)
                        queryset = self.product_filter.qs
                elif field in ('kind', 'manufacturer'):  # поиск по ключу
                    if len(values) > 1:
                        key = '{}__pk__in'.format(field)
                        queryset = queryset.filter(**{key: values})
                        distinct = distinct or lookup_spawns_duplicates(Product._meta, key)
                    else:
                        key = '{}__pk__exact'.format(field)
                        queryset = queryset.filter(**{key: values[0]})
                # elif field == 'inspection':
                #     if len(values) > 1:
                #         key = '{}__pk__in'.format(field)
                #         queryset = queryset.filter(**{key: values})
                #     else:
                #         key = '{}__pk__istartswith'.format(field)
                #         queryset = queryset.filter(**{key: values[0]})
                # elif len(values) > 1:  # поиск в массиве
                #     key = '{}__in'.format(field)
                #     queryset = queryset.filter(**{key: values})
                else:  # строковый поиск
                    key = '{}__exact'.format(field)
                    queryset = queryset.filter(**{key: values[0]})
                    distinct = distinct or lookup_spawns_duplicates(Product._meta, key)
        except (ValueError, FieldError, DjangoValidationError):
            raise serializers.ValidationError({field: [BAD_PARAMETER]})

        if distinct:
            queryset = queryset.distinct()
        if self.action in ('list', 'info', 'retrieve', 'bycode'):
            queryset = self.get_serializer_class().prefetch(queryset)
        return queryset

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        # Products of the same price or title come by id, as they did when DISTINCT sorted them. Without an order
        # of their own, pages of them may repeat or skip some.
        ordering = list(queryset.query.order_by) or (list(Product._meta.ordering) if queryset.query.default_ordering else [])
        if not {'pk', 'id', '-pk', '-id'} & {item for item in ordering if isinstance(item, str)}:
            queryset = queryset.order_by(*ordering, 'pk')
        return queryset

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        if response.status_code == 200 and self.product_filter is not None:
            filters = {}
            for field in self.product_filter.form.visible_fields():
                if field.name == 'enabled':
                    continue
                filters[field.name] = {
                    'id': field.id_for_label
                }
                if hasattr(field.field, 'choices'):
                    choices = field.field.choices
                    if isinstance(choices, dict):
                        choices = list(choices.items())
                    elif isinstance(choices, ChoiceIterator):
                        choices = list(choices)
                    filters[field.name]['choices'] = choices
                if field.field.widget.attrs:
                    filters[field.name]['attrs'] = field.field.widget.attrs
            response.data['filters'] = filters
            # response.data['data'] = self.product_filter.data
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
