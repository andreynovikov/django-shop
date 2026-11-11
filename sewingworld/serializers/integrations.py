from rest_framework import serializers

from shop.models import Product, Stock, Integration

from .common import NonNullModelSerializer
from .catalog import ManufacturerSerializer


class StockSerializer(serializers.ModelSerializer):
    product = serializers.CharField(source='product.code')
    supplier = serializers.CharField(source='supplier.code')

    class Meta:
        model = Stock
        exclude = ('id',)


class IntegrationSerializer(NonNullModelSerializer):
    class Meta:
        model = Integration
        exclude = ('suppliers', 'products', 'settings')  # settings hold the marketplaces' API keys


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
