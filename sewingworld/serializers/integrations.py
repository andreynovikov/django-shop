from django.db.models import Prefetch
from django.db.models.manager import BaseManager

from rest_framework import serializers

from shop.models import Category, Product, Stock, Integration

from .common import NonNullModelSerializer
from .catalog import ManufacturerSerializer, product_columns


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


class IntegrationProductListSerializer(serializers.ListSerializer):
    def to_representation(self, data):
        products = list(data.all() if isinstance(data, BaseManager) else data)
        if 'stock' in self.child.fields:
            # the stock of the whole feed at once, instead of queries for each product
            self.child.stocks = Product.get_stocks([product.pk for product in products], integration=self.context.get('integration'))
        return super().to_representation(products)


class IntegrationProductSerializer(serializers.ModelSerializer):
    categories = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()
    cost = serializers.SerializerMethodField()
    manufacturer = ManufacturerSerializer(read_only=True)
    instock = serializers.SerializerMethodField()
    stock = serializers.SerializerMethodField()

    stocks = None  # {product id: stock} of a list, see IntegrationProductListSerializer

    class Meta:
        model = Product
        fields = ('id', 'code', 'article', 'partnumber', 'gtin', 'isnew', 'whatis', 'whatisit', 'type_prefix', 'title', 'descr', 'yandexdescr',
                  'image', 'price', 'cost', 'enabled', 'categories', 'instock', 'stock', 'manufacturer', 'manufacturer_warranty',
                  'prom_weight', 'length', 'width', 'height', 'sales_notes', 'state')
        list_serializer_class = IntegrationProductListSerializer

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        integration = self.context.get('integration')
        request = self.context.get('request')
        if integration is not None:
            self.site = integration.source_site
            if integration.output_skip_categories:
                self.fields.pop('categories')
        else:
            self.site = request.site
        if integration is None or not integration.output_stock:
            self.fields.pop('stock')

    @classmethod
    def prefetch(cls, queryset):
        """ The products with what the feed needs read in a few queries, instead of queries for each product """
        return queryset.only(*product_columns(cls)).select_related('manufacturer').prefetch_related(
            'site_prices',
            Prefetch('categories', to_attr='active_categories', queryset=Category.objects.filter(active=True).only('id')),
        )

    def get_categories(self, obj):
        if hasattr(obj, 'active_categories'):  # see prefetch()
            return [category.pk for category in obj.active_categories]
        return list(obj.categories.filter(active=True).values_list('pk', flat=True))

    def get_price(self, obj):
        return obj.site_price(self.site)

    def get_cost(self, obj):
        return obj.site_cost(self.site)

    def get_instock(self, obj):
        return max(min(obj.instock, 10), 0)

    def get_stock(self, obj):
        if self.stocks is not None:
            return self.stocks[obj.pk]
        return obj.get_stock(integration=self.context.get('integration'))
