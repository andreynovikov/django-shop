from django.forms import ModelForm
from django.db.models import ImageField
from django.conf import settings
from django.contrib import admin
from django.core.exceptions import PermissionDenied
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.safestring import mark_safe

from adminsortable2.admin import SortableAdminBase, SortableAdminMixin, SortableInlineAdminMixin
from django_admin_listfilter_dropdown.filters import RelatedDropdownFilter
from mptt.admin import DraggableMPTTAdmin

from sewingworld.admin import get_sites
from sewingworld.widgets import AutosizedTextarea
from shop.models import Category, Supplier, Contractor, PosTerminal, Currency, \
    Country, Region, City, Store, StoreImage, ServiceCenter, Manufacturer, \
    Advert, SalesAction, Manager, Courier, News
from .widgets import ImageWidget
from .forms import CategoryAdminForm, PosTerminalAdminForm, NewsAdminForm

from .product import ProductAdmin  # NOQA
from .order import OrderAdmin  # NOQA
from .act import ActAdmin  # NOQA
from .integration import IntegrationAdmin  # NOQA
from .serial import SerialAdmin  # NOQA
from .user import ShopUserAdmin  # NOQA

SHOP_INFO = getattr(settings, 'SHOP_INFO', {})


@admin.register(Category)
class CategoryAdmin(DraggableMPTTAdmin):
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    list_display = ('tree_actions', 'indented_title', 'slug', 'active', 'hidden', 'feed')
    # list_editable = ['active']
    list_display_links = ['indented_title']
    exclude = ('image_width', 'image_height', 'promo_image_width', 'promo_image_height')
    form = CategoryAdminForm


@admin.register(Supplier)
class SupplierAdmin(SortableAdminMixin, admin.ModelAdmin):
    list_display = ['code', 'name', 'show_in_order', 'show_in_list', 'count_in_stock', 'express_count_in_stock']
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
class StoreAdmin(SortableAdminBase, admin.ModelAdmin):
    list_display = ['city', 'address', 'name', 'supplier', 'enabled', 'latitude', 'longitude']
    list_display_links = ['address', 'name']
    list_filter = [('city', RelatedDropdownFilter), 'enabled', 'publish', 'marketplace', 'lottery']
    search_fields = ['name', 'address', 'address2', 'city__name']
    ordering = ['city', 'address']
    inlines = [StoreImageInline]

    def view_on_site(self, obj):
        prefix = SHOP_INFO.get('url_prefix','')
        return f'{prefix}/stores/{obj.id}/'

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('yandexmapfeed/', self.admin_site.admin_view(self.yandex_map_feed_view), name='%s_%s_yandexmapfeed' % (self.model._meta.app_label, self.model._meta.model_name))
        ]
        return my_urls + urls

    def yandex_map_feed_view(self, request):
        if not request.user.is_staff:
            raise PermissionDenied
        stores = Store.objects.filter(enabled=True, publish=True)
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
    list_display = ['code', 'name', 'inn', 'is_seller', 'tax_system', 'yookassa_id', 'modulkassa_login']
    list_display_links = ['name']
    search_fields = ['name']
    ordering = ['code']


@admin.register(PosTerminal)
class PosTerminalAdmin(admin.ModelAdmin):
    list_display = ['id', 'seller']
    ordering = ['id']
    form = PosTerminalAdminForm


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

    def view_on_site(self, obj):
        prefix = SHOP_INFO.get('url_prefix','')
        return f'{prefix}/actions/{obj.slug}/'


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

    list_display = ['name', 'colorbar', 'pos_terminal']
    list_display_links = ['name']
    search_fields = ['name']
    ordering = ['name']


@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ['title', 'publish_date', 'active']
    list_display_links = ['title']
    search_fields = ['title']
    list_filter = ['active']
    exclude = ('image_width', 'image_height')
    form = NewsAdminForm
