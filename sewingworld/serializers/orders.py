from rest_framework import serializers

from shop.models import Order, OrderItem, Serial

from .common import NumberReadOnlyField
from .content import StoreListSerializer
from .shopping import BasketItemProductSerializer, ComparisonSerializer


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


class PreorderSerializer(ComparisonSerializer):
    """ The product to ask about, see OrderViewSet.preorder """
