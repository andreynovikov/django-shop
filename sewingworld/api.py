import logging
from random import randint

from django.conf import settings
from django.contrib.auth import login, logout
from django.contrib.postgres.search import SearchQuery, SearchRank
from django.core.mail import mail_admins
from django.db.models import F
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator

from rest_framework import views, viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.exceptions import MethodNotAllowed, NotFound
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.response import Response

from django.contrib.flatpages.models import FlatPage
from django_ipgeobase.models import IPGeoBase

from qrcode import QRCode
from qrcode.image.svg import SvgPathImage

from yandex_kassa.views import payment as yandex_payment

from facebook.tasks import FACEBOOK_TRACKING, notify_add_to_cart, notify_initiate_checkout, notify_purchase  # TODO: add all tasks
from rarus.tasks import get_bonus_value
from shop.filters import get_product_filter
from shop.models import Category, ProductKind, Product, ProductSet, Stock, Basket, BasketItem, Order, OrderItem, \
    Favorites, ShopUser, Bonus, News, SalesAction, Advert, Store, ServiceCenter, Serial
from shop.tasks import send_password, notify_user_order_new_sms, notify_user_order_new_mail, notify_manager

from .models import SiteProfile
from .serializers import CategoryTreeSerializer, CategorySerializer, ProductSerializer, ProductListSerializer, \
    ProductKindSerializer, ProductImagesSerializer, \
    BasketSerializer, BasketItemActionSerializer, OrderListSerializer, OrderSerializer, OrderActionSerializer, \
    FavoritesSerializer, ComparisonSerializer, SerialSerializer, \
    UserListSerializer, UserSerializer, AnonymousUserSerializer, LoginSerializer, UserBonusSerializer, \
    FlatPageListSerializer, FlatPageSerializer, NewsSerializer, SalesActionSerializer, AdvertSerializer, \
    StoreSerializer, ServiceCenterSerializer, SiteProfileSerializer


logger = logging.getLogger("django")


def ensure_session(request):
    if hasattr(request, 'session') and not request.session.session_key:
        request.session.save()
        request.session.modified = True


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
    page_size = 20
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


class ProductListSerializerContextMixin:
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['product_thumbnail_size'] = self.request.site.profile.product_thumbnail_size
        context['product_small_thumbnail_size'] = self.request.site.profile.product_small_thumbnail_size
        return context


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    lookup_value_regex = '.*'

    def get_serializer_class(self):
        if self.action == 'list':
            return CategoryTreeSerializer
        return CategorySerializer

    def get_queryset(self):
        if self.action == 'list':
            root_slug = self.request.site.profile.category_root_slug
            return Category.objects.get(slug=root_slug).get_active_children()
        return Category.objects.filter(active=True)

    def get_object(self):
        key = self.kwargs.get(self.lookup_field)

        if not key.isdigit():
            root_slug = self.request.site.profile.category_root_slug
            # instance select taken from mptt_urls
            instance = None
            path = key  # path = '{}/'.format(key)  # we add trailing slash to conform .get_path() from mptt_urls
            try:
                instance_slug = path.split('/')[-1]  # [-2]  # slug of the instance
                candidates = Category.objects.filter(slug=instance_slug)  # candidates to be the instance
                for candidate in candidates:
                    # here we compare each candidate's path to the path passed to this view
                    if candidate.get_api_path() == path:
                        if root_slug != candidate.get_root().slug:
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
        products = self.request.query_params.getlist('product')
        if len(products) > 0:
            queryset = queryset.filter(product__in=products)
        return queryset.distinct()


class ProductViewSet(ProductListSerializerContextMixin, viewsets.ReadOnlyModelViewSet):
    lookup_value_regex = '[^/]+'
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ('id', 'code', 'article', 'title', 'price')
    filtering_fields = [f.name for f in Product._meta.get_fields()] + ['text', 'instock']
    product_filter = None

    def get_serializer_class(self):
        if self.action in ('list', 'info'):
            return ProductListSerializer
        if self.action == 'images':
            return ProductImagesSerializer
        return ProductSerializer

    def get_queryset(self):
        queryset = Product.objects.all().order_by('code')
        has_category_filter = False

        for field, values in self.request.query_params.lists():
            base_field = field.split('__', 1)[0]
            if base_field not in self.filtering_fields:
                continue
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
            elif field in ('show_on_sw', 'gift', 'recomended', 'firstpage', 'enabled'):
                key = '{}__exact'.format(field)
                queryset = queryset.filter(**{key: values[0] == '1'})
            elif field == 'title':
                key = '{}__icontains'.format(field)
                queryset = queryset.filter(**{key: values[0]})
            elif field == 'instock':
                if int(values[0]) > 0:
                    queryset = queryset.filter(num__gt=0)
                else:
                    queryset = queryset.filter(num__exact=0)
            elif field == 'categories':
                key = '{}__pk__exact'.format(field)
                queryset = queryset.filter(**{key: values[0]})
                has_category_filter = True

                category = Category.objects.get(pk=values[0])
                if category.filters:
                    fields = category.filters.split(',')
                    self.product_filter = get_product_filter(self.request.query_params, queryset=queryset, fields=fields, request=self.request)
                    queryset = self.product_filter.qs
            elif field in ('kind', 'manufacturer'):  # поиск по ключу
                if len(values) > 1:
                    key = '{}__pk__in'.format(field)
                    queryset = queryset.filter(**{key: values})
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
            # else:  # строковый поиск
            #     key = '{}__exact'.format(field)
            #     queryset = queryset.filter(**{key: values[0]})

        # Always limit product list to current category hierarchy
        if not has_category_filter:
            root_slug = self.request.site.profile.category_root_slug
            if root_slug:
                root = Category.objects.get(slug=root_slug)
                queryset = queryset.filter(categories__in=root.get_descendants(include_self=True))

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
        return Response({f.name: f.verbose_name.capitalize() for f in Product._meta.get_fields() if hasattr(f, 'verbose_name')})

    @action(detail=True)
    def bycode(self, request, pk=None):
        product = self.get_queryset().filter(code=pk).first()
        if product == None:
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
        user = request.user
        return Response({
            'user': user.pk,
            'user_discount': user.discount,
            'price': product.price,
            'cost': Basket.product_cost_for_user(request.site.profile.wholesale, product, user)
        })

    @action(detail=True)
    def stock(self, request, pk=None):
        product = self.get_object()
        if product.constituents.count() == 0:
            suppliers = product.stock.all()
            stores = Store.objects.filter(enabled=True, supplier__in=suppliers).order_by('city__country__ename', 'city__name')
        else:
            stores = Store.objects.filter(enabled=True).order_by('city__country__ename', 'city__name')
        results = []
        for store in stores:
            if product.constituents.count() == 0:
                stock = Stock.objects.get(product=product, supplier=store.supplier)
                quantity = stock.quantity + stock.correction
            else:
                quantity = 32767
                for item in ProductSet.objects.filter(declaration=product):
                    try:
                        stock = Stock.objects.get(product=item.constituent, supplier=store.supplier)
                        q = stock.quantity + stock.correction
                        if item.quantity > 1:
                            q = int(q / item.quantity)
                    except Stock.DoesNotExist:
                        q = 0.0
                        if q < quantity:
                            quantity = q
            if quantity > 0.0:
                results.append(store)
        return Response(StoreSerializer(results, many=True, context=self.get_serializer_context()).data)

    @action(detail=True)
    def video(self, request, pk=None):
        product = self.get_queryset().filter(code=pk).first()
        if product == None or not product.video_url:
            raise NotFound()
        return redirect(product.video_url)

    @action(detail=True, url_path='video/qr')
    def video_qr(self, request, pk=None):
        product = self.get_object()
        qr = QRCode(border=0, image_factory=SvgPathImage)
        qr.add_data('https://www.sewing-world.ru/products/{}/video/'.format(product.code))
        img = qr.make_image()
        return HttpResponse(img.to_string(encoding='unicode').encode(), content_type='image/svg+xml')


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
        queryset = Basket.objects.filter(site=self.request.site, session_id__isnull=False, session_id=self.request.session.session_key)
        return queryset

    def destroy(self, request):
        raise MethodNotAllowed(request.method)

    def update(self, request, *args, **kwargs):
        raise MethodNotAllowed(request.method)

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


class OrderViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_serializer_class(self):
        if self.action == 'list':
            return OrderListSerializer
        elif self.action == 'retrieve':
            return OrderSerializer
        else:
            return OrderActionSerializer

    def get_queryset(self):
        filters = {
            'user': self.request.user
        }
        excludes = {}
        order_site = self.request.query_params.get('site', None)
        if order_site is not None:
            filters['site'] = order_site
        order_filter = self.request.query_params.get('filter', None)
        if order_filter == 'done':
            filters['status__in'] = [Order.STATUS_DONE, Order.STATUS_FINISHED]
        elif order_filter == 'canceled':
            filters['status'] = Order.STATUS_CANCELED
        elif order_filter == 'active':
            excludes['status__in'] = [Order.STATUS_DONE, Order.STATUS_FINISHED, Order.STATUS_CANCELED]
        queryset = Order.objects.order_by('-id').filter(**filters).exclude(**excludes)
        return queryset

    def create(self, request):
        try:
            basket = Basket.objects.get(site=request.site, session_id=request.session.session_key)
        except Basket.DoesNotExist:
            return Response("Basket does not exist", status=status.HTTP_400_BAD_REQUEST)

        if basket.quantity == 0:
            return Response("Basket is empty", status=status.HTTP_400_BAD_REQUEST)

        try:
            order = Order.register(basket, site=request.site)
            ipgeobases = IPGeoBase.objects.by_ip(request.META.get('REMOTE_ADDR'))
            if ipgeobases.exists():
                for ipgeobase in ipgeobases:
                    if ipgeobase.city is not None:
                        order.city = ipgeobase.city
                        break
            order.save()
            """ wait for 5 minutes to let user supply comments and other stuff """
            try:
                notify_user_order_new_mail.apply_async((order.id,), countdown=300)
                notify_user_order_new_sms.apply_async((order.id,), countdown=300)
            except Exception as e:
                mail_admins('Task error', 'Failed to send notification: %s' % e, fail_silently=True)
            basket.delete()

            if FACEBOOK_TRACKING:
                notify_purchase.delay(order.id, request.build_absolute_uri(),
                                      request.META.get('REMOTE_ADDR'), request.META['HTTP_USER_AGENT'])
            """ clear promo discount """
            try:
                del request.session['discount']
            except KeyError:
                pass

            return Response(OrderSerializer(order, context=self.get_serializer_context()).data)
        except Exception as e:
            # mail_admins('Order error', 'Failed to register order: %s' % e, fail_silently=True)
            logger.exception(e)
            return Response("Failed to register order", status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        super().update(request, *args, **kwargs)
        instance = self.get_object()
        return Response(OrderSerializer(instance, context=self.get_serializer_context()).data)

    def destroy(self, request):
        raise MethodNotAllowed(request.method)

    @action(detail=True, methods=['post'])
    def pay(self, request, pk=None):
        order = self.get_object()  # this looks redundant but we keep it for framework internal checks
        return_url = request.data.get('return_url', None)
        response = yandex_payment(request, order.id, return_url)
        if type(response) == HttpResponseRedirect:
            return Response({'location': response.url})
        else:
            return response

    @action(detail=False, methods=['post'])
    def last(self, request):
        queryset = self.get_queryset().order_by('-id').values_list('id', flat=True)
        last = queryset.exclude(status__in=[Order.STATUS_DONE, Order.STATUS_FINISHED, Order.STATUS_CANCELED]).first()
        if last is None:
            last = queryset.first()
        return Response({
            'id': last
        })

    @action(detail=False, methods=['post'])
    def unpaid(self, request):
        queryset = self.get_queryset().order_by('-id').values_list('id', flat=True)
        unpaid = queryset.filter(status=Order.STATUS_COLLECTED, paid=False, payment__in=[Order.PAYMENT_CARD, Order.PAYMENT_TRANSFER, Order.PAYMENT_CREDIT]).first()
        return Response({
            'id': unpaid
        })


class FavoritesViewSet(viewsets.ModelViewSet):
    serializer_class = FavoritesSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Favorites.objects.filter(user=self.request.user)
        return queryset

    def create(self, request):
        raise MethodNotAllowed(request.method)

    def destroy(self, request):
        raise MethodNotAllowed(request.method)

    def update(self, request, *args, **kwargs):
        raise MethodNotAllowed(request.method)

    @action(detail=False, methods=['post'], url_path='add')
    def add_item(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        favorite, created = Favorites.objects.get_or_create(user=request.user, product=serializer.validated_data['product'])
        if created:
            favorite.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['post'], url_path='remove')
    def remove_item(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        favorite = Favorites.objects.filter(user=request.user, product=serializer.validated_data['product']).first()
        if favorite is not None:
            favorite.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ComparisonsViewSet(viewsets.ViewSet):
    def list(self, request):
        comparison_list = request.session.get('comparison_list', None)
        if comparison_list:
            product_ids = list(map(int, comparison_list.split(',')))
            kind = request.query_params.get('kind', None)
            if kind:
                product_ids = list(Product.objects.filter(pk__in=product_ids, kind=kind).values_list('id', flat=True))
        else:
            product_ids = []
        return Response(product_ids)

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


class UserViewSet(viewsets.ModelViewSet):
    pagination_class = StandardResultsSetPagination
    queryset = ShopUser.objects.all()
    lookup_value_regex = r'(:?\+?\d+|current)'

    def get_serializer_class(self):
        if self.action == 'list':
            return UserListSerializer
        elif self.action == 'retrieve' and not self.request.user.is_authenticated:
            return AnonymousUserSerializer
        elif self.action == 'login':
            return LoginSerializer
        elif self.action == 'bonus':
            return UserBonusSerializer
        return UserSerializer

    def get_permissions(self):
        if self.action in ('retrieve', 'update', 'partial_update'):
            self.permission_classes = [IsSelf]
        elif self.action == 'bonus':
            self.permission_classes = [IsAuthenticated]
        elif self.action in ('create', 'check', 'login', 'logout', 'form'):
            self.permission_classes = []
        else:
            # Only superuser can destroy, list
            self.permission_classes = [IsSuperUser]
        return super().get_permissions()

    def get_object(self):
        key = self.kwargs.get(self.lookup_field)

        if key == 'current':
            return self.request.user

        if not key.isdigit():
            instance = self.get_queryset().filter(phone=key).first()
            if instance:
                self.kwargs[self.lookup_field] = instance.pk

        return super().get_object()

    def destroy(self, request):
        raise MethodNotAllowed(request.method)

    @action(detail=False, methods=['get'])
    def bonus(self, request):
        user = self.request.user
        if not hasattr(user, 'bonus'):
            user.bonus = Bonus()
        if not user.bonus.is_fresh and not user.bonus.is_updating:
            user.bonus.status = Bonus.STATUS_PENDING
            user.bonus.save()
            get_bonus_value.delay(user.phone)
        return Response(self.get_serializer(user.bonus, context=self.get_serializer_context()).data)

    @action(detail=True, methods=['post'])
    def check(self, request, pk=None):
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

        try:
            basket = Basket.objects.get(site=request.site, session_id=request.session.session_key)
        except Basket.MultipleObjectsReturned:
            basket = None
        except Basket.DoesNotExist:
            basket = None

        user = serializer.validated_data
        login(request, user)

        # preserve user basket because django login rotates session id
        if basket:
            ensure_session(request)
            basket.update_session(request.session.session_key)

        return Response({
            "id": user.id,
            "registered": user.registered
        })

    @action(detail=False, methods=['get'])
    def logout(self, request, *args, **kwargs):
        try:
            basket = Basket.objects.get(site=request.site, session_id=request.session.session_key)
        except Basket.DoesNotExist:
            basket = None

        logout(request)

        if basket is not None:
            ensure_session(request)
            basket.update_session(request.session.session_key)

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'])
    def form(self, request, *args, **kwargs):
        from shop.forms import UserForm
        form = UserForm()
        fields = []
        for field in form.visible_fields():
            meta = {
                'name': field.name,
                'label': field.label,
                'id': field.id_for_label,
                'help': field.help_text,
                'class': field.field.__class__.__name__,
                'widget': field.field.widget.__class__.__name__,
                'required': field.field.required
            }
            if hasattr(field.field, 'choices'):
                meta['choices'] = field.field.choices
            if field.field.widget.attrs:
                meta['attrs'] = field.field.widget.attrs
            fields.append(meta)
        return Response(fields)


class SerialViewSet(viewsets.ModelViewSet):
    serializer_class = SerialSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Serial.objects.filter(user=self.request.user)
        return queryset

    def destroy(self, request):
        raise MethodNotAllowed(request.method)

    def update(self, request, *args, **kwargs):
        raise MethodNotAllowed(request.method)


class CsrfTokenView(views.APIView):
    @method_decorator(ensure_csrf_cookie)
    def get(self, request, *args, **kwargs):
        return Response({
            "session": request.session,
            "csrf": request.META["CSRF_COOKIE"]
        })


class WarrantyCardView(views.APIView):
    def get(self, request, code):
        item = OrderItem.objects.filter(serial_number=code.strip()).order_by('-order__created').first()
        if item is None:
            return Response({'code': ['Изделие с таким серийным номером не покупалось в нашем интернет-магазине']}, status=status.HTTP_400_BAD_REQUEST)

        context = {
            'owner_info': getattr(settings, 'SHOP_OWNER_INFO', {}),
            'order': item.order,
            'product': item.product,
            'serial_number': item.serial_number,
            'admin': False
        }

        rendered = render_to_string('shop/warrantycard/common.html', context)

        return Response({
            "html": rendered
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
        return FlatPage.objects.filter(sites=self.request.site)

    def get_object(self):
        # TODO: add support for authorization and template
        key = self.kwargs.get(self.lookup_field)
        self.kwargs[self.lookup_field] = '/{}/'.format(key)
        return super().get_object()


class NewsViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NewsSerializer

    def get_queryset(self):
        return News.objects.filter(sites=self.request.site, active=True)


class SalesActionViewSet(ProductListSerializerContextMixin, viewsets.ReadOnlyModelViewSet):
    lookup_field = 'slug'
    ordering = ('order',)
    serializer_class = SalesActionSerializer

    def get_queryset(self):
        queryset = SalesAction.objects.filter(active=True, sites=self.request.site)
        if self.action == 'list':
            queryset = queryset.filter(show_in_list=True)
        return queryset

    @action(detail=True)
    def products(self, request, slug=None):
        action = self.get_object()
        return Response(ProductListSerializer(action.products.filter(enabled=True).order_by('-price'), many=True, context=self.get_serializer_context()).data)


class AdvertViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AdvertSerializer

    def get_queryset(self):
        queryset = Advert.objects.filter(sites=self.request.site, active=True)
        places = self.request.query_params.getlist('place')
        if len(places) > 0:
            queryset = queryset.filter(place__in=places)
        return queryset


class StoreViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = StoreSerializer

    def get_queryset(self):
        return Store.objects.filter(enabled=True).order_by('city__country__ename', 'city__name')


class ServiceCenterViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ServiceCenterSerializer

    def get_queryset(self):
        return ServiceCenter.objects.filter(enabled=True).order_by('city__country__ename', 'city__name')


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
