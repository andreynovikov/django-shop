import re

from django.core import signing
from django.db import transaction

from rest_framework import viewsets, serializers, status
from rest_framework.decorators import action
from rest_framework.exceptions import MethodNotAllowed
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, extend_schema_view, inline_serializer, OpenApiParameter, OpenApiResponse

from shop.models import Product, Basket, Favorites

from sewingworld.serializers.common import validation_error_serializer
from sewingworld.serializers.shopping import BasketSerializer, BasketItemActionSerializer, FavoritesSerializer, \
    ComparisonSerializer

from .common import FORBIDDEN, NOT_FOUND, ensure_session, id_params

# Built once, drf-spectacular expects one serializer class per component name
BASKET_ITEM_ERRORS = validation_error_serializer(BasketItemActionSerializer)
COMPARISON_ERRORS = validation_error_serializer(ComparisonSerializer)
FAVORITE_ERRORS = validation_error_serializer(FavoritesSerializer)

BAD_BASKET_LINK = 'Ссылка недействительна'

BASKET_ITEM_ACTIONS = ('add_item', 'remove_item', 'update_item')
MAX_QUANTITY = 32767  # the range of BasketItem.quantity, a PositiveSmallIntegerField

PRODUCT_IDS = OpenApiResponse(response={'type': 'array', 'items': {'type': 'integer'}}, description='Product ids')


class BasketViewSet(viewsets.ModelViewSet):
    serializer_class = BasketSerializer
    queryset = Basket.objects.none()  # model for the API schema, get_queryset() needs a request

    def get_queryset(self):
        queryset = Basket.objects.filter(site=self.request.site, session_id__isnull=False, session_id=self.request.session.session_key)
        if self.action in BASKET_ITEM_ACTIONS:
            # the item actions of a basket go one at a time: its row stays locked until their transaction ends
            queryset = queryset.select_for_update()
        return queryset

    def destroy(self, request, *args, **kwargs):
        raise MethodNotAllowed(request.method)

    def update(self, request, *args, **kwargs):
        raise MethodNotAllowed(request.method)

    @extend_schema(
        request=inline_serializer('BasketRestore', fields={
            'contents': serializers.CharField(help_text="From the link: '<product id>*<quantity>', separated by commas"),
            'utm_source': serializers.CharField(required=False, allow_blank=True),
        }),
        responses={204: None},
        methods=['POST']
    )
    @action(detail=False, methods=['post'])
    def restore(self, request):
        """
        Fills a basket for the session from the link in the abandoned basket notice, which the storefront's page
        at the link's path sends here. A session that has a basket keeps it. The new basket is marked secondary,
        so it gets no notice of its own.
        """
        data = request.data if isinstance(request.data, dict) else {}
        contents = Basket.parse_link_contents(str(data.get('contents', '')))
        products = list(Product.objects.filter(pk__in=contents))
        if products:
            ensure_session(request)
            with transaction.atomic():
                basket, created = Basket.get_or_create_for_session(request.site, request.session.session_key)
                if created:
                    for product in products:
                        basket.items.create(product=product, quantity=contents[product.id])
                    basket.utm_source = re.sub(r'(?a)[^\w]', '_', str(data.get('utm_source', '')))[:20]  # ASCII only
                    basket.secondary = True
                    basket.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        request=inline_serializer('BasketClear', fields={
            'sign': serializers.CharField(help_text='Signed basket id from the link'),
        }),
        responses={
            204: None,
            400: OpenApiResponse(inline_serializer('BasketClearError', fields={
                'sign': serializers.ListField(child=serializers.CharField())
            }), description='Bad signature'),
        },
        methods=['POST']
    )
    @action(detail=False, methods=['post'])
    def clear(self, request):
        """ Deletes the basket of the link in the abandoned basket notice, whichever session it is in """
        data = request.data if isinstance(request.data, dict) else {}
        try:
            basket_id = signing.Signer().unsign(str(data.get('sign', '')))
        except signing.BadSignature:
            basket_id = None
        if basket_id is None or not basket_id.isdigit():  # the default salt may sign other values elsewhere
            raise serializers.ValidationError({'sign': [BAD_BASKET_LINK]})
        Basket.objects.filter(pk=int(basket_id)).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        request=BasketItemActionSerializer,
        responses={
            204: None,
            400: BASKET_ITEM_ERRORS,
            404: NOT_FOUND,
        },
        methods=['POST']
    )
    @action(detail=True, methods=['post'], url_path='add')
    def add_item(self, request, pk=None):
        with transaction.atomic():
            basket = self.get_object()
            serializer = BasketItemActionSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            quantity = serializer.validated_data.get('quantity', 1)
            item, created = basket.items.get_or_create(product=serializer.validated_data['product'], defaults={'quantity': quantity})
            if not created:
                item.quantity = min(item.quantity + quantity, MAX_QUANTITY)
                item.save()
            basket.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        request=BasketItemActionSerializer,
        responses={
            204: None,
            400: BASKET_ITEM_ERRORS,
            404: NOT_FOUND,
        },
        methods=['POST']
    )
    @action(detail=True, methods=['post'], url_path='remove')
    def remove_item(self, request, pk=None):
        with transaction.atomic():
            basket = self.get_object()
            serializer = BasketItemActionSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            basket.items.filter(product=serializer.validated_data['product']).delete()
            basket.save()
            if not basket.items.exists():
                basket.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        request=BasketItemActionSerializer,
        responses={
            204: None,
            400: BASKET_ITEM_ERRORS,
            404: NOT_FOUND,
        },
        methods=['POST']
    )
    @action(detail=True, methods=['post'], url_path='update')
    def update_item(self, request, pk=None):
        with transaction.atomic():
            basket = self.get_object()
            serializer = BasketItemActionSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            product = serializer.validated_data['product']
            quantity = serializer.validated_data.get('quantity')
            if quantity is None:
                basket.items.get_or_create(product=product)
            elif quantity > 0:
                basket.items.update_or_create(product=product, defaults={'quantity': quantity})
            else:
                basket.items.filter(product=product).delete()
            if not basket.items.exists():
                basket.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema_view(
    list=extend_schema(responses={200: FavoritesSerializer(many=True), 403: FORBIDDEN}),
)
class FavoritesViewSet(viewsets.ModelViewSet):
    serializer_class = FavoritesSerializer
    queryset = Favorites.objects.none()  # model for the API schema, get_queryset() needs a request
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Favorites.objects.filter(site=self.request.site, user=self.request.user)
        return queryset

    def create(self, request):
        raise MethodNotAllowed(request.method)

    def destroy(self, request, *args, **kwargs):
        raise MethodNotAllowed(request.method)

    def update(self, request, *args, **kwargs):
        raise MethodNotAllowed(request.method)

    @extend_schema(
        responses={
            204: None,
            400: FAVORITE_ERRORS,
            403: FORBIDDEN,
        },
        methods=['POST']
    )
    @action(detail=False, methods=['post'], url_path='add')
    def add_item(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        favorite, created = Favorites.objects.get_or_create(site=request.site, user=request.user, product=serializer.validated_data['product'])
        if created:
            favorite.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        responses={
            204: None,
            400: FAVORITE_ERRORS,
            403: FORBIDDEN,
        },
        methods=['POST']
    )
    @action(detail=False, methods=['post'], url_path='remove')
    def remove_item(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        favorite = Favorites.objects.filter(site=request.site, user=request.user, product=serializer.validated_data['product']).first()
        if favorite is not None:
            favorite.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ComparisonsViewSet(viewsets.ViewSet):
    @extend_schema(
        parameters=[OpenApiParameter('kind', OpenApiTypes.INT, description='Only products of this kind')],
        responses={
            200: PRODUCT_IDS,
        },
    )
    def list(self, request):
        comparison_list = request.session.get('comparison_list', None)
        kinds = id_params(request, 'kind')
        if comparison_list:
            product_ids = list(map(int, comparison_list.split(',')))
            if kinds:
                product_ids = list(Product.objects.filter(pk__in=product_ids, kind=kinds[-1]).values_list('id', flat=True))
        else:
            product_ids = []
        return Response(product_ids)

    @extend_schema(
        request=ComparisonSerializer,
        responses={
            200: PRODUCT_IDS,
            400: COMPARISON_ERRORS,
        },
        methods=['POST']
    )
    @action(detail=False, methods=['post'], url_path='add')
    def add_item(self, request):
        serializer = ComparisonSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product = serializer.validated_data['product']
        comparison_list = request.session.get('comparison_list', None)
        if comparison_list:
            product_ids = list(map(int, comparison_list.split(',')))
            if product.id not in product_ids:
                product_ids.append(product.id)
                request.session['comparison_list'] = ','.join(map(str, product_ids))
        else:
            request.session['comparison_list'] = str(product.id)
            product_ids = [product.id]
        return Response(product_ids)

    @extend_schema(
        request=ComparisonSerializer,
        responses={
            200: PRODUCT_IDS,
            400: COMPARISON_ERRORS,
        },
        methods=['POST']
    )
    @action(detail=False, methods=['post'], url_path='remove')
    def remove_item(self, request):
        serializer = ComparisonSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product_ids = []
        comparison_list = request.session.get('comparison_list', None)
        if comparison_list:
            product = serializer.validated_data['product']
            product_ids = list(filter(lambda id: id != product.id, map(int, comparison_list.split(','))))
            if product_ids:
                request.session['comparison_list'] = ','.join(map(str, product_ids))
            else:
                del request.session['comparison_list']
        return Response(product_ids)
