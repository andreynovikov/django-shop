import datetime

from decimal import Decimal, ROUND_UP

from django import forms
from django.urls import reverse
from django.db import connection
from django.db.models import TextField, PositiveSmallIntegerField, PositiveIntegerField, \
    TimeField, DateTimeField, DecimalField, FloatField, Q
from django.contrib import admin, messages
from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.http import HttpResponse, HttpResponseRedirect
from django.template.loader import get_template
from django.template.defaultfilters import floatformat
from django.template.response import TemplateResponse
from django.conf import settings
from django.conf.urls import url
from django.shortcuts import render
from django.utils import timezone
from django.utils.formats import date_format, number_format
from django.utils.html import escape
from django.utils.http import urlquote
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext, ugettext_lazy as _

#import autocomplete_light
#from suit.widgets import AutosizedTextarea
from daterangefilter.filters import FutureDateRangeFilter, PastDateRangeFilter
from adminsortable2.admin import SortableAdminMixin
from django_admin_listfilter_dropdown.filters import DropdownFilter, ChoiceDropdownFilter, RelatedDropdownFilter
from mptt.admin import DraggableMPTTAdmin
from lock_tokens.admin import LockableModelAdmin
from tagging.models import Tag, TaggedItem
from tagging.utils import parse_tag_input

from import_export import resources
from import_export.admin import ImportExportMixin, ExportMixin

from yandex_delivery.api import DeliveryClient

from utility.admin import get_sites
from shop.models import ShopUserManager, ShopUser, Category, Supplier, Contractor, \
    Currency, Country, Region, City, Store, ServiceCenter, Manufacturer, Advert, \
    Product, ProductRelation, ProductSet, ProductKind, SalesAction, Stock, Basket, BasketItem, \
    Manager, Courier, Order, OrderItem
from shop.forms import WarrantyCardPrintForm, OrderAdminForm, OrderCombineForm, \
    OrderDiscountForm, SendSmsForm, SelectTagForm, SelectSupplierForm, ProductAdminForm, \
    ProductKindForm, OrderItemInlineAdminForm, StockInlineForm, YandexDeliveryForm
from shop.widgets import TagAutoComplete
from shop.decorators import admin_changelist_link
from shop.tasks import send_message

from django.apps import AppConfig


def product_stock_view(product, order=None):
    result = ''
    if product.constituents.count() == 0:
        suppliers = product.stock.filter(show_in_order=True).order_by('order')
        if suppliers.exists():
            for supplier in suppliers:
                stock = Stock.objects.get(product=product, supplier=supplier)
                result = result + ('%s:&nbsp;' % supplier.code)
                if stock.quantity == 0:
                    result = result + '<span style="color: #c00">'
                result = result + ('%s' % floatformat(stock.quantity))
                if stock.quantity == 0:
                    result = result + '</span>'
                if stock.correction != 0.0:
                    result = result + '<span style="color: '
                    if stock.correction > 0.0:
                        result = result + '#090'
                    else:
                        result = result + '#c00'
                    result = result + ('" title="%s">' % escape(stock.reason))
                    if stock.correction > 0.0:
                        result = result + '+'
                    result = result + ('%s</span>' % floatformat(stock.correction))
                result = result + '<br/>'
        else:
            result = '<span style="color: #f00">отсутствует</span><br/>'
        if order:
            cursor = connection.cursor()
            cursor.execute("""SELECT shop_orderitem.order_id, shop_orderitem.quantity AS quantity FROM shop_orderitem
                              INNER JOIN shop_order ON (shop_orderitem.order_id = shop_order.id) WHERE shop_order.status IN (0,1,4,64,256,1024)
                              AND shop_orderitem.product_id = %s AND shop_order.id != %s""", (product.id, order.id))
            if cursor.rowcount:
                ordered = 0
                ids = [str(order.id)]
                for row in cursor:
                    ids.append(str(row[0]))
                    ordered = ordered + int(row[1])
                url = '%s?id__in=%s&status=all' % (reverse("admin:shop_order_changelist"), ','.join(ids))
                result = result + '<a href="%s" style="color: #00c">Зак:&nbsp;%s<br/></a>' % (url, floatformat(ordered))
            cursor.close()
    else:
        result = floatformat(product.instock)
    return mark_safe(result)


class CategoryForm(forms.ModelForm):
    class Meta:
        widgets = {
            #'brief': AutosizedTextarea(attrs={'rows': 3,}),
            #'description': AutosizedTextarea(attrs={'rows': 3,}),
        }


@admin.register(Category)
class CategoryAdmin(DraggableMPTTAdmin):
    search_fields = ('name','slug')
    prepopulated_fields = {'slug': ('name',)}
    list_display = ('tree_actions', 'indented_title', 'slug', 'active')
    #list_editable = ['active']
    list_display_links = ['indented_title']
    exclude = ('image_width', 'image_height', 'promo_image_width', 'promo_image_height')
    form = CategoryForm


@admin.register(Supplier)
class SupplierAdmin(SortableAdminMixin, admin.ModelAdmin):
    list_display = ['code', 'name', 'show_in_order', 'count_in_stock', 'spb_count_in_stock', 'ws_count_in_stock']
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


@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ['city', 'address', 'name', 'supplier', 'enabled', 'latitude', 'longitude']
    list_display_links = ['address', 'name']
    list_filter = [('city', RelatedDropdownFilter), 'enabled']
    search_fields = ['name', 'address', 'address2']
    ordering = ['city', 'address']


@admin.register(ServiceCenter)
class ServiceCenterAdmin(admin.ModelAdmin):
    list_display = ['city', 'address', 'enabled', 'latitude', 'longitude']
    list_display_links = ['address']
    list_filter = [('city', RelatedDropdownFilter), 'enabled']
    search_fields = ['address', 'city__name']
    ordering = ['city', 'address']


@admin.register(Manufacturer)
class ManufacturerAdmin(admin.ModelAdmin):
    list_display = ['id', 'code', 'name', 'machinemaker', 'accessorymaker','logo']
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


class AdvertAdminForm(forms.ModelForm):
    class Meta:
        widgets = {
            #'content': AutosizedTextarea(attrs={'rows': 15, 'style': 'width: 95%; max-height: 500px'}),
        }


@admin.register(Advert)
class AdvertAdmin(SortableAdminMixin, admin.ModelAdmin):
    list_display = ['name', 'place', get_sites, 'active']
    list_display_links = ['name']
    search_fields = ['name']
    list_filter = ['active']
    form = AdvertAdminForm


class SalesActionAdminForm(forms.ModelForm):
    class Meta:
        widgets = {
            #'brief': AutosizedTextarea(attrs={'rows': 3, 'style': 'width: 95%; max-height: 500px'}),
            #'description': AutosizedTextarea(attrs={'rows': 10, 'style': 'width: 95%; max-height: 500px'}),
        }


@admin.register(SalesAction)
class SalesActionAdmin(SortableAdminMixin, admin.ModelAdmin):
    list_display = ['name', 'slug', get_sites, 'active', 'show_in_list']
    list_display_links = ['name']
    search_fields = ['name','slug']
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
    search_fields = ['parent_product__title','parent_product__code', 'parent_product__article', 'parent_product__partnumber',
                     'child_product__title','child_product__code', 'child_product__article', 'child_product__partnumber']
    autocomplete_fields = ('parent_product', 'child_product')


class StockInline(admin.TabularInline):
    model = Stock
    form = StockInlineForm
    fields = ['supplier', 'quantity', 'correction', 'reason']
    extra = 0
    classes = ['collapse']
    suit_classes = 'suit-tab suit-tab-stock'
    formfield_overrides = {
        FloatField: {'widget': forms.TextInput(attrs={'style': 'width: 8em'})},
    }

    def has_delete_permission(self, request, obj=None):
        return obj is None #False


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
    class Meta:
        model = Product
        exclude = ('categories',)


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
    list_display = ['product_codes', 'title', 'combined_price',
                    'combined_discount', 'enabled', 'show_on_sw', 'market', 'spb_market', 'product_stock',
                    'orders_link', 'product_link']
    list_display_links = ['title']
    list_editable = ['enabled', 'show_on_sw', 'market', 'spb_market']
    list_filter = ['cur_code', ('pct_discount', DropdownFilter), ('val_discount', DropdownFilter),
                   ('categories', RelatedDropdownFilter), 'manufacturer', 'enabled', 'isnew', 'recomended',
                   'show_on_sw', 'market']
    exclude = ['image_prefix']
    search_fields = ['code', 'article', 'partnumber', 'title', 'tags']
    readonly_fields = ['price', 'ws_price', 'sp_price']
    save_as = True
    view_on_site = True
    inlines = (ProductSetInline,ProductRelationInline,StockInline,)
    filter_vertical = ('categories',)
    autocomplete_fields = ('manufacturer',)
    formfield_overrides = {
        PositiveSmallIntegerField: {'widget': forms.TextInput(attrs={'style': 'width: 4em'})},
        PositiveIntegerField: {'widget': forms.TextInput(attrs={'style': 'width: 8em'})},
        DecimalField: {'widget': forms.TextInput(attrs={'style': 'width: 8em'})},
    }
    spb_fieldset = ('С.Петербург', {
            'classes': ('collapse', 'suit-tab', 'suit-tab-money'),
            'fields': ('spb_price', 'forbid_spb_price_import', 'spb_show_in_catalog', 'spb_market')
        })
    fieldsets = (
        ('Основное', {
                'classes': ('collapse', 'suit-tab', 'suit-tab-general'),
                'fields': (('code', 'article', 'partnumber'),'title','runame','whatis','kind','categories',('manufacturer','gtin'),
                           ('country','developer_country'),'variations','spec','shortdescr','yandexdescr','descr','state','complect','dealertxt',)
        }),
        ('Деньги', {
                'classes': ('collapse', 'suit-tab', 'suit-tab-money'),
                'fields': (('cur_price', 'cur_code', 'price'), ('pct_discount', 'val_discount', 'max_discount', 'max_val_discount'),
                           ('ws_cur_price', 'ws_cur_code', 'ws_price'), 'ws_pack_only', ('ws_pct_discount', 'ws_max_discount'),
                           ('sp_cur_price', 'sp_cur_code', 'sp_price'), 'beru_price', 'consultant_delivery_price', 'forbid_price_import')
        }),
        ('Маркетинг', {
                'classes': ('collapse', 'suit-tab', 'suit-tab-money'),
                'fields': (('enabled','available','show_on_sw','firstpage'),('market', 'beru'),('isnew','recomended','gift'),'credit_allowed','deshevle',
                           'sales_notes','present','delivery','sales_actions','tags')
        }),
        spb_fieldset,
        ('Размеры', {
                'classes': ('collapse', 'suit-tab', 'suit-tab-general'),
                'fields': ('dimensions','measure','weight','prom_weight','pack_factor')
        }),
        ('Вязальные машины', {
                'classes': ('collapse', 'suit-tab', 'suit-tab-knittingmachines'),
                'fields': (
                    'km_class',
                    'km_needles',
                    'km_font',
                    'km_prog',
                    'km_rapport',)
        }),
        ('Швейные машины', {
                'classes': ('collapse', 'suit-tab', 'suit-tab-sewingmachines'),
                'fields': (
                    'stitches',
                    'fabric_verylite',
                    'fabric_lite',
                    'fabric_medium',
                    'fabric_hard',
                    'fabric_veryhard',
                    'fabric_stretch',
                    'fabric_leather',
                    'sm_shuttletype',
                    'sm_stitchwidth',
                    'sm_stitchlenght',
                    'sm_stitchquantity',
                    'sm_buttonhole',
                    'sm_dualtransporter',
                    'sm_platformlenght',
                    'sm_freearm',
                    'ov_freearm',
                    'sm_feedwidth',
                    'sm_footheight',
                    'sm_constant',
                    'sm_speedcontrol',
                    'sm_needleupdown',
                    'sm_threader',
                    'sm_spool',
                    'sm_presscontrol',
                    'sm_power',
                    'sm_light',
                    'sm_organizer',
                    'sm_autostop',
                    'sm_ruler',
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
                    'sw_hoopsize',)
        }),
        ('Гарантия', {
                'classes': ('collapse', 'suit-tab', 'suit-tab-general'),
                'fields': ('warranty', 'extended_warranty', 'manufacturer_warranty') # запятая в конце нужна, если в списке одна позиция
        }),
        ('Остальное', {
                'classes': ('collapse', 'suit-tab', 'suit-tab-other'),
                'fields': (
                    'order',
                    'swcode',
                    'oprice',
                    'coupon',
                    'not_for_sale',
                    'absent',
                    'suspend',
                    'opinion',
                    'allow_reviews',
                    ('bid','cbid'),
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
                'fields': (
                    'recalculate_price',
                    'hide_contents',
                )
        }),
    )
    suit_form_tabs = (
        ('general', 'Основное'),
        ('money', 'Деньги и маркетинг'),
        ('sewingmachines', 'Швейные машины'),
        ('knittingmachines', 'Вязальные машины'),
        ('prommachines', 'Промышленные машины'),
        ('other', 'Остальное'),
        ('set', 'Комплект'),
        ('related', 'Связанные товары'),
        ('stock', 'Запасы'),
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

    # обновляем кеш наличия при сохранении
    def save_model(self, request, obj, form, change):
        obj.num = obj.get_stock('num')
        obj.spb_num = obj.get_stock('spb_num')
        obj.ws_num = obj.get_stock('ws_num')
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

    list_display = ['name', 'colorbar']
    list_display_links = ['name']
    search_fields = ['name']
    ordering = ['name']


class OrderItemInline(admin.TabularInline):
    @mark_safe
    def product_codes(self, obj):
        code = obj.product.code or '--'
        article = obj.product.article or '--'
        partnumber = obj.product.partnumber or '--'
        code = '<a href="{}">{}</a>'.format(reverse('admin:shop_product_change', args=[obj.product.id]), code)
        return '<br/>'.join([code, article, partnumber])
    product_codes.admin_order_field = 'product__code'
    product_codes.short_description = 'Ид/1С/PN'

    def product_stock(self, obj):
        return product_stock_view(obj.product, obj.order)
    product_stock.short_description = 'склад'

    def item_cost(self, obj):
        return obj.cost
    item_cost.short_description = 'стоимость'

    model = OrderItem
    form = OrderItemInlineAdminForm
    extra = 0
    fields = ['product_codes', 'product', 'product_price', 'pct_discount', 'val_discount', 'item_cost', 'quantity', 'total', 'product_stock']
    autocomplete_fields = ('product',)
    readonly_fields = ['product_codes', 'product_stock', 'item_cost']


class OrderStatusListFilter(admin.SimpleListFilter):
    title = _('статус')
    template = 'django_admin_listfilter_dropdown/dropdown_filter.html'

    parameter_name = 'status'

    def lookups(self, request, model_admin):
        """
        Returns a list of tuples. The first element in each
        tuple is the coded value for the option that will
        appear in the URL query. The second element is the
        human-readable name for the option that will appear
        in the right sidebar.
        """
        choices = (
            ('all', _('All')),
            (None, _('активный')),
        )
        choices += Order.STATUS_CHOICES
        return choices

    def choices(self, cl):
        for lookup, title in self.lookup_choices:
            yield {
                'selected': str(self.value()) == str(lookup),
                'query_string': cl.get_query_string({
                    self.parameter_name: lookup,
                }, []),
                'display': title[0].upper() + title[1:],
            }

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via
        `self.value()`.
        """
        if self.value() == 'all':
            return None
        if self.value():
            return queryset.filter(status__exact=self.value())
        if self.value() is None:
            return queryset.filter(status__in=[Order.STATUS_NEW, Order.STATUS_ACCEPTED, Order.STATUS_COLLECTING, Order.STATUS_COLLECTED, Order.STATUS_SENT, Order.STATUS_DELIVERED_SHOP, Order.STATUS_CONSULTATION, Order.STATUS_PROBLEM, Order.STATUS_SERVICE])


class OrderDeliveryListFilter(admin.SimpleListFilter):
    title = _('доставка')
    template = 'django_admin_listfilter_dropdown/dropdown_filter.html'

    parameter_name = 'delivery'

    def lookups(self, request, model_admin):
        """
        Returns a list of tuples. The first element in each
        tuple is the coded value for the option that will
        appear in the URL query. The second element is the
        human-readable name for the option that will appear
        in the right sidebar.
        """
        choices = (
            ('all', _('All')),
            (-Order.DELIVERY_YANDEX, _('кроме Яндекс.Доставки')),
        )
        choices += Order.DELIVERY_CHOICES
        return choices

    def choices(self, cl):
        for lookup, title in self.lookup_choices:
            yield {
                'selected': str(self.value()) == str(lookup),
                'query_string': cl.get_query_string({
                    self.parameter_name: lookup,
                }, []),
                'display': title[0].upper() + title[1:],
            }

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via
        `self.value()`.
        """
        if self.value() == 'all':
            return None
        if self.value():
            value = int(self.value())
            if value < 0:
                return queryset.exclude(delivery__exact=(-value))
            else:
                return queryset.filter(delivery__exact=value)


class FutureDateFieldListFilter(admin.FieldListFilter):
    template = 'django_admin_listfilter_dropdown/dropdown_filter.html'

    def __init__(self, field, request, params, model, model_admin, field_path):
        self.field_generic = '%s__' % field_path
        self.date_params = {k: v for k, v in params.items()
                            if k.startswith(self.field_generic)}

        now = timezone.now()
        # When time zone support is enabled, convert "now" to the user's time
        # zone so Django's definition of "Today" matches what the user expects.
        if timezone.is_aware(now):
            now = timezone.localtime(now)

        if isinstance(field, DateTimeField):
            today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        else:       # field is a models.DateField
            today = now.date()
        tomorrow = today + datetime.timedelta(days=1)
        if today.month == 12:
            next_month = today.replace(year=today.year + 1, month=1, day=1)
        else:
            next_month = today.replace(month=today.month + 1, day=1)
        next_year = today.replace(year=today.year + 1, month=1, day=1)
        shop_epoch = datetime.date(2000, 1, 1)

        self.lookup_kwarg_since = '%s__gte' % field_path
        self.lookup_kwarg_until = '%s__lt' % field_path
        self.links = (
            (_('Any date'), {}),
            (_('Просрочена'), {
                self.lookup_kwarg_since: str(shop_epoch),
                self.lookup_kwarg_until: str(today),
            }),
            (_('Today'), {
                self.lookup_kwarg_since: str(today),
                self.lookup_kwarg_until: str(tomorrow),
            }),
            (_('Завтра'), {
                self.lookup_kwarg_since: str(tomorrow),
                self.lookup_kwarg_until: str(tomorrow + datetime.timedelta(days=1)),
            }),
            (_('Следующие 2 дня'), {
                self.lookup_kwarg_since: str(tomorrow),
                self.lookup_kwarg_until: str(tomorrow + datetime.timedelta(days=2)),
            }),
            (_('Следующие 7 дней'), {
                self.lookup_kwarg_since: str(tomorrow),
                self.lookup_kwarg_until: str(tomorrow + datetime.timedelta(days=7)),
            }),
        )
        if field.null:
            self.lookup_kwarg_isnull = '%s__isnull' % field_path
            self.links += (
                (_('Без даты'), {self.field_generic + 'isnull': 'True'}),
                (_('С датой'), {self.field_generic + 'isnull': 'False'}),
            )
        super(FutureDateFieldListFilter, self).__init__(
            field, request, params, model, model_admin, field_path)

    def expected_parameters(self):
        params = [self.lookup_kwarg_since, self.lookup_kwarg_until]
        if self.field.null:
            params.append(self.lookup_kwarg_isnull)
        return params

    def choices(self, changelist):
        for title, param_dict in self.links:
            yield {
                'selected': self.date_params == param_dict,
                'query_string': changelist.get_query_string(param_dict, [self.field_generic]),
                'display': title,
            }


@admin.register(Order)
class OrderAdmin(LockableModelAdmin):
    @mark_safe
    def order_name(self, obj):
        manager = ''
        if obj.manager:
            manager = ' style="color: %s"' % obj.manager.color
        shop_code = getattr(settings, 'SHOP_ORDER_CODES', {}).get(obj.site.domain, '?')
        if shop_code:
            shop_code = shop_code + '-'
        return '<b%s>%s%s</b><br/><span style="white-space:nowrap">%s</span>' % \
            (manager, shop_code, obj.id, date_format(timezone.localtime(obj.created), "DATETIME_FORMAT"))
    order_name.admin_order_field = 'id'
    order_name.short_description = 'заказ'

    @mark_safe
    def combined_comments(self, obj):
        return '<span style="color:#008">%s</span> %s<br/><em>%s</em>' % (obj.delivery_yd_order, obj.delivery_info, obj.manager_comment)
    combined_comments.admin_order_field = 'manager_comment'
    combined_comments.short_description = 'Комментарии'

    @mark_safe
    def combined_delivery(self, obj):
        datetime = ''
        if obj.delivery_dispatch_date:
            datetime = date_format(obj.delivery_dispatch_date, "SHORT_DATE_FORMAT")
        if obj.delivery_time_from:
            if datetime:
                datetime = datetime + ' '
            datetime = datetime + date_format(obj.delivery_time_from, "TIME_FORMAT")
        if obj.delivery_time_till:
            datetime = datetime + '-' + date_format(obj.delivery_time_till, "TIME_FORMAT")
        courier = ''
        if obj.courier:
            courier = ': %s' % obj.courier.name
        return '%s%s<br/>%s' % (obj.get_delivery_display(), courier, datetime)
    combined_delivery.admin_order_field = 'delivery_dispatch_date'
    combined_delivery.short_description = 'Доставка'

    @mark_safe
    def name_and_skyped_phone(self, obj):
        name = obj.name if obj.name else '---'
        return '%s<br/><a href="skype:%s?call">%s</a>' % (name, obj.phone, ShopUserManager.format_phone(obj.phone))
    name_and_skyped_phone.admin_order_field = 'phone'
    name_and_skyped_phone.short_description = 'Покупатель'

    @mark_safe
    def colored_status(self, obj):
        return '<span style="color: %s">%s</span>' % (obj.STATUS_COLORS[obj.status], obj.get_status_display())
    colored_status.admin_order_field = 'status'
    colored_status.short_description = 'статус'

    @mark_safe
    def combined_payment(self, obj):
        style = ''
        checkmark = ''
        if obj.paid:
            style = '; color: green'
            checkmark = '<span style="display: table-cell; padding-left: 5px; color: green; font-weight: bold">&#10003;</span>'
        elif obj.payment in [Order.PAYMENT_CARD, Order.PAYMENT_TRANSFER, Order.PAYMENT_CREDIT]:
            style = '; color: red'
        return '<div style="display: table"><span style="display: table-cell%s">%s</span>%s</div>' % (style, obj.get_payment_display(), checkmark)
    combined_payment.admin_order_field = 'payment'
    combined_payment.short_description = 'оплата'

    @mark_safe
    def total_cost(self, obj):
        if obj.total == int(obj.total):
            return number_format(int(obj.total), force_grouping=True)
        else:
            return number_format(obj.total, force_grouping=True)
    total_cost.short_description = 'всего'

    @mark_safe
    def link_to_user(self, obj):
        inconsistency = '-'
        if obj.name != obj.user.name or obj.phone != obj.user.phone or \
           obj.email != obj.user.email or obj.postcode != obj.user.postcode or \
           obj.address != obj.user.address:
            inconsistency = '<span style="color: red" title="Несоответствие данных!">&#10033;</span>'
        return inconsistency
    link_to_user.short_description = 'несоответствие'

    @mark_safe
    def link_to_orders(self, obj):
        orders = Order.objects.filter(user=obj.user.id).exclude(pk=obj.id).values_list('id', flat=True)
        if not orders:
            return '<span>нет</span>'
        else:
            url = '%s?pk__in=%s,%s&status=all' % (reverse("admin:shop_order_changelist"), obj.id, ','.join(map(lambda x: str(x), list(orders))))
            return '<span><a href="%s">%s</a></span>' % (url, orders.count())
    link_to_orders.short_description = 'заказы'

    @mark_safe
    def credit_notice(self, obj):
        credit_allowed = False
        for item in obj.items.all():
            credit_allowed = credit_allowed or item.product.credit_allowed
        if credit_allowed:
            return '''
                   <div id="yandex-credit"></div>
                   <script src="https://static.yandex.net/kassa/pay-in-parts/ui/v1"></script>
                   <script>
                   $(document).ready(function() {
                     const $checkoutCreditUI = YandexCheckoutCreditUI({ shopId: '42873', sum: '%d' });
                     const checkoutCreditText = $checkoutCreditUI({ type: 'info', domSelector: '#yandex-credit' });
                   });
                   </script>
                   ''' % obj.total
        else:
            return 'нет'
    credit_notice.short_description = 'кредит'

    list_display = ['order_name', 'name_and_skyped_phone', 'city', 'total_cost', 'combined_payment', 'combined_delivery',
                    'colored_status', 'combined_comments']
    readonly_fields = ['id', 'shop_name', 'credit_notice', 'total', 'products_price', 'created', 'link_to_user', 'link_to_orders']
    list_filter = [OrderStatusListFilter, ('created', PastDateRangeFilter), ('payment', ChoiceDropdownFilter), OrderDeliveryListFilter,
                   ('delivery_dispatch_date', FutureDateRangeFilter), ('delivery_handing_date', FutureDateRangeFilter),
                   'paid', 'site', 'manager', 'courier']
    search_fields = ['id', 'name', 'phone', 'email', 'address', 'city', 'comment',
                     'user__name', 'user__phone', 'user__email', 'user__address', 'user__postcode', 'manager_comment']
    inlines = [OrderItemInline] #, AddOrderItemInline]
    change_form_template = 'admin/shop/order/change_form.html' # we do not need this by default but lockable model overrides it
    form = OrderAdminForm
    autocomplete_fields = ('store','user')
    formfield_overrides = {
        TextField: {'widget': forms.Textarea(attrs={'style': 'width: 60%; height: 4em'})},
        PositiveSmallIntegerField: {'widget': forms.TextInput(attrs={'style': 'width: 4em'})},
        PositiveIntegerField: {'widget': forms.TextInput(attrs={'style': 'width: 6em'})},
        DecimalField: {'widget': forms.TextInput(attrs={'style': 'width: 6em'})},
    }
    actions = ['order_product_list_action', 'order_1c_action', 'order_pickpoint_action', 'order_stock_action', 'order_set_user_tag_action']
    save_as = True
    save_on_top = True
    list_per_page = 50

    def get_fieldsets(self, request, obj=None):
        fieldsets = (
            (None, {'fields': (('status', 'payment', 'paid', 'manager', 'site', 'credit_notice'), ('delivery', 'delivery_price', 'courier'),
                               'delivery_dispatch_date', ('delivery_tracking_number', 'delivery_yd_order'), 'delivery_info',
                               ('delivery_handing_date', 'delivery_time_from', 'delivery_time_till'), 'manager_comment', 'store',
                               'products_price', 'total', 'id')}),
            ('1С', {'fields': (('buyer', 'seller','wiring_date'),),}),
            #('Яндекс.Доставка', {'fields': ('delivery_yd_order',)}),
            #('PickPoint', {'fields': (('delivery_pickpoint_terminal', 'delivery_pickpoint_service', 'delivery_pickpoint_reception'),
            #                          ('delivery_size_length', 'delivery_size_width', 'delivery_size_height'),),}),
            ('Покупатель', {'fields': [('name', 'user', 'link_to_user', 'link_to_orders'), ('phone', 'phone_aux', 'email'),
                                       'address', ('city', 'postcode'), 'comment', ('firm_name', 'is_firm')]}),
            )
        if obj is None or obj.is_firm:
            fieldsets[2][1]['fields'].extend(('firm_address', 'firm_details'))
        fieldsets[2][1]['fields'].append('user_tags')
        return fieldsets

    def lookup_allowed(self, lookup, value):
        if lookup == 'item__product__pk':
            return True
        return super().lookup_allowed(lookup, value)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser and request.user.has_perm('shop.change_order_spb'):
            qs = qs.filter(site=6)
        return qs

    def get_readonly_fields(self, request, obj=None):
        if obj and not request.user.is_superuser:
            return self.readonly_fields + ['site']
        return self.readonly_fields

    def changelist_view(self, request, extra_context=None):
        if not request.user.is_staff:
            raise PermissionDenied
        if 'action' in request.POST and request.POST['action'] == 'order_product_list_action':
            if not request.POST.getlist(admin.ACTION_CHECKBOX_NAME):
                post = request.POST.copy()
                # '0' is special case for 'all'
                post.update({admin.ACTION_CHECKBOX_NAME: '0'})
                request._set_post(post)
        return super(OrderAdmin, self).changelist_view(request, extra_context)

    def get_urls(self):
        urls = super(OrderAdmin, self).get_urls()
        my_urls = [
            url(r'(\d+)/document/([a-z]+)/$', self.admin_site.admin_view(self.document), name='shop_order_document'),
            url(r'products/$', self.admin_site.admin_view(self.order_product_list), name='shop_order_product_list'),
            url(r'(\d+)/item/(\d+)/print_warranty_card/$', self.admin_site.admin_view(self.print_warranty_card), name='print-warranty-card'),
            url(r'(\d+)/combine/$', self.admin_site.admin_view(self.combine_form), name='shop_order_combine'),
            url(r'(\d+)/discount/$', self.admin_site.admin_view(self.discount_form), name='shop_order_discount'),
            url(r'(\d+)/yandex_delivery/$', self.admin_site.admin_view(self.yandex_delivery_form), name='shop_order_yandex_delivery'),
            url(r'(\d+)/yandex_delivery_estimate/$', self.admin_site.admin_view(self.yandex_delivery_estimate), name='shop_order_yandex_delivery_estimate'),
            url(r'sms/(\+\d+)/$', self.admin_site.admin_view(self.send_sms_form), name='shop_order_send_sms'),
        ]
        return my_urls + urls

    def document(self, request, id, template):
        if not request.user.is_staff:
            raise PermissionDenied
        order = Order.objects.get(pk=id)
        return render(request, 'shop/order/' + template + '.html', {
            'owner_info': getattr(settings, 'SHOP_OWNER_INFO', {}),
            'order': order,
            'opts': self.model._meta,
        })

    def order_product_list_action(self, request, queryset):
        if not request.user.is_staff:
            raise PermissionDenied
        selected = request.POST.getlist(admin.ACTION_CHECKBOX_NAME)
        return HttpResponseRedirect("products/?orders=%s" % ",".join(selected))
    order_product_list_action.short_description = "Показать товары для выбранных заказов"

    def order_product_list(self, request):
        if not request.user.is_staff:
            raise PermissionDenied
        suppliers = Supplier.objects.filter(show_in_order=True)
        list_of_ids = suppliers.values_list('id', flat=True)
        format_strings = ','.join(['%s'] * len(list_of_ids))
        ids = request.GET.get('orders', '0')
        where = ''
        if ids != '0':
            where = ' WHERE shop_order.id IN (' + ids + ')'
        sort = request.GET.get('o', 'shop_product.title')
        cursor = connection.cursor()
        inner_cursor = connection.cursor()
        cursor.execute("""SELECT shop_product.id AS product_id, shop_product.article, shop_product.partnumber, shop_product.title,
                          shop_order.id AS order_id, shop_order.status AS order_status,
                          SUM(shop_orderitem.quantity) AS quantity
                          FROM shop_product
                          INNER JOIN shop_orderitem ON (shop_product.id = shop_orderitem.product_id)
                          INNER JOIN shop_order ON (shop_orderitem.order_id = shop_order.id)""" + where +
                          """ GROUP BY shop_order.id, shop_product.id ORDER BY """ + sort)
        products = []
        for row in cursor.fetchall():
            columns = (x[0] for x in cursor.description)
            product = dict(zip(columns, row))
            product['order_status_value'] = dict(Order.STATUS_CHOICES)[product['order_status']]
            product['order_status_color'] = dict(Order.STATUS_COLORS)[product['order_status']]
            stock = ''
            inner_cursor.execute("""SELECT supplier_id, quantity FROM shop_stock LEFT JOIN shop_supplier ON (shop_supplier.id = supplier_id)
                                    WHERE product_id = %s AND supplier_id IN (%s) ORDER BY shop_supplier.order""" % (product['product_id'], format_strings), list_of_ids)
            if inner_cursor.rowcount:
                for row in inner_cursor.fetchall():
                    stock = stock + ('%s:&nbsp;' % suppliers.get(pk=row[0]).code)
                    if row[1] == 0:
                        stock = stock + '<span style="color: #c00">'
                    stock = stock + ('%s' % floatformat(row[1]))
                    if row[1] == 0:
                        stock = stock + '</span>'
                    stock = stock + '<br/>'
            else:
                stock = '<span style="color: #ff0000">отсутствует</span>'
            #inner_cursor.execute("""SELECT SUM(shop_orderitem.quantity) AS quantity FROM shop_orderitem
            #                        INNER JOIN shop_order ON (shop_orderitem.order_id = shop_order.id) WHERE shop_order.status IN (0,1,4,64,256,1024)
            #                        AND shop_orderitem.product_id = %s GROUP BY shop_orderitem.product_id""", (product['product_id'],))
            #if inner_cursor.rowcount:
            #    row = inner_cursor.fetchone()
            #    stock = stock + '<span style="color: #00c">Зак:&nbsp;'
            #    stock = stock + ('%s' % floatformat(row[0]))
            #    stock = stock + '</span><br/>'
            product['stock'] = stock
            products.append(product)
        cursor.close()
        inner_cursor.close()
        return render(request, 'admin/shop/order/products.html', {
            'title': 'Товары для заказов',
            'products': products,
            'orders': ids,
            'o': sort,
            'cl': self,
            'opts': self.model._meta,
            **self.admin_site.each_context(request)
        })

    def print_warranty_card(self, request, order_id, item_id):
        order = self.get_object(request, order_id)
        item = order.items.get(pk=item_id)

        if request.method != 'POST':
            form = WarrantyCardPrintForm({'serial_number': item.serial_number})
            is_popup = request.GET.get('_popup', 0)
        else:
            form = WarrantyCardPrintForm(request.POST)
            is_popup = request.POST.get('_popup', 0)
            if form.is_valid():
                try:
                    serial_number = form.cleaned_data['serial_number']
                    item.serial_number = serial_number
                    item.save()
                    context = {
                        'owner_info': getattr(settings, 'SHOP_OWNER_INFO', {}),
                        'order': order,
                        'product': item.product,
                        'serial_number': serial_number
                        }
                    return TemplateResponse(request, 'shop/order/warrantycard.html', context)

                except Exception as e:
                    # If save() raised, the form will a have a non
                    # field error containing an informative message.
                    pass

        context = self.admin_site.each_context(request)
        context['opts'] = self.model._meta
        context['form'] = form
        context['is_popup'] = is_popup
        context['title'] = "Печать гарантийного талона"

        return TemplateResponse(request, 'admin/shop/order/print_warranty_card.html', context)

    def combine_form(self, request, id):
        if not request.user.is_staff:
            raise PermissionDenied
        order = Order.objects.get(pk=id)
        messages = None
        if request.method != 'POST':
            form = OrderCombineForm()
            is_popup = request.GET.get('_popup', 0)
        else:
            form = OrderCombineForm(request.POST)
            is_popup = request.POST.get('_popup', 0)
            if form.is_valid():
                try:
                    order_number = form.cleaned_data['order_number']
                    other_order = Order.objects.get(pk=order_number)
                    if order.user != other_order.user:
                        form.add_error('order_number', "Разные пользователи у заказов")
                    else:
                        for item in other_order.items.all():
                            item.pk = None
                            item.order = order
                            item.save()
                        return HttpResponse('<!DOCTYPE html><html><head><title></title></head><body>'
                                            '<script type="text/javascript">opener.dismissPopupAndReload(window);</script>'
                                            '</body></html>')

                except Exception as e:
                    form.errors['__all__'] = form.error_class([str(e)])

        context = self.admin_site.each_context(request)
        context['opts'] = self.model._meta
        context['form'] = form
        context['is_popup'] = is_popup
        context['messages'] = messages
        context['title'] = "Укажите заказ для объединения"
        context['action_title'] = "Объеденить"

        return TemplateResponse(request, 'admin/shop/custom_action_form.html', context)

    def discount_form(self, request, id):
        if not request.user.is_staff:
            raise PermissionDenied
        order = Order.objects.get(pk=id)
        messages = None
        if request.method != 'POST':
            form = OrderDiscountForm()
            is_popup = request.GET.get('_popup', 0)
        else:
            form = OrderDiscountForm(request.POST)
            is_popup = request.POST.get('_popup', 0)
            if form.is_valid():
                try:
                    discount = int(form.cleaned_data['discount'])
                    for item in order.items.all():
                        if discount > item.pct_discount:
                            if discount <= item.product.max_discount:
                                item.pct_discount = discount
                            else:
                                item.pct_discount = item.product.max_discount
                            item.save()

                    return HttpResponse('<!DOCTYPE html><html><head><title></title></head><body>'
                                        '<script type="text/javascript">opener.dismissPopupAndReload(window);</script>'
                                        '</body></html>')

                except Exception as e:
                    form.errors['__all__'] = form.error_class([str(e)])

        context = self.admin_site.each_context(request)
        context['opts'] = self.model._meta
        context['form'] = form
        context['is_popup'] = is_popup
        context['messages'] = messages
        context['title'] = "Укажите скидку"
        context['action_title'] = "Применить"

        return TemplateResponse(request, 'admin/shop/custom_action_form.html', context)

    def yandex_delivery_form(self, request, id):
        if not request.user.is_staff:
            raise PermissionDenied
        order = Order.objects.get(pk=id)
        messages = None
        if request.method != 'POST':
            initial = {
                'fio': order.name,
            }
            form = YandexDeliveryForm(initial=initial)
            is_popup = request.GET.get('_popup', 0)
        else:
            form = YandexDeliveryForm(request.POST)
            is_popup = request.POST.get('_popup', 0)
            if form.is_valid():
                try:
                    fio_last = form.cleaned_data['fio_last']
                    warehouse = form.cleaned_data['warehouse']

                    fio = order.name.split(' ')
                    first_name = ''
                    middle_name = ''
                    last_name = ''
                    if len(fio) == 1: # looks like it's a name only
                        first_name = fio[0]
                    elif len(fio) == 2: # looks like it's name with surname
                        if fio_last:
                            fio.reverse()
                        last_name, first_name = fio
                    else:
                        if fio_last:
                            first_name, middle_name, last_name = fio
                        else:
                            last_name, first_name, middle_name = fio

                    yd = DeliveryClient(
                        settings.YD_CLIENT['client']['id'],
                        settings.YD_CLIENT['senders'][0]['id'],
                        list(map(lambda x:x['id'], settings.YD_CLIENT['warehouses'])),
                        list(map(lambda x:x['id'], settings.YD_CLIENT['requisites'])),
                        settings.YD_METHODS
                    )

                    order_items = []
                    for item in order.items.all():
                        if item.quantity > 1:
                            title = '{} ({} шт.)'.format(item.product.title, item.quantity)
                        else:
                            title = item.product.title
                        order_items.append({
                            'orderitem_id': item.product.id,
                            'orderitem_article': item.product.code,
                            'orderitem_name': title,
                            'orderitem_cost': item.price,
                            'orderitem_quantity': 1
                        })

                    result = yd.create_order(
                        order_num=order.id,
                        order_warehouse=warehouse,
                        order_items=order_items,
                        recipient={
                            'first_name': first_name,
                            'middle_name': middle_name,
                            'last_name': last_name,
                            'phone': order.phone,
                            'email': order.email
                            },
                        deliverypoint={
                            'city': order.city,
                            'street': order.address,
                            'index': order.postcode
                            }
                    )
                    yd_order = result['data']['order']['full_num']

                    return HttpResponse('<!DOCTYPE html><html><head><title></title></head><body>'
                                        '<script type="text/javascript">opener.dismissYandexDeliveryPopup(window, "%s", "%s");</script>'
                                        '</body></html>' % (Order.DELIVERY_YANDEX, yd_order))

                except Exception as e:
                    form.errors['__all__'] = form.error_class([str(e)])

        context = self.admin_site.each_context(request)
        context['opts'] = self.model._meta
        context['form'] = form
        context['is_popup'] = is_popup
        context['messages'] = messages
        context['title'] = "Создать черновик заказа"
        context['action_title'] = "Создать"

        return TemplateResponse(request, 'admin/shop/custom_action_form.html', context)

    def yandex_delivery_estimate(self, request, id):
        if not request.user.is_staff:
            raise PermissionDenied

        order = Order.objects.get(pk=id)

        context = self.admin_site.each_context(request)
        context['opts'] = self.model._meta
        context['is_popup'] = request.GET.get('_popup', 0)
        context['title'] = "Варианты доставки"
        context['order'] = order,
        context['city'] = request.GET.get('city', order.city)
        context['weight'] = request.GET.get('weight', 10)
        context['height'] = request.GET.get('height', 27)
        context['length'] = request.GET.get('length', 50)
        context['width'] = request.GET.get('width', 40)

        try:
            yd = DeliveryClient(
                settings.YD_CLIENT['client']['id'],
                settings.YD_CLIENT['senders'][0]['id'],
                list(map(lambda x:x['id'], settings.YD_CLIENT['warehouses'])),
                list(map(lambda x:x['id'], settings.YD_CLIENT['requisites'])),
                settings.YD_METHODS
            )
            result = yd.search_delivery_list('Москва', context['city'], context['weight'], context['width'],
                                             context['height'], context['length'], order_cost=order.total,
                                             total_cost=order.total)
            colors = [
                '#1E98FF', #blue
                '#1BAD03', #darkGreen
                '#ED4543', #red
                '#E6761B', #darkOrange
                '#B51EFF', #violet
                '#0E4779', #night
                '#FFD21E', #yellow
                '#177BC9', #darkBlue
                '#56DB40', #green
                '#F371D1', #pink
                '#FF931E', #orange
                '#B3B3B3', #gray
                '#82CDFF', #lightBlue
                '#793D0E', #brown
                '#97A100', #olive
            ]
            deliveries = {}
            i = 0
            for delivery in result['data']:
                delivery_type = deliveries.get(delivery['type'], None)
                if delivery_type is None:
                    delivery_type = []
                    deliveries[delivery['type']] = delivery_type
                shop_cost = delivery['costWithRules']
                required_services = []
                optional_services = []
                for service in delivery['services']:
                    if service['optional']:
                        optional_services.append(service)
                    else:
                        required_services.append(service)
                        shop_cost = shop_cost + service['cost']
                delivery['required_services'] = required_services
                delivery['optional_services'] = optional_services
                delivery['shop_cost'] = shop_cost
                pickup_points = delivery.get('pickupPoints', [])
                if len(pickup_points):
                    delivery['color'] = colors[i]
                    i = i + 1
                else:
                    delivery['color'] = '#FFFFFF'
                dmf = datetime.time.max
                dmt = datetime.time.min
                for point in pickup_points:
                    mf = datetime.time.max
                    mt = datetime.time.min
                    for schedule in point.get('schedules', []):
                        fr = datetime.datetime.strptime(schedule['from'], '%H:%M:%S').time()
                        tl = datetime.datetime.strptime(schedule['to'], '%H:%M:%S').time()
                        if fr < mf:
                            mf = fr
                        if tl > mt:
                            mt = tl
                        if fr < dmf:
                            dmf = fr
                        if tl > dmt:
                            dmt = tl
                    if mf != datetime.time.max and mt != datetime.time.min:
                        point['delivery_interval'] = mark_safe('{}&ndash;{}'.format(mf.strftime('%H:%M'), mt.strftime('%H:%M')))
                if dmf == datetime.time.max or dmt == datetime.time.min:
                    for delivery_interval in delivery.get('deliveryIntervals', []):
                        fr = datetime.datetime.strptime(delivery_interval['from'], '%H:%M:%S').time()
                        tl = datetime.datetime.strptime(delivery_interval['to'], '%H:%M:%S').time()
                        if fr < dmf:
                            dmf = fr
                        if tl > dmt:
                            dmt = tl
                if dmf != datetime.time.max and dmt != datetime.time.min:
                    delivery['delivery_interval'] = mark_safe('{}&ndash;{}'.format(dmf.strftime('%H:%M'), dmt.strftime('%H:%M')))
                delivery_type.append(delivery)

            context['deliveries'] = deliveries
            context['result'] = result['data']

        except Exception as e:
            context['error'] = str(e)

        return TemplateResponse(request, 'admin/shop/order/yandex_delivery_estimate.html', context)

    def send_sms_form(self, request, phone):
        if not request.user.is_staff:
            raise PermissionDenied
        messages = None
        if request.method != 'POST':
            form = SendSmsForm()
            is_popup = request.GET.get('_popup', 0)
        else:
            form = SendSmsForm(request.POST)
            is_popup = request.POST.get('_popup', 0)
            if form.is_valid():
                try:
                    message = form.cleaned_data['message']
                    if message:
                        send_message.delay(phone, message)
                    messages = ["Сообщение отправлено, закройте окно"]
                    form = SendSmsForm()
                except Exception as e:
                    form.errors['__all__'] = form.error_class([str(e)])

        context = self.admin_site.each_context(request)
        context['opts'] = self.model._meta
        context['form'] = form
        context['is_popup'] = is_popup
        context['messages'] = messages
        context['title'] = "Укажите текст сообщения для %s" % str(phone)
        context['action_title'] = "Отправить"

        return TemplateResponse(request, 'admin/shop/custom_action_form.html', context)

    def order_1c_action(self, request, queryset):
        if not request.user.is_staff:
            raise PermissionDenied
        missing_contractors = set()
        missing_wiring_date = set()
        for order in queryset:
            if not order.buyer or not order.seller:
                missing_contractors.add(order.id)
            if not order.wiring_date:
                missing_wiring_date.add(order.id)
        if missing_contractors:
            self.message_user(request, "В заказах не указан контрагент: %s" % ', '.join(map(str,missing_contractors)), level=messages.ERROR)
        elif missing_wiring_date:
            self.message_user(request, "В заказах не указана дата проводки: %s" % ', '.join(map(str,missing_wiring_date)), level=messages.ERROR)
        else:
            template = get_template('admin/shop/order/1c.txt')
            response = HttpResponse(template.render({'orders': queryset}).replace('\n', '\r\n'), content_type='text/xml; charset=utf8')
            response['Content-Disposition'] = 'attachment; filename=1C-{0}.xml'.format(datetime.date.today().isoformat())
            return response
    order_1c_action.short_description = "Выгрузка в 1С"

    def order_pickpoint_action(self, request, queryset):
        if not request.user.is_staff:
            raise PermissionDenied
        missing_terminal = False
        for order in queryset:
            if not order.delivery_pickpoint_terminal:
                missing_terminal = True
        if missing_terminal:
            self.message_user(request, "Для одного из заказов не указан терминал", level=messages.ERROR)
        else:
            template = get_template('admin/shop/order/pickpoint.xml')
            response = HttpResponse(template.render({'orders': queryset}), content_type='text/plain; charset=utf-8')
            response['Content-Disposition'] = 'attachment; filename=PickPoint-{0}.xml'.format(datetime.date.today().isoformat())
            return response
    order_pickpoint_action.short_description = "Выгрузка в ПикПоинт"

    def order_stock_action(self, request, queryset):
        if not request.user.is_staff:
            raise PermissionDenied
        if 'show_stock' in request.POST:
            supplier_ur = Supplier.objects.get(code='Ур')
            supplier = Supplier.objects.get(pk=request.POST.get('supplier'))
            selected = request.POST.getlist(admin.ACTION_CHECKBOX_NAME)
            cursor = connection.cursor()
            inner_cursor = connection.cursor()
            cursor.execute("""SELECT shop_product.id AS product_id, shop_product.article,
                              SUM(shop_orderitem.quantity) AS quantity
                              FROM shop_product
                              INNER JOIN shop_orderitem ON (shop_product.id = shop_orderitem.product_id)
                              INNER JOIN shop_order ON (shop_orderitem.order_id = shop_order.id)
                              WHERE shop_order.id IN (""" + ','.join(selected) + """)
                              GROUP BY shop_product.id ORDER BY shop_product.article""")
            products = []
            for row in cursor.fetchall():
                columns = (x[0] for x in cursor.description)
                product = dict(zip(columns, row))
                stock = ''
                inner_cursor.execute("""SELECT supplier_id, quantity, correction FROM shop_stock
                                        LEFT JOIN shop_supplier ON (shop_supplier.id = supplier_id)
                                        WHERE product_id = %s AND supplier_id IN (%s, %s)
                                        ORDER BY shop_supplier.order""", (product['product_id'], supplier_ur.id, supplier.id))
                quantity = float(product['quantity'])
                stock = 0
                if inner_cursor.rowcount:
                    for row in inner_cursor.fetchall():
                        if row[0] == supplier_ur.id:
                            quantity = quantity - row[1] - row[2]
                        if row[0] == supplier.id:
                            stock = row[1] + row[2]
                if quantity > 0 and stock > 0:
                    product['stock'] = Decimal(quantity).quantize(Decimal('1'), rounding=ROUND_UP)
                    products.append(product)
            cursor.close()
            inner_cursor.close()
            if not products:
                self.message_user(request, "Нет товаров для отгрузки у этого поставщика", level=messages.WARNING)
                return
            else:
                import io
                import xlsxwriter

                output = io.BytesIO()
                workbook = xlsxwriter.Workbook(output)
                sheet = workbook.add_worksheet(supplier.name)
                for idx, product in enumerate(products):
                    sheet.write(idx, 0, product['article'])
                    sheet.write(idx, 1, product['stock'])
                workbook.close()

                response = HttpResponse(output.getvalue(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                response['Content-Disposition'] = 'attachment; filename={0}-{2}.xlsx; filename*=UTF-8\'\'{1}-{2}.xlsx'.format(
                    'stock',
                    urlquote(supplier.code),
                    datetime.date.today().isoformat())
                return response

        form = SelectSupplierForm(initial = {'supplier': Supplier.objects.get(code='С3').pk})
        context = self.admin_site.each_context(request)
        context['opts'] = self.model._meta
        context['form'] = form
        context['queryset'] = queryset
        context['is_popup'] = 0
        context['title'] = "Выберите поставщика"
        context['action'] = 'order_stock_action'
        context['action_name'] = 'show_stock'
        context['action_title'] = "Сформировать выгрузку"

        return TemplateResponse(request, 'admin/shop/custom_action_form.html', context)

    order_stock_action.short_description = "Выгрузка поставщику"

    def order_set_user_tag_action(self, request, queryset):
        if not request.user.is_staff:
            raise PermissionDenied
        if 'set_user_tag' in request.POST:
            tags = parse_tag_input(request.POST.get('tags'))
            for order in queryset:
                order.append_user_tags(tags)
            self.message_user(request, "Добавлен тег {} пользователям".format(queryset.count()))
            return HttpResponseRedirect(request.get_full_path())

        messages = None
        form = SelectTagForm(model=ShopUser)
        """
            if form.is_valid():
                try:
                    message = form.cleaned_data['message']
                    if message:
                        send_message.delay(phone, message)
                    messages = ["Сообщение отправлено, закройте окно"]
                    form = SendSmsForm()
                except Exception as e:
                    form.errors['__all__'] = form.error_class([str(e)])
        """
        context = self.admin_site.each_context(request)
        context['opts'] = self.model._meta
        context['form'] = form
        context['queryset'] = queryset
        context['is_popup'] = 0
        context['messages'] = messages
        context['title'] = "Укажите один или несколько тегов"
        context['action'] = 'order_set_user_tag_action'
        context['action_name'] = 'set_user_tag'
        context['action_title'] = "Добавить"

        return TemplateResponse(request, 'admin/shop/custom_action_form.html', context)
    order_set_user_tag_action.short_description = "Добавить тег покупателю"


class UserCreationForm(forms.ModelForm):
    error_messages = {
        'password_mismatch': _("The two password fields didn't match."),
    }
    password1 = forms.CharField(label=_("Password"),
        widget=forms.PasswordInput)
    password2 = forms.CharField(label=_("Password confirmation"),
        widget=forms.PasswordInput,
        help_text=_("Enter the same password as above, for verification."))

    class Meta:
        model = ShopUser
        fields = '__all__'

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError(
                self.error_messages['password_mismatch'],
                code='password_mismatch',
            )
        return password2

    def save(self, commit=True):
        user = super(UserCreationForm, self).save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class UserChangeForm(forms.ModelForm):
    password = ReadOnlyPasswordHashField(help_text=_("Raw passwords are not stored, so there is no way to see "
                    "this user's password, but you can change the password "
                    "using <a href=\"../password/\">this form</a>."))

    class Meta:
        model = ShopUser
        fields = '__all__'
        widgets = {
            'tags': TagAutoComplete(model=ShopUser),
            }

    def clean_password(self):
        # Regardless of what the user provides, return the initial value.
        # This is done here, rather than on the field, because the
        # field does not have access to the initial value
        return self.initial["password"]


class TagListFilter(admin.SimpleListFilter):
    """
    Filter records by tags for the current model only. Tags are sorted alphabetically by name.
    """
    title = _('tags')
    parameter_name = 'tag'

    def lookups(self, request, model_admin):
        model_tags = [tag.name for tag in Tag.objects.usage_for_model(model_admin.model)]
        model_tags.sort()
        return tuple([(tag, tag) for tag in model_tags])

    def queryset(self, request, queryset):
        if self.value() is not None:
            #return ShopUser.tagged.with_all(self.value(), queryset)
            return TaggedItem.objects.get_by_model(queryset, self.value())


class ShopUserResource(resources.ModelResource):
    class Meta:
        model = ShopUser
        import_id_fields = ['phone']
        exclude = ('id', 'password', 'groups', 'is_active', 'is_staff', 'is_superuser', 'tags')


class ShopUserAdmin(ExportMixin, UserAdmin):
    # The forms to add and change user instances
    form = UserChangeForm
    add_form = UserCreationForm

    # The fields to be used in displaying the User model.
    # These override the definitions on the base UserAdmin
    # that reference specific fields on auth.User.
    list_display = ('phone', 'name', 'email', 'discount', 'tags', 'is_staff', 'is_superuser')
    list_filter = ('discount', TagListFilter, 'groups', 'is_staff', 'is_superuser')
    # add_fieldsets is not a standard ModelAdmin attribute. UserAdmin
    # overrides get_fieldsets to use this attribute when creating a user.
    add_fieldsets = (
        (None, {
            'fields': ('phone', 'name', 'password1', 'password2')}
        ),
    )
    search_fields = ('phone', 'name', 'email', 'tags')
    ordering = ('phone', 'name')
    filter_horizontal = ()
    #change_list_template = 'admin/change_list_filter_sidebar.html'
    #change_list_filter_template = 'admin/filter_listing.html'
    resource_class = ShopUserResource
    change_form_template = 'loginas/change_form.html'

    def get_fieldsets(self, request, obj=None):
        if not obj:
            return super().get_fieldsets(request, obj)
        fieldsets = [
            (None, {'fields': ('phone', 'password')}),
            ('Personal info', {'fields': ('name', 'username', 'email', 'postcode', 'city', 'address')}),
            ('Marketing', {'fields': ('discount','tags')}),
            ('Important dates', {'fields': ('last_login',)}),
        ]
        #if obj is None or obj.is_firm:
        #    fieldsets[2][1]['fields'].extend(('firm_address', 'firm_details'))
        if request.user.is_superuser:
            fieldsets.append(('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}))
        return fieldsets


# Now register the new UserAdmin...
admin.site.register(ShopUser, ShopUserAdmin)
