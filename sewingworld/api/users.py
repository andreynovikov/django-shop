from django.contrib.auth import login, logout
from django.core import signing
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.debug import sensitive_variables
from django.utils.decorators import method_decorator

from rest_framework import views, viewsets, serializers, status
from rest_framework.decorators import action
from rest_framework.exceptions import MethodNotAllowed, NotAuthenticated
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.response import Response

from drf_spectacular.utils import extend_schema, extend_schema_view, inline_serializer, OpenApiParameter, \
    OpenApiResponse, PolymorphicProxySerializer

# from rarus.tasks import get_bonus_value
from shop import email_confirmation
from shop.models import Basket, ShopUser, ShopUserManager, LoginCode, PhoneCode, Bonus
from shop.tasks.user_interaction import send_password, send_phone_code, send_email_confirmation

from sewingworld.serializers.common import ErrorDetailSerializer, validation_error_serializer
from sewingworld.serializers.users import UserListSerializer, UserSerializer, RegistrationSerializer, \
    AnonymousUserSerializer, LoginSerializer, PhoneValidator, UserBonusSerializer, EMAIL_TAKEN
from sewingworld.throttles import LoginIpThrottle, CheckIpThrottle, CheckPhoneThrottle, CheckPhoneDailyThrottle, \
    RegistrationIpThrottle, EmailLinkUserThrottle, EmailLinkIpThrottle

from .common import FORBIDDEN, NOT_FOUND, THROTTLED, IsSuperUser, StandardResultsSetPagination, ensure_session

# Built once, drf-spectacular expects one serializer class per component name
USER_ERRORS = validation_error_serializer(UserSerializer)
REGISTRATION_ERRORS = validation_error_serializer(RegistrationSerializer)

# Answer to registration or a phone change without the code: nothing is saved until the code comes back
PHONE_CODE_SENT = OpenApiResponse(
    inline_serializer('PhoneCodeSent', fields={
        'phone': serializers.CharField(),
        'retry_after': serializers.IntegerField(help_text='Seconds until a new code can be requested'),
        'attempts_left': serializers.IntegerField(help_text='Attempts left for the code'),
    }),
    description='Code sent to the phone, or the one sent recently is still valid. Send the data again with it.'
)

WRONG_CODE = 'Неверный или устаревший код'
BAD_EMAIL_LINK = 'Ссылка недействительна или устарела'

# users/current/ returns the anonymous user too
CURRENT_USER = PolymorphicProxySerializer(
    component_name='CurrentUser',
    serializers=[UserSerializer, AnonymousUserSerializer],
    resource_type_field_name=None,
)


def sign_in(request, user):
    """ Logs the user in and keeps the basket, which is tied to the session key that login rotates """
    basket = None
    if request.session.session_key:  # without it, the query would match every basket left without a session
        try:
            basket = Basket.objects.get(site=request.site, session_id=request.session.session_key)
        except (Basket.DoesNotExist, Basket.MultipleObjectsReturned):
            pass

    login(request, user)

    if basket is not None:
        ensure_session(request)
        basket.update_session(request.session.session_key)


@sensitive_variables()  # the code it issues
def send_phone_code_once(request, view, phone, user=None):
    """
    Sends a code that proves the phone, for registration or for the user moving to it. As with login codes,
    one sent recently is kept, so a resubmit or a reload sends nothing, and codes sent count against
    the phone's limit for login codes.
    """
    with transaction.atomic():
        phone_code = PhoneCode.objects.select_for_update().filter(phone=phone, user=user).first()
        if phone_code is None or phone_code.retry_after == 0:
            for throttle in (CheckIpThrottle(), CheckPhoneThrottle(phone)):
                if not throttle.allow_request(request, view):
                    view.throttled(request, throttle.wait())
            code, phone_code = PhoneCode.issue(phone, user)
            send_phone_code.delay(phone, code)  # if it fails, record is rolled back and user can retry
    return {
        'phone': phone,
        'retry_after': phone_code.retry_after,
        'attempts_left': phone_code.attempts_left,
    }


def queue_email_confirmation(request, view, user):
    """ Sends the link that confirms the user's address. Returns the throttle that stopped it, if one did. """
    for throttle in (EmailLinkUserThrottle(user), EmailLinkIpThrottle()):
        if not throttle.allow_request(request, view):
            return throttle
    send_email_confirmation.delay(user.id, user.email, request.site.id)
    return None


class IsSelf(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user:
            if request.user.is_superuser:
                return True
            else:
                return obj.pk == request.user.pk
        else:
            return False


@extend_schema_view(
    create=extend_schema(
        description='Registration. Without `code` it checks the data and sends a code to the phone (202). '
                    'With the code it creates the account and logs the user in (201).',
        responses={201: UserSerializer, 202: PHONE_CODE_SENT, 400: REGISTRATION_ERRORS, 429: THROTTLED}
    ),
    retrieve=extend_schema(responses={200: CURRENT_USER, 403: FORBIDDEN, 404: NOT_FOUND}),
    update=extend_schema(
        description='A new phone needs `code`: without it, nothing is saved and a code is sent to that phone (202).',
        responses={200: UserSerializer, 202: PHONE_CODE_SENT, 400: USER_ERRORS, 403: FORBIDDEN, 404: NOT_FOUND, 429: THROTTLED}
    ),
    partial_update=extend_schema(
        responses={200: UserSerializer, 202: PHONE_CODE_SENT, 400: USER_ERRORS, 403: FORBIDDEN, 404: NOT_FOUND, 429: THROTTLED}
    ),
)
class UserViewSet(viewsets.ModelViewSet):
    pagination_class = StandardResultsSetPagination
    queryset = ShopUser.objects.order_by('id')  # pages of an unordered query may repeat or skip rows
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
        elif self.action == 'create':
            return RegistrationSerializer
        return UserSerializer

    def get_permissions(self):
        if self.action in ('retrieve', 'update', 'partial_update', 'email_link'):
            self.permission_classes = [IsSelf]
        elif self.action == 'bonus':
            self.permission_classes = [IsAuthenticated]
        elif self.action in ('create', 'check', 'login', 'logout', 'form', 'confirm_email'):
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

    def get_throttles(self):
        if self.action == 'create':
            return [RegistrationIpThrottle()]
        return super().get_throttles()

    @sensitive_variables()  # the code and the password
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)  # all of it first, so that a code is sent only for data that will do
        phone = serializer.validated_data['phone']
        code = serializer.validated_data.get('code')
        if not code:
            return Response(send_phone_code_once(request, self, phone), status=status.HTTP_202_ACCEPTED)
        email = serializer.validated_data.get('email')
        if email and serializer.email_taken(email):
            # Told only to whoever has the code, so that registration doesn't show which addresses are customers'.
            # A good code is kept for the corrected address, but the attempt counts, so one code can't try many.
            if not PhoneCode.verify(phone, code, keep=True):
                raise serializers.ValidationError({'code': [WRONG_CODE]})
            raise serializers.ValidationError({'email': [EMAIL_TAKEN]})
        if not PhoneCode.verify(phone, code):
            raise serializers.ValidationError({'code': [WRONG_CODE]})
        try:
            user = serializer.save(phone_verified=True)
        except IntegrityError:  # registered in between
            raise serializers.ValidationError({'phone': ["Пользователь с указанным номером уже зарегестрирован"]})
        sign_in(request, user)
        if user.email:
            queue_email_confirmation(request, self, user)
        return Response(UserSerializer(user, context=self.get_serializer_context()).data, status=status.HTTP_201_CREATED)

    @sensitive_variables()  # the code
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        verified = {}
        phone = serializer.validated_data.get('phone', instance.phone)
        if phone != instance.phone:
            code = serializer.validated_data.get('code')
            if not code:
                return Response(send_phone_code_once(request, self, phone, instance), status=status.HTTP_202_ACCEPTED)
            if not PhoneCode.verify(phone, code, instance):
                raise serializers.ValidationError({'code': [WRONG_CODE]})
            verified['phone_verified'] = True
        email_changed = serializer.validated_data.get('email', instance.email) != instance.email
        user = serializer.save(**verified)  # a new email is not verified, see UserSerializer.update
        if email_changed and user.email:
            queue_email_confirmation(request, self, user)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        raise MethodNotAllowed(request.method)

    @extend_schema(
        request=None,
        responses={
            204: None,
            400: OpenApiResponse(inline_serializer('EmailLinkError', fields={
                'email': serializers.ListField(child=serializers.CharField())
            }), description='No address, or it is confirmed already'),
            403: FORBIDDEN,
            404: NOT_FOUND,
            429: THROTTLED,
        },
        methods=['POST']
    )
    @action(detail=True, methods=['post'], url_path='email-link')
    def email_link(self, request, pk=None):
        """ Sends the link that confirms the user's address again """
        user = self.get_object()
        if not user.email or user.email_verified:
            raise serializers.ValidationError({'email': ['Адрес не указан или уже подтверждён']})
        throttle = queue_email_confirmation(request, self, user)
        if throttle is not None:
            self.throttled(request, throttle.wait())
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        request=inline_serializer('EmailConfirmation', fields={'token': serializers.CharField()}),
        responses={
            200: inline_serializer('EmailConfirmed', fields={'email': serializers.CharField()}),
            400: OpenApiResponse(inline_serializer('EmailConfirmationError', fields={
                'token': serializers.ListField(child=serializers.CharField())
            }), description='Bad or expired link, or the address has changed since it was sent'),
        },
        methods=['POST']
    )
    @action(detail=False, methods=['post'], url_path='confirm-email')
    def confirm_email(self, request):
        """ Confirms the address from the link, without a session: the link may be opened on another device """
        token = request.data.get('token') if isinstance(request.data, dict) else None
        try:
            user_id, email = email_confirmation.read_token(str(token or ''))
        except signing.BadSignature:
            raise serializers.ValidationError({'token': [BAD_EMAIL_LINK]})
        user = ShopUser.objects.filter(pk=user_id, email=email).first()
        if user is None:
            raise serializers.ValidationError({'token': [BAD_EMAIL_LINK]})
        if not user.email_verified:
            user.email_verified = True
            user.save(update_fields=['email_verified'])
        return Response({'email': user.email})

    @action(detail=False, methods=['get'])
    def bonus(self, request):
        user = self.request.user
        if not hasattr(user, 'bonus'):
            user.bonus = Bonus()
        # if not user.bonus.is_fresh and not user.bonus.is_updating:
        #     user.bonus.status = Bonus.STATUS_PENDING
        #     user.bonus.save()
        #     get_bonus_value.delay(user.phone)
        return Response(self.get_serializer(user.bonus, context=self.get_serializer_context()).data)

    @extend_schema(
        request=inline_serializer('UserCheck', fields={'reset': serializers.BooleanField(required=False)}),
        parameters=[OpenApiParameter('id', str, OpenApiParameter.PATH, description='Phone number')],
        responses={
            200: OpenApiResponse(
                response={
                    'type': 'object',
                    'properties': {
                        'phone': {'type': 'string'},
                        'permanent_password': {'type': 'boolean'},
                        'retry_after': {'type': 'integer', 'description': 'Seconds until a new code can be requested'},
                        'attempts_left': {'type': 'integer', 'description': 'Attempts left for the code, zero if there is no code'}
                    },
                    'required': ['phone', 'permanent_password', 'retry_after', 'attempts_left'],
                }
            ),
            400: OpenApiResponse(inline_serializer('UserCheckError', fields={
                'phone': serializers.ListField(child=serializers.CharField())
            }), description='Not a +7 phone'),
            404: OpenApiResponse(ErrorDetailSerializer, description='Phone is not registered'),
            429: THROTTLED,
        },
        methods=['POST']
    )
    @action(detail=True, methods=['post'], throttle_classes=[CheckIpThrottle])
    @sensitive_variables()  # the code it issues, also hidden in the frames it calls
    def check(self, request, pk=None):
        phone = ShopUserManager.normalize_phone(pk)
        if not PhoneValidator.pattern.match(phone):  # no SMS abroad, even to old accounts
            raise serializers.ValidationError({'phone': [PhoneValidator.message]})
        # By phone only: anyone can call this, so accepting user id would reveal phones of all customers
        user = get_object_or_404(self.get_queryset(), phone=phone)
        reset = request.data.get('reset', False)
        login_code = None
        if not user.permanent_password or reset:
            # A page reload lands here too: it should not send a code or lose attempts of the one being typed
            with transaction.atomic():
                ShopUser.objects.select_for_update().get(pk=user.pk)  # the first code has no record to lock yet
                login_code = LoginCode.objects.filter(user=user).first()
                if login_code is None or login_code.retry_after == 0:
                    for throttle in (CheckPhoneThrottle(), CheckPhoneDailyThrottle()):
                        if not throttle.allow_request(request, self):
                            self.throttled(request, throttle.wait())
                    # Nothing changes for user until the code is proven, see LoginSerializer
                    code, login_code = LoginCode.issue(user)
                    send_password.delay(user.phone, code)  # if it fails, record is rolled back and user can retry
        return Response({
            'phone': user.phone,
            'permanent_password': user.permanent_password and not reset,
            'retry_after': login_code.retry_after if login_code else 0,
            'attempts_left': login_code.attempts_left if login_code else 0
        })

    @extend_schema(
        request=LoginSerializer,
        responses={
            200: OpenApiResponse(
                response={
                    'type': 'object',
                    'properties': {
                        'id': {'type': 'integer'},
                        'registered': {'type': 'boolean'}
                    }
                }
            ),
            400: OpenApiResponse(inline_serializer('LoginError', fields={
                'permanent_password': serializers.ListField(child=serializers.CharField())
            }), description='New permanent password is too short, the code is not used up'),
            403: OpenApiResponse(ErrorDetailSerializer, description='Wrong code or password'),
            429: OpenApiResponse(ErrorDetailSerializer, description='Too many requests from the client, '
                                 'or too many wrong permanent passwords for the phone: a code from SMS still logs in'),
        },
        methods=['POST']
    )
    # The limits per phone are on wrong permanent passwords only, see LoginSerializer.check_credentials
    @action(detail=False, methods=['post'], throttle_classes=[LoginIpThrottle])
    @sensitive_variables()  # the code or password, also hidden in the serializer and the frames below
    def login(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            if 'permanent_password' in serializer.errors:
                raise serializers.ValidationError({'permanent_password': serializer.errors['permanent_password']})
            raise NotAuthenticated()

        user = serializer.validated_data
        sign_in(request, user)

        return Response({
            'id': user.id,
            'registered': user.registered
        })

    @extend_schema(
        request=None,
        responses={
            204: None
        },
        methods=['GET', 'POST']
    )
    # GET stays until every storefront logs out with POST; their proxies already refuse a GET from browsers
    @action(detail=False, methods=['get', 'post'])
    def logout(self, request, *args, **kwargs):
        basket = None
        if request.session.session_key:  # without it, the query would match every basket left without a session
            try:
                basket = Basket.objects.get(site=request.site, session_id=request.session.session_key)
            except (Basket.DoesNotExist, Basket.MultipleObjectsReturned):
                pass

        logout(request)

        if basket is not None:
            ensure_session(request)
            basket.update_session(request.session.session_key)

        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        responses={
            200: OpenApiResponse(
                response={
                    'type': 'array',
                    'items': {
                        'type': 'object',
                        'properties': {
                            'name': {'type': 'string'},
                            'label': {'type': 'string'},
                            'id': {'type': 'string'},
                            'help': {'type': 'string'},
                            'required': {'type': 'boolean'},
                        },
                    }
                }
            )
        },
        methods=['GET']
    )
    @action(detail=False, methods=['get'])
    def form(self, request, *args, **kwargs):
        fields = [
            {
                'name': 'name',
                'label': 'Имя',
                'id': 'name_id',
                'required': False
            },
            {
                'name': 'phone',
                'label': 'Телефон',
                'id': 'phone_id',
                'help': 'Мы принимаем только мобильные телефоны',
                'required': True
            },
            {
                'name': 'email',
                'label': 'Эл.почта',
                'id': 'email_id',
                'required': False
            },
            {
                'name': 'address',
                'label': 'Адрес',
                'id': 'address_id',
                'required': False
            },
            {
                'name': 'username',
                'label': 'Псевдоним',
                'id': 'username_id',
                'help': 'Отображается в форуме',
                'required': False
            }
        ]
        return Response(fields)


class CsrfTokenView(views.APIView):
    @extend_schema(
        responses={
            200: OpenApiResponse(
                response={
                    'type': 'object',
                    'properties': {
                        'csrf': {'type': 'string'},
                    },
                    'required': ['csrf'],
                }
            )
        },
    )
    @method_decorator(ensure_csrf_cookie)
    def get(self, request, *args, **kwargs):
        return Response({
            "csrf": request.META["CSRF_COOKIE"]
        })
