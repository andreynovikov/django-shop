import logging
import os

from urllib.parse import quote

from django.forms import TextInput
from django.db.models import PositiveSmallIntegerField, PositiveIntegerField, \
    DecimalField, FloatField, ImageField, Prefetch, Q
from django.conf import settings
from django.contrib import admin
from django.contrib.admin.views.main import ChangeList
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse, HttpResponse
from django.template.response import TemplateResponse
from django.urls import path
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from adminsortable2.admin import SortableInlineAdminMixin, SortableAdminBase
from django_better_admin_arrayfield.admin.mixins import DynamicArrayMixin
from more_admin_filters import DropdownFilter, RelatedDropdownFilter, SimpleDropdownFilter
from reviews.admin import ReviewAdmin, ReviewAdminForm, REVIEW_ADMIN_LINK_SYMBOL

from import_export import resources
from import_export.admin import ImportExportMixin


from shop.models import Category, Product, ProductImage, ProductPrice, ProductRelation, ProductSet, ProductKind, \
    ProductReview, Stock, Integration, Order, ImportRun
from shop.revalidation import product_tag, revalidate_products
from shop.tasks.workflow import post_update_product
from .forms import ProductImportForm, ProductConfirmImportForm, ProductExportForm, \
    ProductAdminForm, ProductListAdminForm, ProductKindForm, StockInlineForm, IntegrationInlineForm, \
    ProductCloneForm, OneSImportForm
from .decorators import admin_changelist_link
from .views import STOCK_PREFETCH, check_permission, join_html, permitted_object, product_stock_view
from .widgets import ImageWidget

SHOP_INFO = getattr(settings, 'SHOP_INFO', {})

logger = logging.getLogger(__name__)


@admin.register(ProductRelation)
class ProductRelationAdmin(admin.ModelAdmin):
    # Methods rather than 'parent_product__title' in list_display, which would give both columns the same header
    @admin.display(description='товар', ordering='parent_product')
    def parent_product_link(self, obj):
        return obj.parent_product.title

    @admin.display(description='связанный товар', ordering='child_product')
    def child_product_link(self, obj):
        return obj.child_product.title

    list_display = ['parent_product_link', 'child_product_link', 'kind']
    list_select_related = ['parent_product', 'child_product']
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


class ProductPriceInline(admin.TabularInline):
    model = ProductPrice
    fields = ['site', 'cur_price', 'price', 'pct_discount', 'val_discount']
    readonly_fields = ['price']
    ordering = ['site__name']
    extra = 0
    formfield_overrides = {
        PositiveSmallIntegerField: {'widget': TextInput(attrs={'style': 'width: 4em'})},
        DecimalField: {'widget': TextInput(attrs={'style': 'width: 8em'})},
    }
    verbose_name = "цена на сайте"
    verbose_name_plural = "цены на сайтах"


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
    verbose_name = "внешняя интеграция"
    verbose_name_plural = "внешние интеграции"


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
        self.product_fields = kwargs.get('product_fields')

    def get_import_id_fields(self):
        return (self.id_field,)

    def export(self, queryset=None, **kwargs):
        kwargs.update(export_fields=self.product_fields)
        return super().export(queryset, **kwargs)

    def after_save_instance(self, instance, row, **kwargs):
        super().after_save_instance(instance, row, **kwargs)
        # sent once the import commits, a dry run rolls it back
        revalidate_products([instance.pk])

    class Meta:
        model = Product
        exclude = ('categories', 'stock', 'num', 'sales_actions', 'related', 'constituents', 'images', 'fts_vector')


class IntegrationsFilter(SimpleDropdownFilter):
    title = _('интеграции')
    parameter_name = 'integration'

    def lookups(self, request, model_admin):
        return [(integration.pk, integration.name) for integration in Integration.objects.select_related('target_site')]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(integration__exact=self.value())
        else:
            return queryset


class CategoryDropdownFilter(RelatedDropdownFilter):
    """ Categories by their full paths, which tell those of the same name apart """
    def field_choices(self, field, request, model_admin):
        paths = Category.paths()
        ordering = self.field_admin_ordering(field, request, model_admin)
        if ordering:
            ids = Category._default_manager.order_by(*ordering).values_list('pk', flat=True)
            return [(pk, paths[pk]) for pk in ids]
        return list(paths.items())


class OzonLinkFilter(admin.SimpleListFilter):
    title = 'ссылка Озон'
    parameter_name = 'ozon_link'

    def lookups(self, request, model_admin):
        return (
            ('blank', 'нет'),
            ('not_blank', 'есть'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'blank':
            return queryset.filter(ozon_link='')
        if self.value() == 'not_blank':
            return queryset.exclude(ozon_link='')
        return queryset


class WBLinkFilter(admin.SimpleListFilter):
    title = 'ссылка WB'
    parameter_name = 'wb_link'

    def lookups(self, request, model_admin):
        return (
            ('blank', 'нет'),
            ('not_blank', 'есть'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'blank':
            return queryset.filter(wb_link='')
        if self.value() == 'not_blank':
            return queryset.exclude(wb_link='')
        return queryset


class ProductChangeList(ChangeList):
    """
    The list of products. What its stock column and the form of each row read is prefetched for the page shown,
    not in get_queryset(), whose products the export also reads.
    """
    def get_results(self, request):
        super().get_results(request)
        self.result_list = self.result_list.prefetch_related(
            *STOCK_PREFETCH, Prefetch('integrations', queryset=Integration.objects.only('id')))


@admin.register(Product)
class ProductAdmin(ImportExportMixin, SortableAdminBase, admin.ModelAdmin, DynamicArrayMixin):
    @admin.display(description='Ид/1С/PN', ordering='code')
    def product_codes(self, obj):
        return join_html([obj.code or '--', obj.article or '--', obj.partnumber or '--'], '<br/>')

    @admin.display(description='цена', ordering='price')
    def combined_price(self, obj):
        result = format_html('{}&nbsp;руб', obj.price)
        if obj.forbid_price_import:
            result += mark_safe('&nbsp;<span style="color: var(--error-fg)">&#10004;</span>')
        # the currency's code is its key: rouble prices don't load it
        if obj.cur_code_id != 643:
            result += format_html('<br/>{}&nbsp;{}', obj.cur_price, obj.cur_code)
        return result

    @admin.display(description='скидка')
    def combined_discount(self, obj):
        def color(discount):
            return 'var(--body-fg)' if discount > 0 else 'var(--border-color)'
        return format_html('<span style="color: {}">{}&nbsp;руб<br/><span style="color: {}">{}%</span>',
                           color(obj.val_discount), obj.val_discount, color(obj.pct_discount), obj.pct_discount)

    @admin.display(description='склад')
    def product_stock(self, obj):
        return product_stock_view(obj)

    @admin_changelist_link(None, 'з', model=Order, query_string=lambda p: 'item__product__pk={}'.format(p.pk))
    def orders_link(self, orders):
        return '<i class="ti ti-basket"></i>'

    @admin.display(description='о')
    def product_link(self, obj):
        return format_html('<a href="{}" target="_blank"><i class="ti ti-external-link"></i></a>', self.view_on_site(obj))

    # An empty column: the list renders ProductListAdminForm's integrations field in it, which every row's form has
    @admin.display(description='внешние интеграции')
    def integrations(self, obj):
        pass

    form = ProductAdminForm
    # change_list_template = 'admin/shop/product/change_list.html'
    import_export_change_list_template = 'admin/shop/product/change_list.html'
    resource_classes = [ProductResource]
    export_form_class = ProductExportForm
    list_display = ['product_codes', 'title', 'combined_price', 'combined_discount', 'enabled', 'show_on_sw',
                    'market', 'integrations', 'product_stock', 'orders_link', 'product_link']
    list_display_links = ['title']
    list_editable = ['enabled', 'show_on_sw', 'market']
    list_filter = ['enabled', 'preorder', 'show_on_sw', OzonLinkFilter, WBLinkFilter, IntegrationsFilter,
                   'market', 'isnew', 'recomended',
                   'forbid_price_import', 'cur_code', ('pct_discount', DropdownFilter), ('val_discount', DropdownFilter),
                   ('categories', CategoryDropdownFilter), ('manufacturer', RelatedDropdownFilter)]
    list_per_page = 50
    list_select_related = ['cur_code']
    search_fields = ['code', 'article', 'partnumber', 'title', 'gtin', 'gtins', 'tags']
    search_help_text = 'Ид, код 1С, PN, название, GTIN или теги товара'
    readonly_fields = ['price', 'ws_price', 'sp_price']
    ordering = ('-id',)
    save_on_top = True
    inlines = (ProductImageInline, ProductPriceInline, ProductSetInline, ProductRelationInline, IntegrationInline, StockInline)
    show_facets = admin.ShowFacets.NEVER
    filter_vertical = ('categories',)
    autocomplete_fields = ('manufacturer',)
    formfield_overrides = {
        PositiveSmallIntegerField: {'widget': TextInput(attrs={'style': 'width: 4em'})},
        PositiveIntegerField: {'widget': TextInput(attrs={'style': 'width: 8em'})},
        DecimalField: {'widget': TextInput(attrs={'style': 'width: 8em'})},
        FloatField: {'widget': TextInput(attrs={'style': 'width: 4em'})},
    }
    fieldsets = (
        ('Основное', {
            'classes': ('collapse',),
            'fields': (('code', 'article'), ('partnumber', 'tnved'), 'title', 'runame', 'whatis', 'whatisit', 'type_prefix', 'kind', 'categories',
                       'manufacturer', ('gtin', 'gtins'), ('country', 'developer_country'), 'variations', 'certificate', 'spec', 'shortdescr',
                       'seodescr', 'yandexdescr', 'descr', 'manuals', 'state', 'complect', 'dealertxt')
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
                'video_url',
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
        ('Интеграции', {
            'classes': ('collapse',),
            'fields': ('ozon_link', 'wb_link')
        }),
    )

    """
    def get_formsets_with_inlines(self, request, obj=None):
        for inline in self.get_inline_instances(request, obj):
            if request.user.is_superuser or not request.user.has_perm('shop.change_order_spb'):
                yield inline.get_formset(request, obj), inline
    """

    def get_search_results(self, request, queryset, search_term):
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)
        if search_term:
            queryset |= self.model.objects.filter(gtins__contains=[search_term])
        return queryset, use_distinct

    def view_on_site(self, obj):
        prefix = SHOP_INFO.get('url_prefix', '')
        return f'{prefix}/products/{quote(obj.code)}.html'

    def get_changelist(self, request, **kwargs):
        return ProductChangeList

    def get_changelist_form(self, request, **kwargs):
        # The integrations to check in each row, read once for the page rather than by the form of each row
        choices = list(ProductListAdminForm.base_fields['integrations'].choices)

        class ProductListForm(ProductListAdminForm):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.fields['integrations'].choices = choices

        return ProductListForm

    def get_import_form(self):
        return ProductImportForm

    def get_confirm_import_form(self):
        return ProductConfirmImportForm

    """
    def get_form_kwargs(self, form, *args, **kwargs):
        if not isinstance(form, type) and form.is_valid():
            kwargs.update({'id_field': form.cleaned_data['id_field']})
        return kwargs
    """

    """
    def get_import_resource_kwargs(self, request, *args, **kwargs):
        if request.POST:
            form = self.get_confirm_import_form()(request.POST)
            form.full_clean()
            return {'id_field': form.cleaned_data['id_field']}
        else:
            return {}
    """

    def get_export_resource_kwargs(self, request, *args, **kwargs):
        export_form = kwargs.get('export_form')
        if export_form:
            kwargs.update(product_fields=export_form.cleaned_data['product_fields'])
        return kwargs

    def save_model(self, request, obj, form, change):
        before = Product.objects.filter(pk=obj.pk).values('code', 'firstpage').first() if change else None
        # Mark cached stock for recount.
        obj.num = -1
        super().save_model(request, obj, form, change)
        # Rebuild the search vector after commit so the worker sees the saved product.
        post_update_product.delay_on_commit(obj.pk, 'admin')
        # Revalidation runs after save_related() updates site assignments. Include pages that used to show the product.
        tags = set()
        if before is not None and before['code'] != obj.code:
            tags.add(product_tag(before['code']))
        if before is not None and before['firstpage']:
            tags.add('firstpage')
        revalidate_products([obj.pk], tags=tags)

    def save_related(self, request, form, formsets, change):
        # this is a hack to avoid stock saving for duplicated products (gives error if stock correction is not zero)
        if '_saveasnew' in request.POST:
            to_remove = [i for i, formset in enumerate(formsets) if isinstance(formset.empty_form.instance, Stock)]
            for index in reversed(to_remove):
                # start at the end to avoid recomputing offsets
                del formsets[index]
        super().save_related(request, form, formsets, change)
        obj = form.instance
        # The product is on the sites whose catalogs have its categories: the root of each category's tree is a
        # site's root category
        sites = [
            profile.site for profile in set(
                c.get_root().profile.get() for c in obj.categories.all()
            ) if profile is not None
        ]
        obj.sites.set(sites)

    def get_urls(self):
        urls = super().get_urls()
        info = self.get_model_info()
        my_urls = [
            path('<int:id>/stock/', self.admin_site.admin_view(self.stock_view), name='%s_%s_stock' % info),
            path('<int:id>/clone/', self.admin_site.admin_view(self.clone_form), name='%s_%s_clone' % info),
            path('stock/correction/', self.admin_site.admin_view(self.stock_correction_view), name='%s_%s_stock_correction' % info),
            path('import1c/', self.admin_site.admin_view(self.import_1c_view), name='%s_%s_import_1c' % info),
            path('import1c/status/', self.admin_site.admin_view(self.import_1c_status_view), name='%s_%s_import_1c_status' % info),
        ]
        return my_urls + urls

    def stock_view(self, request, id):
        product = permitted_object(self, request, id)
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
        check_permission(self, request)
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
        product = permitted_object(self, request, id)
        if not self.has_add_permission(request):
            raise PermissionDenied
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
        # the import changes the stock and prices of products
        check_permission(self, request, change=True)
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
        check_permission(self, request)
        return JsonResponse(ImportRun.status())


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

    @admin.display(description=_('link'))
    def link(self, obj):
        if obj.is_public:
            product = Product.objects.get(pk=obj.object_pk)
            prefix = SHOP_INFO.get('url_prefix', '')
            # the symbol is HTML from the settings
            return format_html('<a href="{}/products/{}.html#r{}">{}</a>', prefix, quote(product.code), obj.id,
                               mark_safe(REVIEW_ADMIN_LINK_SYMBOL))
        else:
            return ''


admin.site.register(ProductReview, ProductReviewAdmin)
