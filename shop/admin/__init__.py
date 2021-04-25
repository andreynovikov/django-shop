from django.forms import ModelForm, TextInput
from django.urls import reverse
from django.db.models import PositiveSmallIntegerField, PositiveIntegerField, \
    DecimalField, FloatField, ImageField, Q
from django.core.exceptions import PermissionDenied
from django.contrib import admin
from django.template.response import TemplateResponse
from django.conf.urls import url
from django.utils.safestring import mark_safe

from adminsortable2.admin import SortableAdminMixin, SortableInlineAdminMixin
from django_admin_listfilter_dropdown.filters import DropdownFilter, RelatedDropdownFilter
from mptt.admin import DraggableMPTTAdmin
from reviews.admin import ReviewAdmin

from import_export import resources
from import_export.admin import ImportExportMixin

from sewingworld.admin import get_sites
from sewingworld.widgets import AutosizedTextarea
from shop.models import Category, Supplier, Contractor, Currency, Country, Region, City, \
    Store, StoreImage, ServiceCenter, Manufacturer, Advert, SalesAction, \
    Product, ProductRelation, ProductSet, ProductKind, Stock, ProductReview, \
    Manager, Courier, Order
from .widgets import ImageWidget
from .forms import ProductImportForm, ProductConfirmImportForm, ProductExportForm, \
    ProductAdminForm, ProductKindForm, StockInlineForm, CategoryAdminForm
from .decorators import admin_changelist_link
from .views import product_stock_view

from .order import OrderAdmin  # NOQA
from .act import ActAdmin  # NOQA
from .user import ShopUserAdmin  # NOQA


@admin.register(Category)
class CategoryAdmin(DraggableMPTTAdmin):
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    list_display = ('tree_actions', 'indented_title', 'slug', 'active', 'hidden')
    # list_editable = ['active']
    list_display_links = ['indented_title']
    exclude = ('image_width', 'image_height', 'promo_image_width', 'promo_image_height')
    form = CategoryAdminForm


@admin.register(Supplier)
class SupplierAdmin(SortableAdminMixin, admin.ModelAdmin):
    list_display = ['code', 'name', 'show_in_order', 'count_in_stock', 'spb_count_in_stock',
                    'ws_count_in_stock', 'beru_count_in_stock', 'taxi_count_in_stock']
    list_display_links = ['name']
    search_fields = ['code', 'code1c', 'name']


@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'rate']
    list_display_links = ['name']
    list_editable = ('rate',)
    ordering = ['code']


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'enabled']
    list_display_links = ['name']
    list_filter = ['enabled']
    search_fields = ['name']
    ordering = ['name']


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ['id', 'country', 'name']
    list_display_links = ['name']
    list_filter = ['country']
    search_fields = ['name']
    ordering = ['name']


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ['country', 'region', 'name', 'ename', 'code', 'latitude', 'longitude']
    list_display_links = ['name']
    list_filter = ['country', 'region']
    search_fields = ['name']
    ordering = ['name']


class StoreImageInline(SortableInlineAdminMixin, admin.TabularInline):
    model = StoreImage
    exclude = ('image_width', 'image_height')
    formfield_overrides = {
        ImageField: {
            'widget': ImageWidget
        }
    }
    extra = 2


@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ['city', 'address', 'name', 'supplier', 'enabled', 'latitude', 'longitude']
    list_display_links = ['address', 'name']
    list_filter = [('city', RelatedDropdownFilter), 'enabled', 'publish']
    search_fields = ['name', 'address', 'address2']
    ordering = ['city', 'address']
    inlines = [StoreImageInline]

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            url(r'^yandexmapfeed/$', self.admin_site.admin_view(self.yandex_map_feed_view), name='%s_%s_yandexmapfeed' % (self.model._meta.app_label, self.model._meta.model_name))
        ]
        return my_urls + urls

    def yandex_map_feed_view(self, request):
        if not request.user.is_staff:
            raise PermissionDenied
        stores = Store.objects.filter(publish=True)
        context = {
            'stores': stores,
            'cl': self,
            **self.admin_site.each_context(request)
        }
        return TemplateResponse(request, 'admin/shop/store/yandex_map_feed.xml', context, content_type='text/xml')


@admin.register(ServiceCenter)
class ServiceCenterAdmin(admin.ModelAdmin):
    list_display = ['city', 'address', 'enabled', 'latitude', 'longitude']
    list_display_links = ['address']
    list_filter = [('city', RelatedDropdownFilter), 'enabled']
    search_fields = ['address', 'city__name']
    ordering = ['city', 'address']


@admin.register(Manufacturer)
class ManufacturerAdmin(admin.ModelAdmin):
    list_display = ['id', 'code', 'name', 'machinemaker', 'accessorymaker', 'logo']
    list_display_links = ['name']
    list_filter = ['machinemaker', 'accessorymaker']
    search_fields = ['code', 'name']
    ordering = ['name']


@admin.register(Contractor)
class ContractorAdmin(admin.ModelAdmin):
    list_display = ['code', 'name']
    list_display_links = ['name']
    search_fields = ['name']
    ordering = ['code']


class AdvertAdminForm(ModelForm):
    class Meta:
        widgets = {
            'content': AutosizedTextarea(attrs={'rows': 15, 'style': 'width: 95%; max-height: 500px'}),
        }


@admin.register(Advert)
class AdvertAdmin(SortableAdminMixin, admin.ModelAdmin):
    list_display = ['name', 'place', get_sites, 'active']
    list_display_links = ['name']
    search_fields = ['name']
    list_filter = ['active', 'place']
    form = AdvertAdminForm


class SalesActionAdminForm(ModelForm):
    class Meta:
        widgets = {
            'brief': AutosizedTextarea(attrs={'rows': 3, 'style': 'width: 95%; max-height: 500px'}),
            'description': AutosizedTextarea(attrs={'rows': 10, 'style': 'width: 95%; max-height: 500px'}),
        }


@admin.register(SalesAction)
class SalesActionAdmin(SortableAdminMixin, admin.ModelAdmin):
    list_display = ['name', 'slug', get_sites, 'active', 'show_in_list']
    list_display_links = ['name']
    search_fields = ['name', 'slug']
    form = SalesActionAdminForm


@admin.register(ProductRelation)
class ProductRelationAdmin(admin.ModelAdmin):
    @mark_safe
    def parent_product_link(self, obj):
        return '<span style="white-space: normal!">%s</span>' % obj.parent_product.title
    parent_product_link.admin_order_field = 'parent_product'
    parent_product_link.short_description = 'товар'

    @mark_safe
    def child_product_link(self, obj):
        return '<span style="white-space: normal!">%s</span>' % obj.child_product.title
    child_product_link.admin_order_field = 'child_product'
    child_product_link.short_description = 'связанный товар'

    list_display = ['parent_product_link', 'child_product_link', 'kind']
    list_display_links = ['parent_product_link', 'child_product_link']
    list_filter = ['kind']
    search_fields = ['parent_product__title', 'parent_product__code', 'parent_product__article', 'parent_product__partnumber',
                     'child_product__title', 'child_product__code', 'child_product__article', 'child_product__partnumber']
    autocomplete_fields = ('parent_product', 'child_product')


class StockInline(admin.TabularInline):
    model = Stock
    form = StockInlineForm
    fields = ['supplier', 'quantity', 'correction', 'reason']
    extra = 0
    classes = ['collapse']
    suit_classes = 'suit-tab suit-tab-stock'
    formfield_overrides = {
        FloatField: {'widget': TextInput(attrs={'style': 'width: 8em'})},
    }

    def has_delete_permission(self, request, obj=None):
        return obj is None  # False


class ProductSetInline(admin.TabularInline):
    model = ProductSet
    fk_name = 'declaration'
    ordering = ('constituent__title',)
    autocomplete_fields = ('constituent',)
    extra = 0
    verbose_name = "составляющая"
    verbose_name_plural = "составляющие"
    suit_classes = 'suit-tab suit-tab-set'


class ProductRelationInline(admin.TabularInline):
    model = ProductRelation
    fk_name = 'parent_product'
    ordering = ('kind',)
    autocomplete_fields = ('child_product',)
    extra = 0
    verbose_name = "связанный товар"
    verbose_name_plural = "связанные товары"
    classes = ['collapse']
    suit_classes = 'suit-tab suit-tab-related'


class ProductResource(resources.ModelResource):
    def __init__(self, **kwargs):
        super().__init__()
        self.id_field = kwargs.get('id_field', 'id')
        self.export_fields = kwargs.get('export_fields', [])

    def get_import_id_fields(self):
        return (self.id_field,)

    def get_export_fields(self):
        if self.export_fields:
            return filter(lambda f: f.attribute in self.export_fields, self.get_fields())
        else:
            return self.get_fields()  # import uses same list as export

    class Meta:
        model = Product
        exclude = ('categories', 'stock', 'num', 'spb_num', 'ws_num', 'related', 'constituents', 'image_prefix')


@admin.register(Product)
class ProductAdmin(ImportExportMixin, admin.ModelAdmin):
    @mark_safe
    def product_codes(self, obj):
        code = obj.code or '--'
        article = obj.article or '--'
        partnumber = obj.partnumber or '--'
        return '<br/>'.join([code, article, partnumber])
    product_codes.admin_order_field = 'code'
    product_codes.short_description = 'Ид/1С/PN'

    @mark_safe
    def combined_price(self, obj):
        result = '%s&nbsp;руб' % obj.price
        if obj.forbid_price_import:
            result = result + '&nbsp;<span style="color: red">&#10004;</span>'
        if not obj.cur_code.code == 643:
            result = result + '<br/>%s&nbsp;%s' % (obj.cur_price, obj.cur_code)
        return result
    combined_price.admin_order_field = 'price'
    combined_price.short_description = 'цена'

    @mark_safe
    def combined_discount(self, obj):
        return '%s&nbsp;руб<br/>%s%%' % (obj.val_discount, obj.pct_discount)
    combined_discount.short_description = 'скидка'

    def product_stock(self, obj):
        return product_stock_view(obj)
    product_stock.short_description = 'склад'

    @admin_changelist_link(None, 'з', model=Order, query_string=lambda p: 'item__product__pk={}'.format(p.pk))
    def orders_link(self, orders):
        return '<i class="fas fa-dolly"></i>'

    @mark_safe
    def product_link(self, obj):
        url = reverse('product', args=[obj.code])
        return '<a href="%s" target="_blank"><i class="fas fa-external-link-alt"></i></a>' % url
    product_link.short_description = 'о'

    form = ProductAdminForm
    change_list_template = 'admin/shop/product/change_list.html'
    resource_class = ProductResource
    list_display = ['product_codes', 'title', 'combined_price', 'beru_price', 'combined_discount', 'enabled', 'show_on_sw', 'avito', 'beru', 'taxi',
                    'market', 'spb_market', 'merchant', 'product_stock', 'orders_link', 'product_link']
    list_display_links = ['title']
    list_editable = ['enabled', 'show_on_sw', 'avito', 'beru', 'taxi', 'market', 'spb_market', 'merchant']
    list_filter = ['enabled', 'show_on_sw', 'avito', 'beru', 'taxi', 'market', 'isnew', 'recomended',
                   'cur_code', ('pct_discount', DropdownFilter), ('val_discount', DropdownFilter),
                   ('categories', RelatedDropdownFilter), ('manufacturer', RelatedDropdownFilter)]
    exclude = ['image_prefix']
    search_fields = ['code', 'article', 'partnumber', 'title', 'tags']
    readonly_fields = ['price', 'ws_price', 'sp_price']
    save_as = True
    save_on_top = True
    view_on_site = True
    inlines = (ProductSetInline, ProductRelationInline, StockInline,)
    filter_vertical = ('categories',)
    autocomplete_fields = ('manufacturer',)
    formfield_overrides = {
        PositiveSmallIntegerField: {'widget': TextInput(attrs={'style': 'width: 4em'})},
        PositiveIntegerField: {'widget': TextInput(attrs={'style': 'width: 8em'})},
        DecimalField: {'widget': TextInput(attrs={'style': 'width: 4em'})},
        FloatField: {'widget': TextInput(attrs={'style': 'width: 4em'})},
    }
    spb_fieldset = ('С.Петербург', {
        'classes': ('collapse', 'suit-tab', 'suit-tab-money'),
        'fields': ('spb_price', 'forbid_spb_price_import', 'spb_show_in_catalog', 'spb_market')
    })
    fieldsets = (
        ('Основное', {
            'classes': ('collapse', 'suit-tab', 'suit-tab-general'),
            'fields': (('code', 'article', 'partnumber'), 'title', 'runame', 'whatis', 'kind', 'categories', ('manufacturer', 'gtin'),
                       ('country', 'developer_country'), 'variations', 'spec', 'shortdescr', 'yandexdescr', 'descr', 'manuals', 'state',
                       'complect', 'dealertxt')
        }),
        ('Деньги', {
            'classes': ('collapse', 'suit-tab', 'suit-tab-money'),
            'fields': (('cur_price', 'cur_code', 'price'), ('pct_discount', 'val_discount', 'max_discount', 'max_val_discount'),
                       ('ws_cur_price', 'ws_cur_code', 'ws_price'), 'ws_pack_only', ('ws_pct_discount', 'ws_max_discount'),
                       ('sp_cur_price', 'sp_cur_code', 'sp_price'), ('beru_price', 'avito_price'), 'consultant_delivery_price',
                       ('forbid_price_import', 'forbid_ws_price_import'))
        }),
        ('Маркетинг', {
            'classes': ('collapse', 'suit-tab', 'suit-tab-money'),
            'fields': (('enabled', 'show_on_sw', 'firstpage'), ('merchant', 'market', 'beru', 'avito', 'taxi'), ('isnew', 'recomended', 'gift'), 'credit_allowed', 'deshevle',
                       'sales_notes', 'present', 'delivery', 'sales_actions', 'tags')
        }),
        spb_fieldset,
        ('Размеры', {
            'classes': ('collapse', 'suit-tab', 'suit-tab-general'),
            'fields': (('measure', 'pack_factor'), ('weight', 'prom_weight'), ('length', 'width', 'height'))
        }),
        ('Вязальные машины', {
            'classes': ('collapse', 'suit-tab', 'suit-tab-knittingmachines'),
            'fields': ('km_class', 'km_needles', 'km_font', 'km_prog', 'km_rapport')
        }),
        ('Швейные машины', {
            'classes': ('collapse', 'suit-tab', 'suit-tab-sewingmachines'),
            'fields': ('stitches', 'fabric_verylite', 'fabric_lite', 'fabric_medium', 'fabric_hard', 'fabric_veryhard', 'fabric_stretch',
                       'fabric_leather', 'sm_shuttletype', 'sm_stitchwidth', 'sm_stitchlenght', 'sm_stitchquantity', 'sm_buttonhole', 'sm_dualtransporter',
                       'sm_platformlenght', 'sm_freearm', 'ov_freearm', 'sm_feedwidth', 'sm_footheight', 'sm_constant', 'sm_speedcontrol', 'sm_needleupdown',
                       'sm_threader',
                       'sm_spool',
                       'sm_presscontrol',
                       'sm_power',
                       'sm_light',
                       'sm_organizer',
                       'sm_autostop',
                       'sm_ruler',
                       'sm_wastebin',
                       'sm_cover',
                       'sm_startstop',
                       'sm_kneelift',
                       'sm_display',
                       'sm_advisor',
                       'sm_memory',
                       'sm_mirror',
                       'sm_fix',
                       'sm_alphabet',
                       'sm_diffeed',
                       'sm_easythreading',
                       'sm_needles',
                       'sm_software',
                       'sm_autocutter',
                       'sm_maxi',
                       'sm_autobuttonhole_bool',
                       'sm_threader_bool',
                       'sm_dualtransporter_bool',
                       'sm_alphabet_bool',
                       'sm_maxi_bool',
                       'sm_patterncreation_bool',
                       'sm_advisor_bool',
                       'sw_datalink',
                       'sw_hoopsize')
        }),
        ('Гарантия', {
            'classes': ('collapse', 'suit-tab', 'suit-tab-general'),
            'fields': ('warranty', 'extended_warranty', 'manufacturer_warranty')
        }),
        ('Остальное', {
            'classes': ('collapse', 'suit-tab', 'suit-tab-other'),
            'fields': (
                'order',
                'swcode',
                'coupon',
                'not_for_sale',
                'absent',
                'suspend',
                'opinion',
                'allow_reviews',
                ('bid', 'cbid'),
                'whatisit',
            )
        }),
        ('Промышленные машины', {
            'classes': ('collapse', 'suit-tab', 'suit-tab-prommachines'),
            'fields': (
                'prom_transporter_type',
                'prom_shuttle_type',
                'prom_speed',
                'prom_needle_type',
                'prom_stitch_lenght',
                'prom_foot_lift',
                'prom_fabric_type',
                'prom_oil_type',
                'prom_cutting',
                'prom_threads_num',
                'prom_power',
                'prom_bhlenght',
                'prom_overstitch_lenght',
                'prom_overstitch_width',
                'prom_stitch_width',
                'prom_needle_width',
                'prom_needle_num',
                'prom_platform_type',
                'prom_button_diaouter',
                'prom_button_diainner',
                'prom_needle_height',
                'prom_stitch_type',
                'prom_autothread'
            )
        }),
        ('Комплект', {
            'classes': ('collapse', 'suit-tab', 'suit-tab-set'),
            'fields': ('recalculate_price', 'hide_contents')
        }),
    )

    def get_fieldsets(self, request, obj=None):
        if not request.user.is_superuser and request.user.has_perm('shop.change_order_spb'):
            self.spb_fieldset[1].pop('classes', None)
            return (self.spb_fieldset,)
        else:
            return super().get_fieldsets(request, obj=obj)

    def get_formsets_with_inlines(self, request, obj=None):
        for inline in self.get_inline_instances(request, obj):
            if request.user.is_superuser or not request.user.has_perm('shop.change_order_spb'):
                yield inline.get_formset(request, obj), inline

    def get_import_form(self):
        return ProductImportForm

    def get_confirm_import_form(self):
        return ProductConfirmImportForm

    def get_export_form(self):
        return ProductExportForm

    def get_form_kwargs(self, form, *args, **kwargs):
        if not isinstance(form, type) and form.is_valid():
            kwargs.update({'id_field': form.cleaned_data['id_field']})
        return kwargs

    def get_import_resource_kwargs(self, request, *args, **kwargs):
        if request.POST:
            form = self.get_confirm_import_form()(request.POST)
            form.full_clean()
            return {'id_field': form.cleaned_data['id_field']}
        else:
            return {}

    def get_export_resource_kwargs(self, request, *args, **kwargs):
        if request.POST:
            formats = self.get_export_formats()
            form = self.get_export_form()(formats, request.POST)
            form.full_clean()
            return {'export_fields': form.cleaned_data['export_fields']}
        else:
            return {}

    # обновляем кеш наличия при сохранении
    def save_model(self, request, obj, form, change):
        if change:
            obj.num = obj.get_stock('num')
            obj.spb_num = obj.get_stock('spb_num')
            obj.ws_num = obj.get_stock('ws_num')
        else:
            obj.num = -1
            obj.spb_num = -1
            obj.ws_num = -1
        super().save_model(request, obj, form, change)

    def save_related(self, request, form, formsets, change):
        # this is a hack to avoid stock saving for duplicated products (gives error if stock correction is not zero)
        if '_saveasnew' in request.POST:
            to_remove = [i for i, formset in enumerate(formsets) if isinstance(formset.empty_form.instance, Stock)]
            for index in reversed(to_remove):
                # start at the end to avoid recomputing offsets
                del formsets[index]
        super().save_related(request, form, formsets, change)

    def get_urls(self):
        urls = super().get_urls()
        info = self.get_model_info()
        my_urls = [
            url(r'(\d+)/stock/$', self.admin_site.admin_view(self.stock_view), name='%s_%s_stock' % info),
            url(r'^stock/correction/$', self.admin_site.admin_view(self.stock_correction_view), name='%s_%s_stock_correction' % info),
        ]
        return my_urls + urls

    def stock_view(self, request, id):
        if not request.user.is_staff:
            raise PermissionDenied
        product = Product.objects.get(pk=id)
        stock = product.stock_items.all().order_by('supplier__order')
        context = {
            'title': 'Запасы %s' % str(product),
            'product': product,
            'stock': stock,
            'cl': self,
            'is_popup': request.GET.get('_popup', 0),
            **self.admin_site.each_context(request)
        }
        return TemplateResponse(request, 'admin/shop/product/stock.html', context)

    def stock_correction_view(self, request):
        if not request.user.is_staff:
            raise PermissionDenied
        sort = request.GET.get('o', 'product__title')
        stock = Stock.objects.filter(~Q(correction=0)).order_by(sort)
        context = {
            'title': 'Коррекция склада',
            'stock': stock,
            'o': sort,
            'cl': self,
            **self.admin_site.each_context(request)
        }
        return TemplateResponse(request, 'admin/shop/product/stock_correction.html', context)


@admin.register(ProductKind)
class ProductKindAdmin(admin.ModelAdmin):
    form = ProductKindForm
    list_display = ['name']
    list_display_links = ['name']
    search_fields = ['name']
    ordering = ['name']


@admin.register(Manager)
class ManagerAdmin(admin.ModelAdmin):
    @mark_safe
    def colorbar(self, obj):
        return '<div style="width: 40px; background-color: ' + obj.color + '">&nbsp;</div>'
    colorbar.admin_order_field = 'color'
    colorbar.short_description = 'цвет'

    list_display = ['name', 'colorbar']
    list_display_links = ['name']
    search_fields = ['name']
    ordering = ['name']


@admin.register(Courier)
class CourierAdmin(admin.ModelAdmin):
    @mark_safe
    def colorbar(self, obj):
        return '<div style="width: 40px; background-color: ' + obj.color + '">&nbsp;</div>'
    colorbar.admin_order_field = 'color'
    colorbar.short_description = 'цвет'

    list_display = ['name', 'colorbar', 'pos_id']
    list_display_links = ['name']
    search_fields = ['name']
    ordering = ['name']


# Register default ReviewAdmin as it suits our model
admin.site.register(ProductReview, ReviewAdmin)
