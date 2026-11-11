from urllib.parse import urlparse

from django.conf import settings
from django.core.files.storage import default_storage

from rest_framework import serializers
from rest_framework.exceptions import NotFound

from drf_spectacular.extensions import OpenApiSerializerExtension
from drf_spectacular.utils import Direction, extend_schema_field, inline_serializer

from shop.filters import get_product_filter
from shop.models import Category, Product, ProductRelation, ProductKind, Manufacturer

from .common import NumberReadOnlyField, NonNullModelSerializer, DynamicFieldsModelSerializer
from .content import CountrySerializer, SalesActionSerializer


class RecursiveField(serializers.Serializer):
    def to_representation(self, value):
        serializer = CategoryTreeSerializer(value, context=self.context)
        return serializer.data


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
