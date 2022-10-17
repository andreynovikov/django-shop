import logging
from random import randint
from urllib.parse import urlparse

from django.contrib.auth import get_user_model, login, logout
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator

from rest_framework import generics, views, viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.response import Response

from rest_framework_simplejwt.tokens import RefreshToken

from django.contrib.flatpages.models import FlatPage

from shop.filters import get_product_filter
from shop.models import Category, Product, Basket, BasketItem, ShopUser, ShopUserManager
from shop.tasks import send_password

from .serializers import CategoryTreeSerializer, CategorySerializer, ProductSerializer, ProductListSerializer, \
    BasketSerializer, BasketItemActionSerializer, \
    UserSerializer, AnonymousUserSerializer, LoginSerializer, \
    FlatPageListSerializer, FlatPageSerializer


logger = logging.getLogger("django")


class IsSuperUser(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_superuser


class IsSelf(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user:
            if request.user.is_superuser:
                return True
            else:
                return obj.pk == request.user.pk
        else:
            return False


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 1000

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


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    lookup_value_regex = '.*'

    def get_serializer_class(self):
        if self.action == 'list':
            return CategoryTreeSerializer
        return CategorySerializer

    def get_queryset(self):
        if self.action == 'list':
            return Category.objects.get(slug='sewing.world').get_active_children()  # TODO: remove hard coded root
        return Category.objects.filter(active=True)

    def get_object(self):
        key = self.kwargs.get(self.lookup_field)

        if not key.isdigit():
            # instance select taken from mptt_urls
            instance = None
            path = '{}/'.format(key)  # we add trailing slash to conform .get_path() from mptt_urls
            try:
                instance_slug = path.split('/')[-2]  # slug of the instance
                candidates = Category.objects.filter(slug=instance_slug)  # candidates to be the instance
                for candidate in candidates:
                    # here we compare each candidate's path to the path passed to this view
                    if candidate.get_path() == path:
                        instance = candidate
                        break
                if instance:
                    self.kwargs[self.lookup_field] = instance.pk
            except IndexError:
                pass  # let DRF issue the error
        return super().get_object()


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ('id', 'code', 'article', 'title', 'price')
    filtering_fields = [f.name for f in Product._meta.get_fields()]
    ordering = ('code',)
    product_filter = None

    def get_serializer_class(self):
        if self.action == 'list':
            return ProductListSerializer
        return ProductSerializer

    def get_queryset(self):
        queryset = Product.objects.filter(enabled=True)

        for field, values in self.request.query_params.lists():
            base_field = field.split('__', 1)[0]
            if base_field not in self.filtering_fields:
                continue
            if field in ('show_on_sw', 'gift', 'recomended', 'firstpage'):
                key = '{}__exact'.format(field)
                queryset = queryset.filter(**{key: int(values[0])})
            elif field == 'categories':
                key = '{}__pk__exact'.format(field)
                queryset = queryset.filter(**{key: values[0]})

                category = Category.objects.get(pk=values[0])
                if category.filters:
                    fields = category.filters.split(',')
                    self.product_filter = get_product_filter(self.request.query_params, queryset=queryset, fields=fields, request=self.request)
                    queryset = self.product_filter.qs
            # elif field == 'inspection':
            #     if len(values) > 1:
            #         key = '{}__pk__in'.format(field)
            #         queryset = queryset.filter(**{key: values})
            #     else:
            #         key = '{}__pk__istartswith'.format(field)
            #         queryset = queryset.filter(**{key: values[0]})
            # elif field in ('account__units', 'inspection__breach'):  # поиск по ключу
            #     if len(values) > 1:
            #         key = '{}__pk__in'.format(field)
            #         queryset = queryset.filter(**{key: values})
            #     else:
            #         key = '{}__pk__exact'.format(field)
            #         queryset = queryset.filter(**{key: values[0]})
            # elif len(values) > 1:  # поиск в массиве
            #     key = '{}__in'.format(field)
            #     queryset = queryset.filter(**{key: values})
            # else:  # строковый поиск
            #     key = '{}__exact'.format(field)
            #     queryset = queryset.filter(**{key: values[0]})

        return queryset.distinct()

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
                    filters[field.name]['choices'] = field.field.choices
                if field.field.widget.attrs:
                    filters[field.name]['attrs'] = field.field.widget.attrs
            response.data['filters'] = filters
            # response.data['data'] = self.product_filter.data
        return response

    @action(detail=False)
    def fields(self, request):
        return Response({f.name: f.verbose_name for f in Product._meta.get_fields() if hasattr(f, 'verbose_name')})

    @action(detail=True, permission_classes=[IsAuthenticated])
    def price(self, request, pk=None):
        product = self.get_object()
        user = request.user
        return Response({
            'user': user.pk,
            'user_discount': user.discount,
            'price': product.price,
            'cost': Basket.product_cost_for_user(product, user)
        })


"""
class ViolationModelPermission(AccountsModelPermission):
    def has_object_permission(self, request, view, obj):
        model_permission = super().has_object_permission(request, view, obj)
        if request.method in SAFE_METHODS or request.user.is_staff or request.user.has_perm('accounts.audit_violations'):
            return model_permission

        # дополнительно проверяем операторов на принадлежность к ДО
        oparated_units = list(Operator.objects.filter(user=request.user).values_list('units', flat=True).distinct())
        violation_units = list(obj.account.units.values_list('id', flat=True).distinct())
        return not set(oparated_units).isdisjoint(violation_units)  # https://stackoverflow.com/a/17735466
"""


class BasketViewSet(viewsets.ModelViewSet):
    serializer_class = BasketSerializer

    def get_queryset(self):
        queryset = Basket.objects.filter(session_id=self.request.session.session_key)
        return queryset

    @action(detail=True, methods=['post'], url_path='add')
    def add_item(self, request, pk=None):
        # TODO: check that basket belongs to current user
        basket = self.get_object()
        serializer = BasketItemActionSerializer(data=request.data)
        if serializer.is_valid():
            item, created = basket.items.get_or_create(product=serializer.validated_data['product'])
            if 'quantity' in serializer.validated_data:
                quantity = serializer.validated_data['quantity']
            else:
                quantity = 1
            if created:
                item.quantity = quantity
            else:
                item.quantity += quantity
            item.save()
            basket.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='remove')
    def remove_item(self, request, pk=None):
        basket = self.get_object()
        serializer = BasketItemActionSerializer(data=request.data)
        if serializer.is_valid():
            try:
                item = basket.items.get(product=serializer.validated_data['product'])
                item.delete()
            except BasketItem.DoesNotExist:
                pass
            basket.save()
            if basket.items.count() == 0:
                basket.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='update')
    def update_item(self, request, pk=None):
        basket = self.get_object()
        serializer = BasketItemActionSerializer(data=request.data)
        if serializer.is_valid():
            item, created = basket.items.get_or_create(product=serializer.validated_data['product'])
            if 'quantity' in serializer.validated_data:
                quantity = serializer.validated_data['quantity']
                if quantity <= 0:
                    quantity = 0
            else:
                quantity = item.quantity
            if quantity == 0:
                item.delete()
            else:
                item.quantity = quantity
                item.save()
            if basket.items.count() == 0:
                basket.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    pagination_class = StandardResultsSetPagination
    queryset = get_user_model().objects.all()
    lookup_field = 'phone'
    lookup_value_regex = '(:?\+\d+|current)'

    def get_serializer_class(self):
        if self.action == 'retrieve':
            if self.request.user.is_authenticated:
                return UserSerializer
            else:
                return AnonymousUserSerializer
        elif self.action == 'login':
            return LoginSerializer
        return UserSerializer

    def get_permissions(self):
        # Only superuser can create, update, partial update, destroy, list
        self.permission_classes = [IsSuperUser]

        logger.error(self.action)
        if self.action == 'retrieve':
            self.permission_classes = [IsSelf]
        elif self.action in ('check', 'code', 'login'):
            self.permission_classes = []

        return super().get_permissions()

    def get_object(self):
        key = self.kwargs.get(self.lookup_field)

        if key == 'current':
            return self.request.user

        return super().get_object()

    @action(detail=True, methods=['post'])
    def check(self, request, phone=None):
        user = self.get_object()
        permanent_password = getattr(user, 'permanent_password', False)
        reset = request.data.get('reset', False)
        if not permanent_password or reset:
            password = str(randint(1000, 9999))
            user.set_password(password)
            user.permanent_password = False
            user.save()
            send_password.delay(user.phone, password)
        return Response({
            'exists': hasattr(user, 'id'),
            'permanent_password': permanent_password and not reset
        })

    @action(detail=False, methods=['post'])
    def login(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data
        login(request, user)
        refresh = RefreshToken.for_user(user)
        return Response({
            "user": UserSerializer(user, context=self.get_serializer_context()).data,
            "sjwt": {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "accessExpires": refresh.access_token['exp']
            }
        })

    @action(detail=False, methods=['get'])
    def logout(self, request, *args, **kwargs):
        logout(request)
        return Response({
            "user": None,
        })


class CsrfTokenView(views.APIView):
    @method_decorator(ensure_csrf_cookie)
    def get(self, request, *args, **kwargs):
        return Response({
            "session": request.session
        })


class FlatPageViewSet(viewsets.ReadOnlyModelViewSet):
    lookup_field = 'url'
    lookup_value_regex = '.*'
    ordering = ('url',)

    def get_serializer_class(self):
        if self.action == 'list':
            return FlatPageListSerializer
        return FlatPageSerializer

    def get_queryset(self):
        domain = urlparse(self.request.META.get('HTTP_REFERER', '')).hostname
        if domain == 'cartzilla.sigalev.ru':  # TODO: put this in Sites config
            domain = 'www.sewing-world.ru'
        return FlatPage.objects.filter(sites__domain=domain)

    def get_object(self):
        # TODO: add support for authorization and template
        key = self.kwargs.get(self.lookup_field)
        self.kwargs[self.lookup_field] = '/{}/'.format(key)
        return super().get_object()
