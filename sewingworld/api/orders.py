import logging

from django.conf import settings
from django.core.mail import mail_admins
from django.http import HttpResponseRedirect
from django.template.loader import render_to_string

from rest_framework import views, viewsets, serializers, status
from rest_framework.decorators import action
from rest_framework.exceptions import MethodNotAllowed
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, extend_schema_view, inline_serializer, OpenApiParameter, OpenApiResponse

from yandex_kassa.views import payment as yandex_payment

from shop.models import Basket, Order, OrderItem, ShopUser, Serial
from shop.tasks.user_interaction import notify_user_order_new_sms, notify_user_order_new_mail

from sewingworld.serializers.common import validation_error_serializer
from sewingworld.serializers.orders import OrderListSerializer, OrderSerializer, OrderActionSerializer, \
    PreorderSerializer, SerialSerializer

from .common import FORBIDDEN, NOT_FOUND, StandardResultsSetPagination, id_params
from .users import queue_email_confirmation

logger = logging.getLogger("django")

# Built once, drf-spectacular expects one serializer class per component name
ORDER_ERRORS = validation_error_serializer(OrderActionSerializer)
PREORDER_ERRORS = validation_error_serializer(PreorderSerializer)


def adopt_order_email(request, view, order):
    """
    A buyer without an address gets the one typed for the order, to confirm: order mail goes only to
    the buyer's confirmed address, and is postponed until then.
    """
    user = order.user
    if not order.email or user.email or ShopUser.objects.filter(email__iexact=order.email).exclude(pk=user.pk).exists():
        return
    user.email = order.email
    user.email_verified = False
    user.save(update_fields=['email', 'email_verified'])
    queue_email_confirmation(request, view, user)


@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter('filter', str, enum=['active', 'done', 'canceled'], description='Only active, done or canceled orders'),
            OpenApiParameter('site', OpenApiTypes.INT, description='Only orders made on this site'),
        ],
        responses={200: OrderListSerializer(many=True), 403: FORBIDDEN}
    ),
    retrieve=extend_schema(responses={200: OrderSerializer, 403: FORBIDDEN, 404: NOT_FOUND}),
    update=extend_schema(responses={200: OrderSerializer, 400: ORDER_ERRORS, 403: FORBIDDEN, 404: NOT_FOUND}),
)
class OrderViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Order.objects.none()  # model for the API schema, get_queryset() needs a request
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
        order_sites = id_params(self.request, 'site')
        if order_sites:
            filters['site'] = order_sites[-1]
        order_filter = self.request.query_params.get('filter', None)
        if order_filter == 'done':
            filters['status__in'] = [Order.STATUS_DONE, Order.STATUS_FINISHED]
        elif order_filter == 'canceled':
            filters['status'] = Order.STATUS_CANCELED
        elif order_filter == 'active':
            excludes['status__in'] = [Order.STATUS_DONE, Order.STATUS_FINISHED, Order.STATUS_CANCELED]
        queryset = Order.objects.order_by('-id').filter(**filters).exclude(**excludes)
        return queryset

    @extend_schema(
        request=None,
        responses={
            200: OrderSerializer,
            400: OpenApiResponse(OpenApiTypes.STR, description='Basket does not exist, Basket is empty or Failed to register order'),
            403: FORBIDDEN,
        },
    )
    def create(self, request):
        if not request.session.session_key:  # without it, the query would match every basket left without a session
            return Response("Basket does not exist", status=status.HTTP_400_BAD_REQUEST)
        try:
            basket = Basket.objects.get(site=request.site, session_id=request.session.session_key)
        except Basket.DoesNotExist:
            return Response("Basket does not exist", status=status.HTTP_400_BAD_REQUEST)

        if basket.quantity == 0:
            return Response("Basket is empty", status=status.HTTP_400_BAD_REQUEST)

        try:
            order = Order.register(basket, site=request.site)
            """
            ipgeobases = IPGeoBase.objects.by_ip(request.META.get('REMOTE_ADDR'))
            if ipgeobases.exists():
                for ipgeobase in ipgeobases:
                    if ipgeobase.city is not None:
                        order.city = ipgeobase.city
                        break
            order.save()
            """
            """ wait for 5 minutes to let user supply comments and other stuff """
            try:
                notify_user_order_new_mail.apply_async((order.id,), countdown=300)
                notify_user_order_new_sms.apply_async((order.id,), countdown=300)
            except Exception as e:
                mail_admins('Task error', 'Failed to send notification: %s' % e, fail_silently=True)
            basket.delete()

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
        adopt_order_email(request, self, instance)
        return Response(OrderSerializer(instance, context=self.get_serializer_context()).data)

    def destroy(self, request, *args, **kwargs):
        raise MethodNotAllowed(request.method)

    @extend_schema(
        request=PreorderSerializer,
        responses={
            200: OrderSerializer,
            400: PREORDER_ERRORS,
            403: FORBIDDEN,
        },
        methods=['POST']
    )
    @action(detail=False, methods=['post'])
    def preorder(self, request):
        serializer = PreorderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product = serializer.validated_data['product']
        request.session.save()  # ensure session is persisted
        request.session.modified = True
        basket = Basket.objects.create(site=request.site, session_id=request.session.session_key, secondary=True)
        item = basket.items.create(product=product, quantity=1)
        item.save()
        basket.save()
        kwargs = {
            'site': request.site,
            'comment': 'Запрос о поступлении'
        }
        order = Order.register(basket, **kwargs)
        """
        ipgeobases = IPGeoBase.objects.by_ip(request.META.get('REMOTE_ADDR'))
        if ipgeobases.exists():
            for ipgeobase in ipgeobases:
                if ipgeobase.city is not None:
                    order.city = ipgeobase.city
                    break
        """
        order.save()
        basket.delete()
        return Response(OrderSerializer(order, context=self.get_serializer_context()).data)

    @extend_schema(
        request=inline_serializer('Payment', fields={'return_url': serializers.CharField(required=False)}),
        responses={
            200: OpenApiResponse(
                response={
                    'type': 'object',
                    'properties': {
                        'location': {'type': 'string'},
                    },
                }
            ),
            403: FORBIDDEN,
            404: NOT_FOUND,
        },
        methods=['POST']
    )
    @action(detail=True, methods=['post'])
    def pay(self, request, pk=None):
        order = self.get_object()  # this looks redundant but we keep it for framework internal checks
        return_url = request.data.get('return_url', None)
        response = yandex_payment(request, order.id, return_url)
        if isinstance(response, HttpResponseRedirect):
            return Response({'location': response.url})
        else:
            return response

    @extend_schema(
        request=None,
        responses={
            200: OpenApiResponse(
                response={
                    'type': 'object',
                    'properties': {
                        'id': {'type': 'integer', 'nullable': True},
                    },
                    'required': ['id'],
                }
            ),
            403: FORBIDDEN,
        },
        methods=['POST']
    )
    @action(detail=False, methods=['post'])
    def last(self, request):
        queryset = self.get_queryset().order_by('-id').values_list('id', flat=True)
        last = queryset.exclude(status__in=[Order.STATUS_DONE, Order.STATUS_FINISHED, Order.STATUS_CANCELED]).first()
        return Response({
            'id': last
        })

    @extend_schema(
        request=None,
        responses={
            200: OpenApiResponse(
                response={
                    'type': 'object',
                    'properties': {
                        'id': {'type': 'integer', 'nullable': True},
                    },
                    'required': ['id'],
                }
            ),
            403: FORBIDDEN,
        },
        methods=['POST']
    )
    @action(detail=False, methods=['post'])
    def unpaid(self, request):
        queryset = self.get_queryset().order_by('-id').values_list('id', flat=True)
        unpaid = queryset.filter(status=Order.STATUS_COLLECTED, paid=False, payment__in=[Order.PAYMENT_CARD, Order.PAYMENT_TRANSFER, Order.PAYMENT_CREDIT]).first()
        return Response({
            'id': unpaid
        })


class SerialViewSet(viewsets.ModelViewSet):
    serializer_class = SerialSerializer
    queryset = Serial.objects.none()  # model for the API schema, get_queryset() needs a request
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Serial.objects.filter(user=self.request.user)
        return queryset

    def destroy(self, request, *args, **kwargs):
        raise MethodNotAllowed(request.method)

    def update(self, request, *args, **kwargs):
        raise MethodNotAllowed(request.method)


class WarrantyCardView(views.APIView):
    @extend_schema(
        responses={
            200: OpenApiResponse(
                response={
                    'type': 'object',
                    'properties': {
                        'html': {'type': 'string'},
                    },
                    'required': ['html'],
                },
                description='Warranty card to print',
            ),
            400: OpenApiResponse(
                response={
                    'type': 'object',
                    'properties': {
                        'code': {'type': 'array', 'items': {'type': 'string'}},
                    },
                },
                description='The shop has not sold a product with this serial number',
            ),
        },
    )
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
