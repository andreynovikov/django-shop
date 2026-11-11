from rest_framework import serializers

from drf_spectacular.extensions import OpenApiSerializerExtension
from drf_spectacular.utils import Direction

from shop.models import Basket, BasketItem, Favorites, Product

from .common import NumberReadOnlyField, IntegerReadOnlyField, NonNullModelSerializer


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
        for name, value in validated_data.items():
            setattr(basket, name, value)
        basket.save()
        return basket


class BasketItemActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = BasketItem
        fields = ('product', 'quantity')
        extra_kwargs = {'quantity': {'required': False}}


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


class ComparisonSerializer(serializers.Serializer):
    product = serializers.IntegerField()

    def validate_product(self, value):
        product = Product.objects.filter(pk=value).first()
        if product is None:
            raise serializers.ValidationError("Product does not exist")
        return product
