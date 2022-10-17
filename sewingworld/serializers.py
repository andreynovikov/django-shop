import logging
from collections import OrderedDict
from random import randint

from django.contrib.auth import authenticate
from django.contrib.auth.models import AnonymousUser
from django.core.files.storage import default_storage

from rest_framework import serializers

from sorl.thumbnail import get_thumbnail

from django.contrib.flatpages.models import FlatPage

from shop.filters import get_product_filter
from shop.models import Basket, BasketItem, Category, Product, ShopUser, ShopUserManager

logger = logging.getLogger("django")


class NonNullModelSerializer(serializers.ModelSerializer):
    def to_representation(self, instance):
        def keep(value):
            return not (value is None or (isinstance(value, str) and len(value) == 0) or (hasattr(value, '__len__') and len(value) == 0))

        result = super().to_representation(instance)
        return OrderedDict([(key, result[key]) for key in result if keep(result[key])])


class RecursiveField(serializers.Serializer):
    def to_representation(self, value):
        serializer = CategoryTreeSerializer(value, context=self.context)
        return serializer.data


class CategoryTreeSerializer(NonNullModelSerializer):
    children = RecursiveField(many=True, source='get_active_children')

    class Meta:
        model = Category
        fields=('id', 'name', 'slug', 'children')


class CategorySerializer(NonNullModelSerializer):
    path = serializers.SerializerMethodField()
    children = RecursiveField(many=True, source='get_active_children')
    filters = serializers.SerializerMethodField()

    class Meta:
        model = Category
        exclude = ('active', 'hidden', 'ya_active', 'lft', 'rght')

    def get_path(self, obj):
        return obj.get_path()

    def get_filters(self, obj):
        request = self.context.get('request')
        if not obj.filters:
            return None
        fields = obj.filters.split(',')
        product_filter = get_product_filter(request.query_params, queryset=Product.objects.none(), fields=fields, request=request)
        filters = []
        for field in product_filter.form.visible_fields():
            if field.name == 'enabled':
                continue
            field_label = field.label.split(',')
            filter = {
                'name': field.name,
                'id': field.id_for_label,
                'class': field.field.__class__.__name__,
                'label': field_label[0],
                'widget': field.field.widget.__class__.__name__,
            }
            if len(field_label) > 1:
                filter['unit'] = field_label[1].strip()
            if field.help_text:
                filter['help'] =  field.help_text
            filters.append(filter)
        return filters


class ProductListSerializer(NonNullModelSerializer):
    instock = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()
    thumbnail = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ('id', 'code', 'article', 'partnumber', 'whatis', 'title', 'variations', 'price', 'cost', 'discount', 'instock', 'image', 'thumbnail')

    def get_instock(self, obj):
        return obj.instock > 0

    def get_image(self, obj):
        if not obj.image_prefix:
            return None
        filepath = obj.image_prefix + '.jpg'
        if default_storage.exists(filepath):
            return default_storage.base_url + filepath
        else:
            return None

    def get_thumbnail(self, obj):
        if not obj.image_prefix:
            return None
        filepath = obj.image_prefix + '.jpg'
        if default_storage.exists(filepath):
            image = get_thumbnail(filepath, '200x200', padding=True)
            return {
                'url': image.url,
                'width': image.width,
                'height': image.height
            }
        else:
            return None


class ProductSerializer(NonNullModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'


class BasketItemProductSerializer(NonNullModelSerializer):
    thumbnail = serializers.SerializerMethodField()
    thumbnail_small = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ('id', 'title', 'whatis', 'price', 'thumbnail', 'thumbnail_small')

    def get_thumbnail(self, obj):
        if not obj.image_prefix:
            return None
        filepath = obj.image_prefix + '.jpg'
        if default_storage.exists(filepath):
            image = get_thumbnail(filepath, '160x160', padding=True)
            return {
                'url': image.url,
                'width': image.width,
                'height': image.height
            }
        else:
            return None

    def get_thumbnail_small(self, obj):
        if not obj.image_prefix:
            return None
        filepath = obj.image_prefix + '.jpg'
        if default_storage.exists(filepath):
            image = get_thumbnail(filepath, '64x64', padding=True)
            return {
                'url': image.url,
                'width': image.width,
                'height': image.height
            }
        else:
            return None


class BasketItemSerializer(serializers.ModelSerializer):
    product = BasketItemProductSerializer(read_only=True)
    cost = serializers.ReadOnlyField()
    discount = serializers.ReadOnlyField()
    discount_text = serializers.ReadOnlyField()
    price = serializers.ReadOnlyField()

    class Meta:
        model = BasketItem
        exclude = ('basket', 'meta', 'ext_discount')


class BasketSerializer(serializers.ModelSerializer):
    items = BasketItemSerializer(many=True, read_only=True)
    total = serializers.ReadOnlyField()
    quantity = serializers.ReadOnlyField()

    class Meta:
        model = Basket
        exclude = ('created', 'secondary', 'session')

    def create(self, validated_data):
        request = self.context.get('request')
        request.session.save()  # ensure session is persisted
        request.session.modified = True
        basket, created = Basket.objects.get_or_create(session_id=request.session.session_key)
        basket.save(**validated_data)
        return basket


class BasketItemActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = BasketItem
        fields = ('product', 'quantity')
        extra_kwargs = {'quantity': {'required': False}}


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShopUser
        exclude = ('groups', 'user_permissions', 'password', 'tags')


class AnonymousUserSerializer(serializers.BaseSerializer):
    def to_representation(self, instance):
        return {
            'is_anonymous': True
        }


class PhoneValidator:
    message = 'Mobile phone required'
    code = 'phone_required'

    def __call__(self, value):
        norm_phone = ShopUserManager.normalize_phone(value)
        if not norm_phone:
            raise ValidationError(self.message, code=self.code)


class LoginSerializer(serializers.Serializer):
    phone = serializers.CharField(validators=[PhoneValidator()])
    password = serializers.CharField(required=False)
    ctx = serializers.CharField(required=False)

    def validate(self, data):
        norm_phone = ShopUserManager.normalize_phone(data['phone'])
        exists = ShopUser.objects.filter(phone=norm_phone).exists()
        if not exists and data.get('ctx', None) == 'order':
            # Silently create user if they are creating order
            user = ShopUser.objects.create(phone=norm_phone)
            password = str(randint(1000, 9999))
            user.set_password(password)
            user.save()
            user = authenticate(phone=norm_phone, password=password)
        else:
            user = authenticate(**data)

        if user and user.is_active:
            return user

        raise serializers.ValidationError("Unable to log in with provided credentials")


class FlatPageListSerializer(serializers.ModelSerializer):
    class Meta:
        model = FlatPage
        fields = ('url', 'title')


class FlatPageSerializer(serializers.ModelSerializer):
    class Meta:
        model = FlatPage
        exclude = ('sites',)
