import logging
import re
from collections import OrderedDict
from math import ceil
from urllib.parse import urlparse

from django.conf import settings
from django.contrib.auth import authenticate, password_validation
from django.core.files.storage import default_storage

from rest_framework import serializers
from rest_framework.exceptions import NotFound, Throttled

from drf_spectacular.extensions import OpenApiSerializerExtension
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import Direction, extend_schema_field, inline_serializer

from django.contrib.flatpages.models import FlatPage

from sewingworld.models import SiteProfile
from sewingworld.templatetags.gravatar import get_gravatar_url
from sewingworld.throttles import PasswordFailureHourlyThrottle, PasswordFailureDailyThrottle

from shop.filters import get_product_filter
from shop.models import Basket, BasketItem, Order, OrderItem, Favorites, Serial, \
    Category, Product, ProductRelation, ProductKind, Stock, ShopUser, ShopUserManager, LoginCode, Bonus, \
    Country, City, Store, StoreImage, ServiceCenter, News, Advert, SalesAction, Manufacturer, \
    Integration


logger = logging.getLogger("django")

EMAIL_TAKEN = "Пользователь с указанным адресом уже зарегестрирован"
TOO_MANY_PASSWORDS = "Слишком много попыток входа с неверным паролем. Войдите с кодом из смс."


@extend_schema_field(OpenApiTypes.NUMBER)
class NumberReadOnlyField(serializers.ReadOnlyField):
    # A Decimal or int property, rendered as a JSON number. The API schema can't tell the type of a property.
    pass


@extend_schema_field(OpenApiTypes.INT)
class IntegerReadOnlyField(serializers.ReadOnlyField):
    # An int property, see NumberReadOnlyField
    pass


class ErrorDetailSerializer(serializers.Serializer):
    # Body of DRF exceptions in the API schema, e.g. 403 Forbidden or 404 Not Found
    detail = serializers.CharField()


def validation_error_serializer(serializer_class):
    # Body of validation errors in the API schema: messages for each invalid field,
    # and messages of validate() under non_field_errors
    names = [name for name, field in serializer_class().fields.items() if not field.read_only]
    return inline_serializer(
        name=serializer_class.__name__.removesuffix('Serializer') + 'ValidationError',
        fields={
            name: serializers.ListField(child=serializers.CharField(), required=False)
            for name in [*names, 'non_field_errors']
        },
    )


class NonNullModelSerializer(serializers.ModelSerializer):
    def to_representation(self, instance):
        def keep(value):
            return not (value is None or (isinstance(value, str) and len(value) == 0) or (hasattr(value, '__len__') and len(value) == 0))

        result = super().to_representation(instance)
        return OrderedDict([(key, result[key]) for key in result if keep(result[key])])


class DynamicFieldsModelSerializer(NonNullModelSerializer):
    def __init__(self, *args, **kwargs):
        fields = kwargs.pop('fields', None)
        super().__init__(*args, **kwargs)

        if fields is not None:
            # Drop any fields that are not specified in the `fields` argument.
            allowed = set(fields)
            existing = set(self.fields)
            for field_name in existing - allowed:
                self.fields.pop(field_name)


class RecursiveField(serializers.Serializer):
    def to_representation(self, value):
        serializer = CategoryTreeSerializer(value, context=self.context)
        return serializer.data


class CountrySerializer(NonNullModelSerializer):
    class Meta:
        model = Country
        fields = ('id', 'name', 'enabled')


class CitySerializer(NonNullModelSerializer):
    country = CountrySerializer(read_only=True)

    class Meta:
        model = City
        fields = '__all__'  # TODO refactor


class StoreImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = StoreImage
        exclude = ('id', 'store')


class StoreListSerializer(NonNullModelSerializer):
    city = CitySerializer(read_only=True)
    phones = serializers.SerializerMethodField()

    class Meta:
        model = Store
        exclude = ('site', 'supplier', 'enabled')

    def get_phones(self, obj) -> list[str] | None:
        if not obj.phone:
            return None
        phones = obj.phone.split(',')
        if obj.phone2:
            phones.append(obj.phone2)
        return [phone.strip() for phone in phones]


class StoreSerializer(StoreListSerializer):
    images = StoreImageSerializer(many=True)


class ServiceCenterSerializer(NonNullModelSerializer):
    city = CitySerializer(read_only=True)

    class Meta:
        model = ServiceCenter
        exclude = ('enabled',)


class CategoryTreeSerializer(NonNullModelSerializer):
    children = RecursiveField(many=True, source='get_active_children')

    class Meta:
        model = Category
        fields = ('id', 'name', 'subname', 'active', 'hidden', 'feed', 'slug', 'svg_icon', 'image', 'children')


class CategoryBreadcrumbSerializer(serializers.Serializer):
    # For the API schema of CategoryPathSerializer
    id = serializers.IntegerField()
    slug = serializers.CharField()
    name = serializers.CharField()


class CategoryPathSerializer(serializers.Serializer):
    # For the API schema of the category path
    uri = serializers.CharField()
    breadcrumbs = CategoryBreadcrumbSerializer(many=True)


class CategoryBriefSerializer(NonNullModelSerializer):
    path = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ('id', 'name', 'subname', 'slug', 'path')

    @extend_schema_field(CategoryPathSerializer)
    def get_path(self, obj):
        ancestors = obj.get_ancestors(include_self=True)[1:]  # exclude root category
        uri = '/'.join([item.slug for item in ancestors])
        breadcrumbs = [{
            'id': item.id,
            'slug': item.slug,
            'name': item.name
        } for item in ancestors]
        return {
            'uri': uri,
            'breadcrumbs': breadcrumbs
        }


class CategorySerializer(NonNullModelSerializer):
    path = serializers.SerializerMethodField()
    children = RecursiveField(many=True, source='get_active_children')
    filters = serializers.SerializerMethodField()

    class Meta:
        model = Category
        exclude = ('active', 'hidden', 'feed', 'tree_id', 'lft', 'rght')

    @extend_schema_field(CategoryPathSerializer)
    def get_path(self, obj):
        ancestors = obj.get_ancestors(include_self=True)[1:]  # exclude root category
        uri = '/'.join([item.slug for item in ancestors])
        breadcrumbs = [{
            'id': item.id,
            'slug': item.slug,
            'name': item.name
        } for item in ancestors]
        return {
            'uri': uri,
            'breadcrumbs': breadcrumbs
        }

    # inline, because "class" can't be a field name
    @extend_schema_field(inline_serializer('CategoryFilter', fields={
        'name': serializers.CharField(),
        'id': serializers.CharField(),
        'class': serializers.CharField(),
        'label': serializers.CharField(),
        'widget': serializers.CharField(),
        'unit': serializers.CharField(required=False),
        'help': serializers.CharField(required=False),
    }, many=True, allow_null=True))
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
                filter['help'] = field.help_text
            filters.append(filter)
        return filters


class ProductKindSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductKind
        fields = '__all__'


class ManufacturerSerializer(NonNullModelSerializer):
    class Meta:
        model = Manufacturer
        fields = '__all__'  # TODO: refactor


class SalesActionSerializer(NonNullModelSerializer):
    class Meta:
        model = SalesAction
        exclude = ('active', 'show_in_list', 'order', 'sites')


class ProductImagesSerializer(serializers.BaseSerializer):  # BaseSerializer is used to be able to return list instead of dict
    def to_representation(self, obj):
        request = self.context.get('request')
        images = []
        for product_image in obj.all():
            images.append({
                'src': request.build_absolute_uri(product_image.image.url),
            })
        return images


class ProductImagesSerializerExtension(OpenApiSerializerExtension):
    target_class = ProductImagesSerializer

    def map_serializer(self, auto_schema, direction: Direction):
        item_schema = {
            'type': 'object',
            'properties': {
                'src': {'type': 'string', 'readOnly': True},
            },
        }
        return {
            'type': 'array',
            'items': item_schema
        }


class ProductListSerializer(DynamicFieldsModelSerializer):
    price = serializers.SerializerMethodField()
    cost = serializers.SerializerMethodField()
    instock = serializers.SerializerMethodField()
    sales = serializers.SerializerMethodField()
    rank = NumberReadOnlyField()  # annotated by the product search

    class Meta:
        model = Product
        fields = ('id', 'code', 'article', 'partnumber', 'order', 'whatis', 'whatisit', 'type_prefix', 'title', 'variations',
                  'price', 'cost', 'discount', 'instock', 'image', 'enabled', 'isnew', 'recomended',
                  'ws_pack_only', 'pack_factor', 'sales', 'sales_notes', 'shortdescr', 'rank',
                  'wb_link', 'ozon_link')

    def to_representation(self, instance):
        request = self.context.get('request')
        if request is not None:
            typeahead = request.GET.get('ta', None)
            if typeahead is not None:
                return instance.title
        return super().to_representation(instance)

    def get_price(self, obj) -> float:
        request = self.context.get('request')
        return obj.site_price(request.site)

    def get_cost(self, obj) -> float:
        request = self.context.get('request')
        return obj.site_cost(request.site)

    def get_instock(self, obj) -> int:
        return max(min(obj.instock, 10), 0)

    def get_sales(self, obj) -> list[str] | None:
        request = self.context.get('request')
        if request is not None:
            # TODO: put this in middleware
            domain = urlparse(request.META.get('HTTP_REFERER', '')).hostname
            if domain == 'cartzilla.sigalev.ru':  # TODO: put this in Sites config
                domain = 'www.sewing-world.ru'
            return list(obj.sales_actions.filter(active=True).exclude(notice='').order_by('order').values_list('notice', flat=True))  # , sites__domain=domain).order_by('order')
        return None


class ProductSerializer(NonNullModelSerializer):
    images = ProductImagesSerializer(read_only=True)
    country = CountrySerializer(read_only=True)
    developer_country = CountrySerializer(read_only=True)
    manufacturer = ManufacturerSerializer(read_only=True)
    categories = serializers.SerializerMethodField()
    constituents = ProductListSerializer(many=True, read_only=True)
    price = serializers.SerializerMethodField()
    cost = serializers.SerializerMethodField()
    accessories = serializers.SerializerMethodField()
    similar = serializers.SerializerMethodField()
    gifts = serializers.SerializerMethodField()
    sales = serializers.SerializerMethodField()
    stitches = serializers.SerializerMethodField()
    instock = serializers.ReadOnlyField()
    discount = serializers.ReadOnlyField()

    class Meta:
        model = Product
        exclude = ('sp_price', 'sp_cur_price', 'cur_price', 'max_discount', 'ws_max_discount',
                   'forbid_price_import', 'forbid_ws_price_import', 'show_on_sw', 'market', 'firstpage',
                   'num', 'recalculate_price', 'ws_cur_price', 'cur_code', 'ws_cur_code', 'sp_cur_code',
                   'sites', 'sales_actions', 'stock', 'related', 'bid', 'cbid', 'fts_vector')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['constituents'].context.update(self.context)

    @extend_schema_field(CategoryBriefSerializer(many=True))
    def get_categories(self, obj):
        request = self.context.get('request')
        root_category = request.site.profile.root_category
        categories = [
            c for c in obj.categories.all() if c.get_root() == root_category
        ]
        return CategoryBriefSerializer(categories, many=True).data

    def get_price(self, obj) -> float:
        request = self.context.get('request')
        return obj.site_price(request.site)

    def get_cost(self, obj) -> float:
        request = self.context.get('request')
        return obj.site_cost(request.site)

    def get_instock(self, obj):
        return obj.instock  # TODO: limit output

    @extend_schema_field(ProductListSerializer(many=True))
    def get_accessories(self, obj):
        request = self.context.get('request')
        accessories = obj.related.filter(
            child_products__child_product__enabled=True,
            child_products__child_product__sites=request.site,
            child_products__kind=ProductRelation.KIND_ACCESSORY
        )
        return ProductListSerializer(accessories, many=True, context=self.context).data

    @extend_schema_field(ProductListSerializer(many=True))
    def get_similar(self, obj):
        request = self.context.get('request')
        similar = obj.related.filter(
            child_products__child_product__enabled=True,
            child_products__child_product__sites=request.site,
            child_products__kind=ProductRelation.KIND_SIMILAR
        )
        return ProductListSerializer(similar, many=True, context=self.context).data

    @extend_schema_field(ProductListSerializer(many=True))
    def get_gifts(self, obj):
        request = self.context.get('request')
        gifts = obj.related.filter(
            child_products__child_product__enabled=True,
            child_products__child_product__sites=request.site,
            child_products__kind=ProductRelation.KIND_GIFT
        )
        return ProductListSerializer(gifts, many=True, context=self.context).data

    @extend_schema_field(SalesActionSerializer(many=True))
    def get_sales(self, obj):
        request = self.context.get('request')
        # TODO: put this in middleware
        domain = urlparse(request.META.get('HTTP_REFERER', '')).hostname
        if domain == 'cartzilla.sigalev.ru':  # TODO: put this in Sites config
            domain = 'www.sewing-world.ru'
        sales = obj.sales_actions.filter(active=True)  # , sites__domain=domain).order_by('order') - TODO!
        return SalesActionSerializer(sales, many=True, context=self.context).data

    def get_stitches(self, obj) -> str:
        filepath = 'images/{manufacturer}/stitches/{code}_stitches.jpg'.format(manufacturer=obj.manufacturer.code, code=obj.code)
        if default_storage.exists(filepath):
            request = self.context.get('request')
            img = '<div><img class="img-fluid" src="{src}" alt="Строчки швейной машины {title}" /></div>'.format(
                src=request.build_absolute_uri(settings.MEDIA_URL + filepath),
                title=obj.title
            )
            if obj.stitches:
                return obj.stitches + img
            else:
                return img
        return obj.stitches

    def to_representation(self, obj):
        data = super().to_representation(obj)
        if not data.get('categories'):
            raise NotFound()
        return data


class StockSerializer(serializers.ModelSerializer):
    product = serializers.CharField(source='product.code')
    supplier = serializers.CharField(source='supplier.code')

    class Meta:
        model = Stock
        exclude = ('id',)


class BasketItemProductSerializer(NonNullModelSerializer):
    price = serializers.SerializerMethodField()
    cost = serializers.SerializerMethodField()
    instock = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ('id', 'code', 'title', 'whatis', 'partnumber', 'article',
                  'ws_pack_only', 'pack_factor', 'price', 'cost', 'instock', 'image')

    def get_price(self, obj) -> float:
        request = self.context.get('request')
        return obj.site_price(request.site)

    def get_cost(self, obj) -> float:
        request = self.context.get('request')
        return obj.site_cost(request.site)

    def get_instock(self, obj) -> int:
        return max(min(obj.instock, 10), 0)


class BasketItemSerializer(serializers.ModelSerializer):
    product = BasketItemProductSerializer(read_only=True)
    cost = NumberReadOnlyField()
    discount = NumberReadOnlyField()
    discount_text = serializers.ReadOnlyField()
    price = NumberReadOnlyField()

    class Meta:
        model = BasketItem
        exclude = ('basket', 'meta', 'ext_discount')


class BasketSerializer(serializers.ModelSerializer):
    items = BasketItemSerializer(many=True, read_only=True)
    total = NumberReadOnlyField()
    quantity = IntegerReadOnlyField()

    class Meta:
        model = Basket
        exclude = ('created', 'secondary', 'session', 'site')

    def create(self, validated_data):
        request = self.context.get('request')
        request.session.save()  # ensure session is persisted
        request.session.modified = True
        basket, created = Basket.objects.get_or_create(site=request.site, session_id=request.session.session_key)
        basket.save(**validated_data)
        return basket


class BasketItemActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = BasketItem
        fields = ('product', 'quantity')
        extra_kwargs = {'quantity': {'required': False}}


class OrderItemSerializer(serializers.ModelSerializer):
    product = BasketItemProductSerializer(read_only=True)
    cost = NumberReadOnlyField()
    discount = NumberReadOnlyField()
    discount_text = serializers.ReadOnlyField()
    price = NumberReadOnlyField()

    class Meta:
        model = OrderItem
        fields = ('product', 'cost', 'price', 'product_price', 'quantity', 'total', 'discount', 'discount_text')


class OrderListSerializer(serializers.ModelSerializer):
    total = NumberReadOnlyField()
    status_text = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ('id', 'total', 'created', 'status', 'status_text', 'payment', 'paid')

    def get_status_text(self, obj) -> str:
        return obj.get_status_display()


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    total = NumberReadOnlyField()
    status_text = serializers.SerializerMethodField()
    payment_text = serializers.SerializerMethodField()
    store = StoreListSerializer(read_only=True, allow_null=True)

    class Meta:
        model = Order
        fields = ('id', 'created', 'status', 'status_text', 'payment', 'payment_text', 'paid', 'total',
                  'delivery', 'delivery_price', 'delivery_tracking_number', 'delivery_info',
                  'delivery_dispatch_date', 'delivery_handing_date', 'delivery_time_from', 'delivery_time_till',
                  'store', 'name', 'phone', 'email', 'address', 'is_firm', 'firm_name', 'firm_address', 'firm_details',
                  'items', 'comment')

    def get_status_text(self, obj) -> str:
        return obj.get_status_display()

    def get_payment_text(self, obj) -> str:
        return obj.get_payment_display()


class OrderActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ('name', 'email', 'address', 'comment')


class FavoritesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorites
        exclude = ('id', 'user', 'site')

    def to_representation(self, instance):
        return instance.product.id


class FavoritesSerializerExtension(OpenApiSerializerExtension):
    target_class = FavoritesSerializer

    def map_serializer(self, auto_schema, direction: Direction):
        # requests send the product, responses are product ids
        if direction == 'request':
            return auto_schema._map_serializer(self.target, direction, bypass_extensions=True)
        return {
            'type': 'integer',
        }


class SerialSerializer(serializers.ModelSerializer):
    class Meta:
        model = Serial
        exclude = ('id', 'user', 'comment')
        read_only_fields = ('purchase_date', 'product', 'order', 'approved')
        extra_kwargs = {
            'number': {'validators': []}  # we validate it in create method by ourselves
        }

    def create(self, validated_data):
        if validated_data['number'] is None or validated_data['number'].strip() == '':
            raise serializers.ValidationError("Необходимо указать серийный номер")
        request = self.context.get('request')
        serial = Serial.register(validated_data['number'], request.user)
        if serial is None:
            raise serializers.ValidationError("Серийный номер {} уже был ранее зарегистрирован".format(validated_data['number']))
        return serial


class ComparisonSerializer(serializers.Serializer):
    product = serializers.IntegerField()

    def validate_product(self, value):
        product = Product.objects.filter(pk=value).first()
        if product is None:
            raise serializers.ValidationError("Product does not exist")
        return product


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


class FlatPageListSerializer(serializers.ModelSerializer):
    class Meta:
        model = FlatPage
        fields = ('url', 'title')


class FlatPageSerializer(serializers.ModelSerializer):
    class Meta:
        model = FlatPage
        exclude = ('sites',)


class NewsSerializer(serializers.ModelSerializer):
    class Meta:
        model = News
        exclude = ('sites', 'active')


class AdvertSerializer(serializers.ModelSerializer):
    class Meta:
        model = Advert
        exclude = ('sites', 'active')


class SiteProfileSerializer(NonNullModelSerializer):
    id = serializers.SerializerMethodField()
    url_prefix = serializers.SerializerMethodField()
    city = CitySerializer(read_only=True)

    class Meta:
        model = SiteProfile
        fields = ('id', 'url_prefix', 'title', 'description', 'city', 'phone', 'wholesale')

    def get_id(self, obj) -> int:
        return obj.site.pk

    def get_url_prefix(self, obj) -> str:
        return 'https://' + obj.site.domain


class IntegrationSerializer(NonNullModelSerializer):
    class Meta:
        model = Integration
        exclude = ('suppliers', 'products')


class IntegrationProductSerializer(serializers.ModelSerializer):
    categories = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()
    cost = serializers.SerializerMethodField()
    manufacturer = ManufacturerSerializer(read_only=True)
    instock = serializers.SerializerMethodField()
    stock = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ('id', 'code', 'article', 'partnumber', 'gtin', 'isnew', 'whatis', 'whatisit', 'type_prefix', 'title', 'descr', 'yandexdescr',
                  'image', 'price', 'cost', 'enabled', 'categories', 'instock', 'stock', 'manufacturer', 'manufacturer_warranty',
                  'prom_weight', 'length', 'width', 'height', 'sales_notes', 'state')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        integration = self.context.get('integration')
        request = self.context.get('request')
        if integration is not None:
            self.site = integration.site
            if integration.output_skip_categories:
                self.fields.pop('categories')
        else:
            self.site = request.site
        if integration is None or not integration.output_stock:
            self.fields.pop('stock')

    def get_categories(self, obj):
        return list(obj.categories.filter(active=True).values_list('pk', flat=True))

    def get_price(self, obj):
        return obj.site_price(self.site)

    def get_cost(self, obj):
        return obj.site_cost(self.site)

    def get_instock(self, obj):
        return max(min(obj.instock, 10), 0)

    def get_stock(self, obj):
        return obj.get_stock(integration=self.context.get('integration'))
