import re
from math import ceil

from django.contrib.auth import authenticate, password_validation

from rest_framework import serializers
from rest_framework.exceptions import Throttled

from drf_spectacular.extensions import OpenApiSerializerExtension
from drf_spectacular.utils import Direction

from sewingworld.templatetags.gravatar import get_gravatar_url
from sewingworld.throttles import PasswordFailureHourlyThrottle, PasswordFailureDailyThrottle

from shop.models import ShopUser, ShopUserManager, LoginCode, Bonus

EMAIL_TAKEN = "Пользователь с указанным адресом уже зарегестрирован"
TOO_MANY_PASSWORDS = "Слишком много попыток входа с неверным паролем. Войдите с кодом из смс."


class UserListSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField(read_only=True)
    gravatar = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ShopUser
        fields = ('id', 'full_name', 'gravatar')

    def get_full_name(self, obj) -> str:
        return obj.get_full_name()

    def get_gravatar(self, obj) -> str:
        return get_gravatar_url(obj, 90)


class PhoneValidator:
    """ Russian numbers only, +7 and ten digits: codes go by SMS, and other countries cost more and draw SMS fraud """
    message = 'Укажите мобильный номер в формате +7 (999) 111-22-33'
    code = 'invalid_phone'
    pattern = re.compile(r'^\+7\d{10}$')

    def __call__(self, value):
        if not self.pattern.match(ShopUserManager.normalize_phone(value)):
            raise serializers.ValidationError(self.message, code=self.code)


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField(read_only=True)
    gravatar = serializers.SerializerMethodField()
    discount = serializers.ReadOnlyField()
    bonuses = serializers.ReadOnlyField()
    expiring_bonuses = serializers.ReadOnlyField()
    expiration_date = serializers.ReadOnlyField()
    permanent_password = serializers.ReadOnlyField()
    last_login = serializers.ReadOnlyField()
    date_joined = serializers.ReadOnlyField()
    code = serializers.CharField(write_only=True, required=False, help_text='Code from SMS sent to a new phone')

    class Meta:
        model = ShopUser
        exclude = ('groups', 'user_permissions', 'password', 'tags', 'is_superuser', 'is_active', 'is_staff', 'first_name', 'last_name')
        read_only_fields = ('email_verified', 'phone_verified')

    def get_full_name(self, obj) -> str:
        return obj.get_full_name()

    def get_gravatar(self, obj) -> str:
        return get_gravatar_url(obj, 90)

    def validate_phone(self, value):
        PhoneValidator()(value)
        norm_phone = ShopUserManager.normalize_phone(value)
        another = ShopUser.objects.filter(phone=norm_phone).first()
        if another is not None and not (self.instance and another.id == self.instance.id):
            raise serializers.ValidationError("Пользователь с указанным номером уже зарегестрирован")
        return norm_phone

    def validate_email(self, value):
        if value == '':
            return value
        if self.email_taken(value):
            raise serializers.ValidationError(EMAIL_TAKEN)
        return value

    def email_taken(self, value):
        another = ShopUser.objects.filter(email=value).first()
        return another is not None and not (self.instance and another.id == self.instance.id)

    def validate_username(self, value):
        if value == '':
            return value
        another = ShopUser.objects.filter(username=value).first()
        if another is not None and not (self.instance and another.id == self.instance.id):
            raise serializers.ValidationError("Пользователь с указанным псевдонимом уже зарегестрирован")
        return value

    def update(self, instance, validated_data):
        validated_data.pop('code', None)  # checked by the view
        if validated_data.get('email', instance.email) != instance.email:
            validated_data['email_verified'] = False
        return super().update(instance, validated_data)


class RegistrationSerializer(UserSerializer):
    """ New account: the data, then the same data with the code sent to the phone, see UserViewSet.create """
    password = serializers.CharField(write_only=True, required=False, allow_blank=True, style={'input_type': 'password'},
                                     help_text='Permanent password, without it the user logs in with codes from SMS')

    class Meta(UserSerializer.Meta):
        exclude = tuple(name for name in UserSerializer.Meta.exclude if name != 'password')

    def validate_password(self, value):
        if value:
            password_validation.validate_password(value)
        return value

    def validate_email(self, value):
        # A taken address is reported only with the phone's code, see UserViewSet.create
        return value

    def create(self, validated_data):
        validated_data.pop('code', None)  # checked by the view
        password = validated_data.pop('password', '')
        user = ShopUser(**validated_data)
        if password:
            user.set_password(password)
            user.permanent_password = True
        else:
            user.set_unusable_password()
        user.save()
        return user


class AnonymousUserSerializer(serializers.BaseSerializer):
    def to_representation(self, instance):
        return {
            'id': None,
            'is_anonymous': True
        }


class AnonymousUserSerializerExtension(OpenApiSerializerExtension):
    target_class = AnonymousUserSerializer

    def map_serializer(self, auto_schema, direction: Direction):
        # OpenAPI 3.0 has no null type. The enum keeps a signed in user from matching this schema too.
        return {
            'type': 'object',
            'properties': {
                'id': {'type': 'integer', 'nullable': True, 'readOnly': True},
                'is_anonymous': {'type': 'boolean', 'enum': [True], 'readOnly': True},
            },
            'required': ['id', 'is_anonymous'],
        }


class LoginSerializer(serializers.Serializer):
    phone = serializers.CharField(validators=[PhoneValidator()])
    password = serializers.CharField(required=False)
    permanent_password = serializers.CharField(required=False)
    ctx = serializers.CharField(required=False)

    def validate_permanent_password(self, value):
        # Field errors stop before validate(), so a code sent with a short password is not used up
        if value:
            password_validation.validate_password(value)
        return value

    def check_credentials(self, phone, password):
        """ Password field holds either SMS code or permanent password """
        user = ShopUser.objects.filter(phone=phone, is_active=True).first()
        if user is None or password is None:
            return None
        if LoginCode.verify(user, password):
            # Phone is proven: as always with SMS login, drop the password and sessions opened with it,
            # such as the one that created account silently. Staff need their password in admin.
            if not user.is_staff:
                user.set_unusable_password()
                user.permanent_password = False
            if not user.phone_verified:
                # Proven for the first time, so the account was created silently: whoever did it may have
                # confirmed their own address in it. The owner confirms it again, or changes it.
                user.phone_verified = True
                user.email_verified = False
            user.save()
            return user
        if user.permanent_password:  # otherwise it can only be a code left from when they were stored as passwords
            return self.check_password(phone, password)
        return None

    def check_password(self, phone, password):
        """
        Wrong passwords of a phone are limited, codes are not: whoever guesses passwords can't lock the owner out,
        a code from SMS logs in. The codes have limits of their own, attempts per code and codes per phone.
        """
        request, view = self.context.get('request'), self.context.get('view')
        limits = [PasswordFailureHourlyThrottle(phone), PasswordFailureDailyThrottle(phone)]
        for limit in limits:
            if not limit.allow_request(request, view):
                throttled = Throttled(detail=TOO_MANY_PASSWORDS)  # with the wait, the detail would add it in words
                throttled.wait = ceil(limit.wait())  # for Retry-After
                raise throttled
        user = authenticate(phone=phone, password=password)
        if user is None:
            for limit in limits:
                limit.failed()
        return user

    def validate(self, data):
        norm_phone = ShopUserManager.normalize_phone(data['phone'])
        exists = ShopUser.objects.filter(phone=norm_phone).exists()
        if not exists and data.get('ctx', None) in ('order', 'preorder', 'warranty'):
            # Silently create user if they are creating order or registering warranty. Phone
            # is not proven, so account gets no password until owner logs in with SMS code.
            user = ShopUser.objects.create_user(norm_phone)
            user.registered = True
            return user

        user = self.check_credentials(norm_phone, data.get('password'))
        if user:
            user.registered = False
            if 'permanent_password' in data and len(data['permanent_password']):
                user.set_password(data['permanent_password'])
                user.permanent_password = True
                user.save()
            return user

        raise serializers.ValidationError("Невозможно войти с указанными учетными данными")


class UserBonusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bonus
        fields = ('value', 'is_fresh', 'is_undefined', 'is_updating')
