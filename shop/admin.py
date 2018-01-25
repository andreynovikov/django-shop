import datetime

from django import forms
from django.core.urlresolvers import reverse
from django.db import connection
from django.db.models import TextField, PositiveSmallIntegerField, PositiveIntegerField, TimeField, DateTimeField
from django.contrib import admin, messages
from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.http import HttpResponse, HttpResponseRedirect
from django.template.loader import get_template
from django.template.defaultfilters import floatformat
from django.conf import settings
from django.conf.urls import url
from django.shortcuts import render
from django.utils import timezone
from django.utils.formats import date_format
from django.utils.translation import ugettext, ugettext_lazy as _

import autocomplete_light
from datetimewidget.widgets import TimeWidget
from suit.admin import SortableModelAdmin
from django.forms import ModelForm, TextInput
from suit.widgets import AutosizedTextarea
from mptt.admin import MPTTModelAdmin

from shop.models import ShopUserManager, ShopUser, Category, Supplier, Contractor, \
    Currency, Country, Manufacturer, Product, Stock, Basket, BasketItem, Manager, \
    Courier, Order, OrderItem
from shop.decorators import admin_changelist_link

from django.apps import AppConfig


class SortableMPTTModelAdmin(MPTTModelAdmin, SortableModelAdmin):
    def __init__(self, *args, **kwargs):
        super(SortableMPTTModelAdmin, self).__init__(*args, **kwargs)
        mptt_opts = self.model._mptt_meta
        # NOTE: use mptt default ordering
        self.ordering = (mptt_opts.tree_id_attr, mptt_opts.left_attr)
        if self.list_display and self.sortable not in self.list_display:
            self.list_display = list(self.list_display) + [self.sortable]

        self.list_editable = self.list_editable or []
        if self.sortable not in self.list_editable:
            self.list_editable = list(self.list_editable) + [self.sortable]

        self.exclude = self.exclude or []
        if self.sortable not in self.exclude:
            self.exclude = list(self.exclude) + [self.sortable]

    # NOTE: return default admin ChangeList
    def get_changelist(self, request, **kwargs):
        return admin.views.main.ChangeList

    def is_bulk_edit(self, request):
        changelist_url = 'admin:%(app_label)s_%(model_name)s_changelist' % {
            'app_label': self.model._meta.app_label,
            'model_name': self.model._meta.model_name,
        }
        return (request.path == reverse(changelist_url) and
                request.method == 'POST' and '_save' in request.POST)

    def save_model(self, request, obj, form, change):
        super(SortableMPTTModelAdmin, self).save_model(request, obj, form, change)
        if not self.is_bulk_edit(request):
            self.model.objects.rebuild()

    def changelist_view(self, request, extra_context=None):
        response = super(SortableMPTTModelAdmin, self).changelist_view(request, extra_context)
        if self.is_bulk_edit(request):
            self.model.objects.rebuild()
        return response


class CategoryForm(ModelForm):
    class Meta:
        widgets = {
            'brief': AutosizedTextarea(attrs={'rows': 3,}),
            'description': AutosizedTextarea(attrs={'rows': 3,}),
        }


@admin.register(Category)
class CategoryAdmin(SortableMPTTModelAdmin):
    mptt_level_indent = 20
    search_fields = ('name','slug')
    prepopulated_fields = {'slug': ('name',)}
    list_display = ('name', 'slug', 'basset_id', 'active')
    list_editable = ['active']
    list_display_links = ['name']
    sortable = 'order'
    exclude = ('image_width', 'image_height', 'promo_image_width', 'promo_image_height')
    form = CategoryForm


@admin.register(Supplier)
class SupplierAdmin(SortableModelAdmin):
    list_display = ['id', 'code', 'name', 'show_in_order']
    list_display_links = ['name']
    search_fields = ['code', 'name']
    sortable = 'order'


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


@admin.register(Manufacturer)
class ManufacturerAdmin(admin.ModelAdmin):
    list_display = ['id', 'code', 'name', 'machinemaker', 'accessorymaker']
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


class StockInline(admin.TabularInline):
    model = Stock
    readonly_fields = ['supplier', 'quantity']
    suit_classes = 'suit-tab suit-tab-stock'

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class ProductForm(ModelForm):
    class Meta:
        widgets = {
            'gtin': TextInput(attrs={'size': 10}),
            'spec': AutosizedTextarea(attrs={'rows': 3,}),
            'shortdescr': AutosizedTextarea(attrs={'rows': 3,}),
            'yandexdescr': AutosizedTextarea(attrs={'rows': 3,}),
            'descr': AutosizedTextarea(attrs={'rows': 3,}),
            'state': AutosizedTextarea(attrs={'rows': 2,}),
            'complect': AutosizedTextarea(attrs={'rows': 3,}),
            'dealertxt': AutosizedTextarea(attrs={'rows': 2,})
        }


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    def calm_forbid_price_import(self, obj):
        if obj.forbid_price_import:
            return '<span style="color: red">&#10004;</span>'
        else:
            return ''
    calm_forbid_price_import.allow_tags = True
    calm_forbid_price_import.admin_order_field = 'forbid_price_import'
    calm_forbid_price_import.short_description = 'ос. цена'

    def product_stock(self, obj):
        result = ''
        suppliers = obj.stock.filter(show_in_order=True).order_by('order')
        if suppliers.exists():
            for supplier in suppliers:
                stock = Stock.objects.get(product=obj, supplier=supplier)
                result = result + ('%s:&nbsp;' % supplier.code)
                if stock.quantity == 0:
                    result = result + '<span style="color: #c00">'
                result = result + ('%s' % floatformat(stock.quantity))
                if stock.quantity == 0:
                    result = result + '</span>'
                result = result + '<br/>'
        else:
            result = '<span style="color: #f00">отсутствует</span><br/>'
        #cursor = connection.cursor()
        #cursor.execute("""SELECT SUM(shop_orderitem.quantity) AS quantity FROM shop_orderitem
        #                  INNER JOIN shop_order ON (shop_orderitem.order_id = shop_order.id) WHERE shop_order.status IN (0,1,4,64,256,1024)
        #                  AND shop_orderitem.product_id = %s GROUP BY shop_orderitem.product_id""", (obj.id,))
        #if cursor.rowcount:
        #    row = cursor.fetchone()
        #    result  = result + '<span style="color: #00c">Зак:&nbsp;%s</span><br/>' % floatformat(row[0])
        #cursor.close()
        if obj.num_correction:
            result  = result + '<span style="color: #f00">Кор:&nbsp;%s</span><br/>' % obj.num_correction
        return result
    product_stock.allow_tags=True
    product_stock.short_description = 'склад'

    @admin_changelist_link(None, 'заказы', model=Order, query_string=lambda p: 'item__product__pk={}'.format(p.pk))
    def orders_link(self, orders):
        return '<i class="icon-list"></i>'

    form = ProductForm
    list_display = ['article', 'title', 'price', 'cur_price', 'cur_code', 'calm_forbid_price_import', 'pct_discount', 'val_discount', 'product_stock', 'orders_link']
    list_display_links = ['title']
    list_filter = ['cur_code', 'pct_discount', 'val_discount', 'categories']
    exclude = ['image_prefix']
    search_fields = ['code', 'article', 'partnumber', 'title']
    readonly_fields = ['price', 'ws_price', 'sp_price']
    inlines = (StockInline,)
    fieldsets = (
        (None, {
                'classes': ('suit-tab', 'suit-tab-general'),
                'fields': (('code', 'article', 'partnumber'),'title','runame','whatis','categories',('manufacturer','gtin'),('country','developer_country'),'spec','shortdescr','yandexdescr','descr','state','complect','dealertxt',)
        }),
        ('Деньги', {
                'classes': ('suit-tab', 'suit-tab-general'),
                'fields': (('cur_price', 'cur_code', 'price'), ('pct_discount', 'val_discount', 'max_discount'),
                           ('ws_cur_price', 'ws_cur_code', 'ws_price'), ('ws_pct_discount', 'ws_max_discount'),
                           ('sp_cur_price', 'sp_cur_code', 'sp_price'), 'consultant_delivery_price', ('forbid_price_import'))
        }),
        ('Маркетинг', {
                'classes': ('suit-tab', 'suit-tab-general'),
                'fields': (('enabled','available','show_on_sw'),'isnew','deshevle','recomended','gift','market','sales_notes','internetonly','present','delivery','firstpage',)
        }),
        ('Размеры', {
                'classes': ('suit-tab', 'suit-tab-general'),
                'fields': ('dimensions','measure','weight','prom_weight',)
        }),
        ('Вязальные машины', {
                'classes': ('suit-tab', 'suit-tab-knittingmachines'),
                'fields': (
                    'km_class',
                    'km_needles',
                    'km_font',
                    'km_prog',
                    'km_rapport',)
        }),
        ('Швейные машины', {
                'classes': ('suit-tab', 'suit-tab-sewingmachines'),
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
                'classes': ('suit-tab', 'suit-tab-general'),
                'fields': ('warranty', 'extended_warranty', 'manufacturer_warranty') # запятая в конце нужна, если в списке одна позиция
        }),
        ('Остальное', {
                'classes': ('suit-tab', 'suit-tab-other'),
                'fields': (
                    'swcode',
                    'oprice',
                    'coupon',
                    'not_for_sale','absent',
                    'suspend',
                    'opinion',
                    'num',('bid','cbid'),
                    'whatisit',
                )
        }),
        ('Промышленные машины', {
                'classes': ('suit-tab', 'suit-tab-prommachines'),
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
        ('Разное', {
                'classes': ('suit-tab', 'suit-tab-stock'),
                'fields': (
                    'num_correction',
                )
        }),
    )
    suit_form_tabs = (
        ('general', 'Основное'),
        ('sewingmachines', 'Швейные машины'),
        ('knittingmachines', 'Вязальные машины'),
        ('prommachines', 'Промышленные машины'),
        ('other', 'Остальное'),
        ('stock', 'Запасы'),
    )


class BasketItemInline(admin.TabularInline):
    model = BasketItem
    extra = 0


@admin.register(Basket)
class BasketAdmin(admin.ModelAdmin):
    list_display = ['phone', 'created', 'was_created_recently']
    list_filter = ['phone', 'created']
    exclude = ['session']
    inlines = [BasketItemInline]


@admin.register(Manager)
class ManagerAdmin(admin.ModelAdmin):
    def colorbar(self, obj):
        return '<div style="width: 40px; background-color: ' + obj.color + '">&nbsp;</div>'
    colorbar.allow_tags = True
    colorbar.admin_order_field = 'color'
    colorbar.short_description = 'цвет'

    list_display = ['name', 'colorbar']
    list_display_links = ['name']
    search_fields = ['name']
    ordering = ['name']


@admin.register(Courier)
class CourierAdmin(admin.ModelAdmin):
    def colorbar(self, obj):
        return '<div style="width: 40px; background-color: ' + obj.color + '">&nbsp;</div>'
    colorbar.allow_tags = True
    colorbar.admin_order_field = 'color'
    colorbar.short_description = 'цвет'

    list_display = ['name', 'colorbar']
    list_display_links = ['name']
    search_fields = ['name']
    ordering = ['name']


class OrderItemInline(admin.TabularInline):
    def product_article(self, obj):
        return obj.product.article
    product_article.admin_order_field = 'product__article'
    product_article.short_description = 'артикул'

    def product_code(self, obj):
        return obj.product.code
    product_code.admin_order_field = 'product__code'
    product_code.short_description = 'код'

    def product_link(self, obj):
        link=reverse('admin:shop_product_change', args=[obj.product.id])
        return '<a href="%s?_popup=1" class="related-widget-wrapper-link">%s</a>&nbsp;<i class="icon-pencil icon-alpha5"></i>' % (link, str(obj.product))
    product_link.allow_tags=True
    product_link.short_description = 'товар'

    def product_stock(self, obj):
        result = ''
        suppliers = obj.product.stock.filter(show_in_order=True).order_by('order')
        if suppliers.exists():
            for supplier in suppliers:
                stock = Stock.objects.get(product=obj.product, supplier=supplier)
                result = result + ('%s:&nbsp;' % supplier.code)
                if stock.quantity == 0:
                    result = result + '<span style="color: #c00">'
                result = result + ('%s' % floatformat(stock.quantity))
                if stock.quantity == 0:
                    result = result + '</span>'
                result = result + '<br/>'
        else:
            result = '<span style="color: #f00">отсутствует</span><br/>'
        cursor = connection.cursor()
        cursor.execute("""SELECT shop_orderitem.order_id, shop_orderitem.quantity AS quantity FROM shop_orderitem
                          INNER JOIN shop_order ON (shop_orderitem.order_id = shop_order.id) WHERE shop_order.status IN (0,1,4,64,256,1024)
                          AND shop_orderitem.product_id = %s AND shop_order.id != %s""", (obj.product.id, obj.order.id))
        if cursor.rowcount:
            ordered = 0
            ids = [str(obj.order.id)]
            for row in cursor:
                ids.append(str(row[0]))
                ordered = ordered + int(row[1])
            url = '%s?id__in=%s&status=any' % (reverse("admin:shop_order_changelist"), ','.join(ids))
            result = result + '<a href="%s" style="color: #00c">Зак:&nbsp;%s<br/></a>' % (url, floatformat(ordered))
        cursor.close()
        if obj.product.num_correction:
            result  = result + '<span style="color: #f00">Кор:&nbsp;%s</span><br/>' % obj.product.num_correction
        return result
    product_stock.allow_tags=True
    product_stock.short_description = 'склад'

    def item_cost(self, obj):
        return obj.cost
    item_cost.short_description = 'стоимость'

    def item_sum(self, obj):
        sum=obj.quantity*obj.cost
        return sum
    item_sum.short_description = 'сумма'

    model = OrderItem
    extra = 0
    fields = ['product', 'product_article', 'product_code', 'product_link', 'product_price', 'pct_discount', 'val_discount', 'item_cost', 'quantity', 'item_sum', 'product_stock']
    raw_id_fields = ['product']
    #autocomplete_lookup_fields = {
    #    'fk': ['product'],
    #}
    readonly_fields = ['product_link', 'product_article', 'product_code', 'product_stock', 'item_cost', 'item_sum']
    formfield_overrides = {
        PositiveSmallIntegerField: {'widget': forms.TextInput(attrs={'style': 'width: 4em'})},
        PositiveIntegerField: {'widget': forms.TextInput(attrs={'style': 'width: 6em'})},
    }

    def has_add_permission(self, request):
        return False


class AddOrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    #raw_id_fields = ['product']
    #autocomplete_lookup_fields = {
    #    'fk': ['product'],
    #}
    form = autocomplete_light.modelform_factory(OrderItem, exclude=['fake'])
    formfield_overrides = {
        PositiveSmallIntegerField: {'widget': forms.TextInput(attrs={'style': 'width: 4em'})},
        PositiveIntegerField: {'widget': forms.TextInput(attrs={'style': 'width: 6em'})},
    }

    def has_change_permission(self, request, obj=None):
        return False

class OrderStatusListFilter(admin.SimpleListFilter):
    title = _('статус')

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
            ('any', _('любой')), # hack for Django Suit: it removes first choice
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
        if self.value() == 'any':
            return None
        if self.value():
            return queryset.filter(status__exact=self.value())
        if self.value() is None:
            return queryset.filter(status__in=[Order.STATUS_NEW, Order.STATUS_ACCEPTED, Order.STATUS_COLLECTING, Order.STATUS_COLLECTED, Order.STATUS_SENT, Order.STATUS_DELIVERED_SHOP, Order.STATUS_CONSULTATION, Order.STATUS_PROBLEM, Order.STATUS_SERVICE])


class FutureDateFieldListFilter(admin.FieldListFilter):
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
class OrderAdmin(admin.ModelAdmin):
    def order_name(self, obj):
        manager = ''
        if obj.manager:
            manager = ' style="color: %s"' % obj.manager.color
        return '<b%s>%s</b><br/><span style="white-space:nowrap">%s</span>' % (manager, obj.id, date_format(timezone.localtime(obj.created), "DATETIME_FORMAT"))
    order_name.allow_tags = True
    order_name.admin_order_field = 'id'
    order_name.short_description = 'заказ'

    def combined_comments(self, obj):
        return '<span style="color:#008">%s</span> %s<br/><em>%s</em>' % (obj.delivery_yd_order, obj.delivery_info, obj.manager_comment)
    combined_comments.allow_tags = True
    combined_comments.admin_order_field = 'manager_comment'
    combined_comments.short_description = 'Комментарии'

    def combined_delivery(self, obj):
        datetime = ''
        if obj.delivery_date:
            datetime = date_format(obj.delivery_date, "SHORT_DATE_FORMAT")
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
    combined_delivery.allow_tags = True
    combined_delivery.admin_order_field = 'delivery_date'
    combined_delivery.short_description = 'Доставка'

    def name_and_skyped_phone(self, obj):
        return '%s<br/><a href="skype:%s?call">%s</a>' % (obj.name, obj.phone, ShopUserManager.format_phone(obj.phone))
    name_and_skyped_phone.allow_tags = True
    name_and_skyped_phone.admin_order_field = 'phone'
    name_and_skyped_phone.short_description = 'Покупатель'

    def skyped_phone(self, obj):
        return '<a href="skype:%s?call">%s</a>' % (obj.phone, ShopUserManager.format_phone(obj.phone))
    skyped_phone.allow_tags = True
    skyped_phone.admin_order_field = 'phone'
    skyped_phone.short_description = 'телефон'

    def colored_status(self, obj):
        return '<span style="color: %s">%s</span>' % (obj.STATUS_COLORS[obj.status], obj.get_status_display())
    colored_status.allow_tags = True
    colored_status.admin_order_field = 'status'
    colored_status.short_description = 'статус'

    def calm_paid(self, obj):
        if obj.paid:
            return '<span style="color: green">&#10004;</span>'
        else:
            return ''
    calm_paid.allow_tags = True
    calm_paid.admin_order_field = 'paid'
    calm_paid.short_description = 'оплачен'

    def was_created_recently(self, obj):
        return obj.created >= timezone.now() - datetime.timedelta(days=1)
    was_created_recently.admin_order_field = 'created'
    was_created_recently.boolean = True
    was_created_recently.short_description = 'недавний?'

    def link_to_user(self, obj):
        inconsistency = ''
        if obj.name != obj.user.name or obj.phone != obj.user.phone or \
           obj.email != obj.user.email or obj.postcode != obj.user.postcode or \
           obj.address != obj.user.address:
            inconsistency = '<span style="color: red" title="Несоответствие данных!">&#10033;</span>'
        return inconsistency
    link_to_user.allow_tags = True
    link_to_user.short_description = 'несоответствие'

    def link_to_orders(self, obj):
        orders = Order.objects.filter(user=obj.user.id).exclude(pk=obj.id)
        if not orders:
            return '<span>нет</span>'
        else:
            url = '%s?user__exact=%s&status=any' % (reverse("admin:shop_order_changelist"), obj.user.id)
            return '<span><a href="%s">%d</a></span>' % (url, orders.count())
    link_to_orders.allow_tags = True
    link_to_orders.short_description = 'заказы'


    list_display = ['order_name', 'name_and_skyped_phone', 'city', 'total', 'payment', 'calm_paid', 'combined_delivery',
                    'colored_status', 'combined_comments']
    readonly_fields = ['id', 'shop_name', 'total', 'created', 'link_to_user', 'link_to_orders', 'skyped_phone']
    list_filter = [OrderStatusListFilter, 'created', 'payment', 'paid', 'manager', 'courier', 'delivery', ('delivery_date', FutureDateFieldListFilter)]
    search_fields = ['id', 'name', 'phone', 'email', 'address', 'city',
                     'user__name', 'user__phone', 'user__email', 'user__address', 'user__postcode', 'manager_comment']
    fieldsets = (
        (None, {'fields': (('status', 'payment', 'paid', 'manager', 'site'), ('delivery', 'delivery_price', 'courier'),
                           ('delivery_date', 'delivery_time_from', 'delivery_time_till'),
                            'delivery_tracking_number', 'delivery_info', 'manager_comment', 'total', 'id')}),
        ('1С', {'fields': (('buyer', 'seller','wiring_date'),),}),
        ('Яндекс.Доставка', {'fields': ('delivery_yd_order',)}),
        ('PickPoint', {'fields': (('delivery_pickpoint_terminal', 'delivery_pickpoint_service', 'delivery_pickpoint_reception'),
                                  ('delivery_size_length', 'delivery_size_width', 'delivery_size_height'),),}),
        ('Покупатель', {'fields': (('name', 'user', 'link_to_user', 'link_to_orders'), ('phone', 'phone_aux'),
                                    'email', 'postcode', 'city', 'address', 'comment',
                                   ('firm_name', 'is_firm'), 'firm_address', 'firm_details',)}),
    )
    inlines = [OrderItemInline, AddOrderItemInline]
    #raw_id_fields = ('user',)
    form = autocomplete_light.modelform_factory(Order, exclude=['created'])
    formfield_overrides = {
        TextField: {'widget': forms.Textarea(attrs={'style': 'height: 4em'})},
        TimeField: {'widget': TimeWidget()},
    }
    actions = ['order_product_list_action', 'order_1c_action', 'order_pickpoint_action']
    save_as = True
    list_per_page = 50

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
        cursor = connection.cursor()
        inner_cursor = connection.cursor()
        cursor.execute("""SELECT shop_product.id AS product_id, shop_product.article, shop_product.partnumber, shop_product.title,
                          shop_order.id AS order_id, shop_order.status AS order_status,
                          SUM(shop_orderitem.quantity) AS quantity
                          FROM shop_product
                          INNER JOIN shop_orderitem ON (shop_product.id = shop_orderitem.product_id)
                          INNER JOIN shop_order ON (shop_orderitem.order_id = shop_order.id)""" + where +
                          """ GROUP BY shop_order.id, shop_product.id ORDER BY shop_product.title""")
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
            'products': products,
            'cl': self,
            'opts': self.model._meta,
        })

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

    def get_actions(self, request):
        actions = super(OrderAdmin, self).get_actions(request)
        del actions['delete_selected']
        return actions


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

    def clean_password(self):
        # Regardless of what the user provides, return the initial value.
        # This is done here, rather than on the field, because the
        # field does not have access to the initial value
        return self.initial["password"]


class ShopUserAdmin(UserAdmin):
    # The forms to add and change user instances
    form = UserChangeForm
    add_form = UserCreationForm

    # The fields to be used in displaying the User model.
    # These override the definitions on the base UserAdmin
    # that reference specific fields on auth.User.
    list_display = ('phone', 'name', 'email', 'discount', 'is_wholesale', 'is_admin')
    list_filter = ('is_wholesale', 'is_admin', 'discount')
    fieldsets = (
        (None, {'fields': ('phone', 'password')}),
        ('Personal info', {'fields': ('name', 'email', 'postcode', 'city', 'address')}),
        ('Marketing', {'fields': ('discount',)}),
        ('Permissions', {'fields': ('is_active', 'is_wholesale', 'is_staff', 'is_admin',)}),
        ('Important dates', {'fields': ('last_login',)}),
    )
    # add_fieldsets is not a standard ModelAdmin attribute. UserAdmin
    # overrides get_fieldsets to use this attribute when creating a user.
    add_fieldsets = (
        (None, {
            'fields': ('phone', 'name', 'password1', 'password2')}
        ),
    )
    search_fields = ('phone', 'name', 'email')
    ordering = ('phone', 'name')
    filter_horizontal = ()
    #change_list_template = 'admin/change_list_filter_sidebar.html'
    #change_list_filter_template = 'admin/filter_listing.html'


# Now register the new UserAdmin...
admin.site.register(ShopUser, ShopUserAdmin)
# ... and, since we're not using Django's built-in permissions,
# unregister the Group model from admin.
admin.site.unregister(Group)
