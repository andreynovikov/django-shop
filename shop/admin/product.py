import logging
import os

from django.forms import TextInput
from django.urls import reverse
from django.db.models import PositiveSmallIntegerField, PositiveIntegerField, \
    DecimalField, FloatField, ImageField, Q
from django.core.exceptions import PermissionDenied
from django.core.files import File
from django.core.files.storage import default_storage
from django.contrib import admin
from django.http import JsonResponse, HttpResponse
from django.template.response import TemplateResponse
from django.conf.urls import url
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from adminsortable2.admin import SortableInlineAdminMixin
from django_better_admin_arrayfield.admin.mixins import DynamicArrayMixin
from django_admin_listfilter_dropdown.filters import SimpleDropdownFilter
from django_admin_listfilter_dropdown.filters import DropdownFilter, RelatedDropdownFilter
from reviews.admin import ReviewAdmin, ReviewAdminForm

from import_export import resources
from import_export.admin import ImportExportMixin

from flags.state import flag_enabled

from shop.models import Product, ProductImage, ProductRelation, ProductSet, ProductKind, \
    ProductReview, Stock, Integration, Order
from .forms import ProductImportForm, ProductConfirmImportForm, ProductExportForm, \
    ProductAdminForm, ProductListAdminForm, ProductKindForm, StockInlineForm, IntegrationInlineForm, \
    ProductCloneForm, OneSImportForm
from .decorators import admin_changelist_link
from .views import product_stock_view
from .widgets import ImageWidget


logger = logging.getLogger(__name__)


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


class ProductImageInline(SortableInlineAdminMixin, admin.TabularInline):
    model = ProductImage
    extra = 0
    formfield_overrides = {
        ImageField: {
            'widget': ImageWidget
        }
    }
    verbose_name = "дополнительное изображение"
    verbose_name_plural = "дополнительные изображения"


class StockInline(admin.TabularInline):
    model = Stock
    form = StockInlineForm
    fields = ['supplier', 'quantity', 'correction', 'reason']
    extra = 0
    classes = ['collapse']
    formfield_overrides = {
        FloatField: {'widget': TextInput(attrs={'style': 'width: 8em'})},
    }

    def has_delete_permission(self, request, obj=None):
        return obj is None  # False


class IntegrationInline(admin.TabularInline):
    model = Integration.products.through
    form = IntegrationInlineForm
    fields = ['integration', 'price', 'notify_stock']
    ordering = ['integration__name']
    extra = 0
    classes = ['collapse']
    verbose_name = "интеграция"
    verbose_name_plural = "интеграции"


class ProductSetInline(admin.TabularInline):
    model = ProductSet
    fk_name = 'declaration'
    ordering = ('constituent__title',)
    autocomplete_fields = ('constituent',)
    extra = 0
    verbose_name = "составляющая"
    verbose_name_plural = "составляющие"


class ProductRelationInline(admin.TabularInline):
    model = ProductRelation
    fk_name = 'parent_product'
    ordering = ('kind',)
    autocomplete_fields = ('child_product',)
    extra = 0
    verbose_name = "связанный товар"
    verbose_name_plural = "связанные товары"
    classes = ['collapse']


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
        exclude = ('categories', 'stock', 'num', 'related', 'constituents', 'images')


class IntegrationsFilter(SimpleDropdownFilter):
    title = _('интеграции')
    parameter_name = 'integration'

    def lookups(self, request, model_admin):
        return [(i.id, i.name) for i in Integration.objects.all()]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(integration__exact=self.value())
        else:
            return queryset


@admin.register(Product)
class ProductAdmin(ImportExportMixin, admin.ModelAdmin, DynamicArrayMixin):
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
        result = '<span style="color: '
        if obj.val_discount > 0:
            result = result + 'black'
        else:
            result = result + 'grey'
        result = result + '">%s&nbsp;руб<br/><span style="color: ' % obj.val_discount
        if obj.pct_discount > 0:
            result = result + 'black'
        else:
            result = result + 'grey'
        result = result + '">%s%%</span>' % obj.pct_discount
        return result
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

    def integrations(self, obj):
        pass
    integrations.short_description = 'внешние интеграции'

    form = ProductAdminForm
    change_list_template = 'admin/shop/product/change_list.html'
    resource_class = ProductResource
    list_display = ['product_codes', 'title', 'combined_price', 'combined_discount', 'enabled', 'show_on_sw',
                    'market', 'integrations', 'product_stock', 'orders_link', 'product_link']
    list_display_links = ['title']
    list_editable = ['enabled', 'show_on_sw', 'market']
    list_filter = ['enabled', 'preorder', 'show_on_sw', IntegrationsFilter, 'market', 'isnew', 'recomended',
                   'forbid_price_import', 'cur_code', ('pct_discount', DropdownFilter), ('val_discount', DropdownFilter),
                   ('categories', RelatedDropdownFilter), ('manufacturer', RelatedDropdownFilter)]
    list_per_page = 50
    search_fields = ['code', 'article', 'partnumber', 'title', 'tags']
    readonly_fields = ['price', 'ws_price', 'sp_price']
    ordering = ('-id',)
    save_on_top = True
    view_on_site = True
    inlines = (ProductImageInline, ProductSetInline, ProductRelationInline, IntegrationInline, StockInline)
    filter_vertical = ('categories',)
    autocomplete_fields = ('manufacturer',)
    formfield_overrides = {
        PositiveSmallIntegerField: {'widget': TextInput(attrs={'style': 'width: 4em'})},
        PositiveIntegerField: {'widget': TextInput(attrs={'style': 'width: 8em'})},
        DecimalField: {'widget': TextInput(attrs={'style': 'width: 4em'})},
        FloatField: {'widget': TextInput(attrs={'style': 'width: 4em'})},
    }
    fieldsets = (
        ('Основное', {
            'classes': ('collapse',),
            'fields': (('code', 'article'), ('partnumber', 'tnved'), 'title', 'runame', 'whatis', 'whatisit', 'kind', 'categories',
                       'manufacturer', ('gtin', 'gtins'), ('country', 'developer_country'), 'variations', 'spec', 'shortdescr',
                       'yandexdescr', 'descr', 'manuals', 'state', 'complect', 'dealertxt')
        }),
        ('Деньги', {
            'classes': ('collapse',),
            'fields': (('cur_price', 'cur_code', 'price'), ('pct_discount', 'val_discount', 'max_discount', 'max_val_discount'),
                       ('ws_cur_price', 'ws_cur_code', 'ws_price'), 'ws_pack_only', ('ws_pct_discount', 'ws_max_discount'),
                       ('sp_cur_price', 'sp_cur_code', 'sp_price'), 'consultant_delivery_price',
                       ('forbid_price_import', 'forbid_ws_price_import'))
        }),
        ('Маркетинг', {
            'classes': ('collapse',),
            'fields': (('enabled', 'show_on_sw', 'firstpage'), 'market', ('preorder', 'isnew', 'recomended', 'gift'), 'credit_allowed', 'deshevle',
                       'sales_notes', 'present', 'delivery', 'sales_actions', 'tags')
        }),
        ('Размеры', {
            'classes': ('collapse',),
            'fields': (('measure', 'pack_factor'), ('weight', 'prom_weight'), ('length', 'width', 'height'))
        }),
        ('Вязальные машины', {
            'classes': ('collapse',),
            'fields': ('km_class', 'km_needles', 'km_font', 'km_prog', 'km_rapport')
        }),
        ('Швейные машины', {
            'classes': ('collapse',),
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
            'classes': ('collapse',),
            'fields': ('warranty', 'extended_warranty', 'manufacturer_warranty', 'comment_warranty', 'service_life')
        }),
        ('Остальное', {
            'classes': ('collapse',),
            'fields': (
                'comment_packer',
                'order',
                'swcode',
                'coupon',
                'not_for_sale',
                'absent',
                'suspend',
                'opinion',
                'allow_reviews',
                ('bid', 'cbid'),
            )
        }),
        ('Промышленные машины', {
            'classes': ('collapse',),
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
            'classes': ('collapse',),
            'fields': ('recalculate_price', 'hide_contents')
        }),
        ('Изображения товара', {
            'classes': ('collapse',),
            'fields': ('image', 'big_image')
        }),
    )

    """
    def get_formsets_with_inlines(self, request, obj=None):
        for inline in self.get_inline_instances(request, obj):
            if request.user.is_superuser or not request.user.has_perm('shop.change_order_spb'):
                yield inline.get_formset(request, obj), inline
    """

    def get_changelist_form(self, request, **kwargs):
        return ProductListAdminForm

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
        """
        if change:
            obj.num = obj.get_stock()
        else:
        """
        obj.num = -1
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
            url(r'(\d+)/clone/$', self.admin_site.admin_view(self.clone_form), name='%s_%s_clone' % info),
            url(r'^stock/correction/$', self.admin_site.admin_view(self.stock_correction_view), name='%s_%s_stock_correction' % info),
            url(r'^import1c/$', self.admin_site.admin_view(self.import_1c_view), name='%s_%s_import_1c' % info),
            url(r'^import1c/status/$', self.admin_site.admin_view(self.import_1c_status_view), name='%s_%s_import_1c_status' % info),
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

    def clone_form(self, request, id):
        if not request.user.is_staff:
            raise PermissionDenied
        product = Product.objects.get(pk=id)
        messages = None
        if request.method != 'POST':
            form = ProductCloneForm()
            is_popup = request.GET.get('_popup', 0)
        else:
            form = ProductCloneForm(request.POST)
            is_popup = request.POST.get('_popup', 0)
            if form.is_valid():
                try:
                    product_code = form.cleaned_data['product_code']
                    other_product = Product.objects.filter(code=product_code).first()
                    if other_product:
                        form.add_error('product_code', "Товар с таким кодом уже существует")
                    else:
                        # remember relations
                        old_kind = product.kind.all()
                        old_categories = product.categories.all()
                        old_sales_actions = product.sales_actions.all()
                        old_related = product.related.all()
                        old_constituents = product.constituents.all()
                        old_image = product.image
                        old_big_image = product.big_image
                        old_images = list(product.images.all())
                        # clone object
                        product.image = None
                        product.big_image = None
                        product.pk = None
                        product._state.adding = True
                        product.code = product_code
                        product.save()
                        product.kind.set(old_kind)
                        product.categories.set(old_categories)
                        product.sales_actions.set(old_sales_actions)
                        product.related.set(old_related)
                        product.constituents.set(old_constituents)
                        # copy images
                        product.image.save(os.path.basename(old_image.path), old_image)
                        product.big_image.save(os.path.basename(old_big_image.path), old_big_image)
                        for image in old_images:
                            product_image = ProductImage(product=product, order=image.order)
                            product_image.image.save(os.path.basename(image.image.path), image.image)
                            product_image.save()

                        return HttpResponse('<!DOCTYPE html><html><head><title></title></head><body>'
                                            '<script type="text/javascript">opener.dismissPopupAndReload(window);</script>'
                                            '</body></html>')
                except Exception as e:
                    form.errors['__all__'] = form.error_class([str(e)])

        context = self.admin_site.each_context(request)
        context['cl'] = self
        context['opts'] = self.model._meta
        context['form'] = form
        context['is_popup'] = is_popup
        context['messages'] = messages
        context['title'] = "Укажите новый код товара"
        context['action_title'] = "Клонировать"

        return TemplateResponse(request, 'admin/shop/custom_action_form.html', context)

    def import_1c_view(self, request):
        if not request.user.is_staff:
            raise PermissionDenied
        context = {
            'title': "Импорт 1С",
            'cl': self,
            **self.admin_site.each_context(request)
        }
        if request.method == 'POST':
            form = OneSImportForm(request.POST, request.FILES)
            if form.is_valid():
                result = form.save()
                context['result'] = result
            else:
                context['form'] = form
            context['is_popup'] = request.POST.get('_popup', 0)
        else:
            form = OneSImportForm()
            context['form'] = form
            context['is_popup'] = request.GET.get('_popup', 0)
        return TemplateResponse(request, 'admin/shop/import_1c.html', context)

    def import_1c_status_view(self, request):
        if not request.user.is_staff:
            raise PermissionDenied
        return JsonResponse({
            'running': flag_enabled('1C_IMPORT_RUNNING'),
            'copying': flag_enabled('1C_IMPORT_COPYING')
        })


@admin.register(ProductKind)
class ProductKindAdmin(admin.ModelAdmin):
    form = ProductKindForm
    list_display = ['name']
    list_display_links = ['name']
    search_fields = ['name']
    ordering = ['name']


class ProductReviewAdminForm(ReviewAdminForm):
    class Meta(ReviewAdminForm.Meta):
        model = ProductReview

class ProductReviewAdmin(ReviewAdmin):
    form = ProductReviewAdminForm
    fieldsets = (
        (
            None,
            {'fields': ('content_type', 'object_pk', 'site')}
        ),
        (
            _('Content'),
            {'fields': ('user', 'rating', 'weight', 'comment')}
        ),
        (
            'Дополнительно',
            {'fields': ('advantage', 'disadvantage', 'reviewer_name', 'reviewer_avatar'),
             'classes': ('collapse',)}
        ),
        (
            _('Metadata'),
            {'fields': ('submit_date', 'ip_address', 'is_public')}
        ),
    )

admin.site.register(ProductReview, ProductReviewAdmin)
