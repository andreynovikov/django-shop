import logging
from collections import OrderedDict
from random import randint
from urllib.parse import urlparse

from django.conf import settings
from django.contrib.auth import authenticate
from django.core.files.storage import default_storage

from rest_framework import serializers

from sorl.thumbnail import get_thumbnail

from django.contrib.flatpages.models import FlatPage

from sewingworld.models import SiteProfile
from sewingworld.templatetags.gravatar import get_gravatar_url

from shop.filters import get_product_filter
from shop.models import Basket, BasketItem, Order, OrderItem, Favorites, \
    Category, Product, ProductRelation, ProductKind, ShopUser, ShopUserManager, Country, City, Store, \
    ServiceCenter, News, SalesAction, Manufacturer


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


class CountrySerializer(NonNullModelSerializer):
    class Meta:
        model = Country
        fields = ('id', 'name', 'enabled')


class CitySerializer(NonNullModelSerializer):
    country = CountrySerializer(read_only=True)

    class Meta:
        model = City
        fields = '__all__'  # TODO refactor


class StoreSerializer(NonNullModelSerializer):
    city = CitySerializer(read_only=True)

    class Meta:
        model = Store
        exclude = ('supplier', 'enabled')


class ServiceCenterSerializer(NonNullModelSerializer):
    city = CitySerializer(read_only=True)

    class Meta:
        model = ServiceCenter
        exclude = ('enabled',)


class CategoryTreeSerializer(NonNullModelSerializer):
    children = RecursiveField(many=True, source='get_active_children')

    class Meta:
        model = Category
        fields = ('id', 'name', 'slug', 'svg_icon', 'image', 'children')


class CategorySerializer(NonNullModelSerializer):
    path = serializers.SerializerMethodField()
    children = RecursiveField(many=True, source='get_active_children')
    filters = serializers.SerializerMethodField()

    class Meta:
        model = Category
        exclude = ('active', 'hidden', 'ya_active', 'tree_id', 'lft', 'rght')

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
            thumbnail = get_thumbnail(product_image.image, '80x80', padding=True)
            images.append({
                'src': request.build_absolute_uri(product_image.image.url),
                'thumbnail': {
                    'src': request.build_absolute_uri(thumbnail.url),
                    'width': thumbnail.width,
                    'height': thumbnail.height
                }
            })
        return images


class ProductListSerializer(NonNullModelSerializer):
    price = serializers.SerializerMethodField()
    cost = serializers.SerializerMethodField()
    instock = serializers.SerializerMethodField()
    thumbnail = serializers.SerializerMethodField()
    sales = serializers.SerializerMethodField()
    rank = serializers.ReadOnlyField()

    class Meta:
        model = Product
        fields = ('id', 'code', 'article', 'partnumber', 'whatis', 'title', 'variations', 'price',
                  'cost', 'discount', 'instock', 'image', 'thumbnail', 'enabled', 'isnew', 'recomended',
                  'ws_pack_only', 'pack_factor', 'sales', 'sales_notes', 'shortdescr', 'rank')

    def to_representation(self, instance):
        request = self.context.get('request')
        if request is not None:
            typeahead = request.GET.get('ta', None)
            if typeahead is not None:
                return instance.title
        return super().to_representation(instance)

    def get_price(self, obj):
        request = self.context.get('request')
        if request.site.profile.wholesale:
            return obj.ws_price
        else:
            return obj.price

    def get_cost(self, obj):
        request = self.context.get('request')
        if request.site.profile.wholesale:
            return obj.ws_cost
        else:
            return obj.cost

    def get_instock(self, obj):
        return max(min(obj.instock, 10), 0)

    def get_thumbnail(self, obj):
        if not obj.image:
            return None
        request = self.context.get('request')
        thumbnail_size = '{}x{}'.format(self.context.get('product_thumbnail_size'), self.context.get('product_thumbnail_size'))
        image = get_thumbnail(obj.image, thumbnail_size, padding=True, upscale=False)
        return {
            'url': request.build_absolute_uri(image.url),
            'width': image.width,
            'height': image.height
        }

    def get_sales(self, obj):
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
    thumbnail = serializers.SerializerMethodField()
    thumbnail_small = serializers.SerializerMethodField()
    country = CountrySerializer(read_only=True)
    developer_country = CountrySerializer(read_only=True)
    manufacturer = ManufacturerSerializer(read_only=True)
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
                   'sales_actions', 'categories', 'stock', 'related', 'image_prefix', 'bid', 'cbid', 'fts_vector')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['constituents'].context.update(self.context)

    def get_price(self, obj):
        request = self.context.get('request')
        if request.site.profile.wholesale:
            return obj.ws_price
        else:
            return obj.price

    def get_cost(self, obj):
        request = self.context.get('request')
        if request.site.profile.wholesale:
            return obj.ws_cost
        else:
            return obj.cost

    def get_instock(self, obj):
        return obj.instock  # TODO: limit output

    def get_thumbnail(self, obj):
        if not obj.image:
            return None
        request = self.context.get('request')
        thumbnail_size = '{}x{}'.format(self.context.get('product_thumbnail_size'), self.context.get('product_thumbnail_size'))
        image = get_thumbnail(obj.image, thumbnail_size, padding=True)
        return {
            'url': request.build_absolute_uri(image.url),
            'width': image.width,
            'height': image.height
        }

    def get_thumbnail_small(self, obj):
        if not obj.image:
            return None
        request = self.context.get('request')
        thumbnail_size = '{}x{}'.format(self.context.get('product_small_thumbnail_size'), self.context.get('product_small_thumbnail_size'))
        image = get_thumbnail(obj.image, thumbnail_size, padding=True)
        return {
            'url': request.build_absolute_uri(image.url),
            'width': image.width,
            'height': image.height
        }

    def get_accessories(self, obj):
        accessories = obj.related.filter(child_products__child_product__enabled=True, child_products__kind=ProductRelation.KIND_ACCESSORY)
        return ProductListSerializer(accessories, many=True, context=self.context).data

    def get_similar(self, obj):
        similar = obj.related.filter(child_products__child_product__enabled=True, child_products__kind=ProductRelation.KIND_SIMILAR)
        return ProductListSerializer(similar, many=True, context=self.context).data

    def get_gifts(self, obj):
        gifts = obj.related.filter(child_products__child_product__enabled=True, child_products__kind=ProductRelation.KIND_GIFT)
        return ProductListSerializer(gifts, many=True, context=self.context).data

    def get_sales(self, obj):
        request = self.context.get('request')
        # TODO: put this in middleware
        domain = urlparse(request.META.get('HTTP_REFERER', '')).hostname
        if domain == 'cartzilla.sigalev.ru':  # TODO: put this in Sites config
            domain = 'www.sewing-world.ru'
        sales = obj.sales_actions.filter(active=True)  # , sites__domain=domain).order_by('order') - TODO!
        return SalesActionSerializer(sales, many=True, context=self.context).data

    def get_stitches(self, obj):
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

class BasketItemProductSerializer(NonNullModelSerializer):
    price = serializers.SerializerMethodField()
    thumbnail = serializers.SerializerMethodField()
    thumbnail_small = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ('id', 'code', 'title', 'whatis', 'partnumber', 'article',
                  'ws_pack_only', 'pack_factor', 'price', 'thumbnail', 'thumbnail_small')

    def get_price(self, obj):
        request = self.context.get('request')
        if request.site.profile.wholesale:
            return obj.ws_price
        else:
            return obj.price

    def get_thumbnail(self, obj):
        if not obj.image:
            return None
        request = self.context.get('request')
        image = get_thumbnail(obj.image, '160x160', padding=True)
        return {
            'url': request.build_absolute_uri(image.url),
            'width': image.width,
            'height': image.height
        }

    def get_thumbnail_small(self, obj):
        if not obj.image:
            return None
        request = self.context.get('request')
        image = get_thumbnail(obj.image, '64x64', padding=True)
        return {
            'url': request.build_absolute_uri(image.url),
            'width': image.width,
            'height': image.height
        }


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
    cost = serializers.ReadOnlyField()
    discount = serializers.ReadOnlyField()
    discount_text = serializers.ReadOnlyField()
    price = serializers.ReadOnlyField()

    class Meta:
        model = OrderItem
        fields = ('product', 'cost', 'price', 'product_price', 'quantity', 'total', 'discount', 'discount_text')


class OrderListSerializer(serializers.ModelSerializer):
    total = serializers.ReadOnlyField()
    status_text = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ('id', 'total', 'created', 'status', 'status_text')

    def get_status_text(self, obj):
        return obj.get_status_display()


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    total = serializers.ReadOnlyField()
    status_text = serializers.SerializerMethodField()
    payment_text = serializers.SerializerMethodField()
    store = StoreSerializer(read_only=True)

    class Meta:
        model = Order
        fields = ('id', 'created', 'status', 'status_text', 'payment', 'payment_text', 'paid', 'total',
                  'delivery', 'delivery_price', 'delivery_tracking_number', 'delivery_info',
                  'delivery_dispatch_date', 'delivery_handing_date', 'delivery_time_from', 'delivery_time_till',
                  'store', 'name', 'phone', 'address', 'is_firm', 'firm_name', 'firm_address', 'firm_details',
                  'items')

    def get_status_text(self, obj):
        return obj.get_status_display()

    def get_payment_text(self, obj):
        return obj.get_payment_display()


class OrderActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ('name', 'email', 'address', 'comment')


class FavoritesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorites
        exclude = ('id', 'user')

    def to_representation(self, instance):
        return instance.product.id


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

    def get_full_name(self, obj):
        return obj.get_full_name()

    def get_gravatar(self, obj):
        return get_gravatar_url(obj, 90)


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

    class Meta:
        model = ShopUser
        exclude = ('groups', 'user_permissions', 'password', 'tags', 'is_superuser', 'is_active', 'is_staff', 'first_name', 'last_name')

    def get_full_name(self, obj):
        return obj.get_full_name()

    def get_gravatar(self, obj):
        return get_gravatar_url(obj, 90)

    def validate_phone(self, value):
        norm_phone = ShopUserManager.normalize_phone(value)
        another = ShopUser.objects.filter(phone=norm_phone).first()
        if another is not None and not (self.instance and another.id == self.instance.id):
            raise serializers.ValidationError("Пользователь с указанным номером уже зарегестрирован")
        return norm_phone

    def validate_email(self, value):
        if value == '':
            return value
        another = ShopUser.objects.filter(email=value).first()
        if another is not None and not (self.instance and another.id == self.instance.id):
            raise serializers.ValidationError("Пользователь с указанным адресом уже зарегестрирован")
        return value

    def validate_username(self, value):
        if value == '':
            return value
        another = ShopUser.objects.filter(username=value).first()
        if another is not None and not (self.instance and another.id == self.instance.id):
            raise serializers.ValidationError("Пользователь с указанным псевдонимом уже зарегестрирован")
        return value

    def create(self, validated_data):
        user = ShopUser(**validated_data)
        user.save()
        return user


class AnonymousUserSerializer(serializers.BaseSerializer):
    def to_representation(self, instance):
        return {
            'id': None,
            'is_anonymous': True
        }


class PhoneValidator:
    message = 'Mobile phone required'
    code = 'phone_required'

    def __call__(self, value):
        norm_phone = ShopUserManager.normalize_phone(value)
        if not norm_phone:
            raise serializers.ValidationError(self.message, code=self.code)


class LoginSerializer(serializers.Serializer):
    phone = serializers.CharField(validators=[PhoneValidator()])
    password = serializers.CharField(required=False)
    permanent_password = serializers.CharField(required=False)
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
            user.registered = True
        else:
            user = authenticate(**data)
            if user:
                user.registered = False

        if user and user.is_active:
            if 'permanent_password' in data and len(data['permanent_password']):
                user.set_password(data['permanent_password'])
                user.permanent_password = True
                user.save()
            return user

        raise serializers.ValidationError("Невозможно войти с указанными учетными данными")


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


class SiteProfileSerializer(NonNullModelSerializer):
    id = serializers.SerializerMethodField()
    city = CitySerializer(read_only=True)

    class Meta:
        model = SiteProfile
        fields = ('id', 'title', 'description', 'city', 'phone')

    def get_id(self, obj):
        return obj.site.pk
