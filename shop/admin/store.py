from django.db.models import ImageField
from django.conf import settings
from django.contrib import admin
from django.core.exceptions import PermissionDenied
from django.template.response import TemplateResponse
from django.urls import path

from adminsortable2.admin import SortableAdminBase, SortableInlineAdminMixin
from more_admin_filters import RelatedDropdownFilter

from shop.models import Store, StoreImage
from .widgets import ImageWidget
from .forms import StoreAdminForm

SHOP_INFO = getattr(settings, 'SHOP_INFO', {})


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
    list_display = ['city', 'address', 'name', 'site', 'supplier', 'enabled', 'latitude', 'longitude']
    list_display_links = ['address', 'name']
    list_filter = [('city', RelatedDropdownFilter), ('site', RelatedDropdownFilter), 'enabled', 'publish', 'marketplace', 'lottery']
    search_fields = ['name', 'address', 'address2', 'city__name', 'site__domain']
    ordering = ['city', 'address']
    form = StoreAdminForm
    inlines = [StoreImageInline]

    def view_on_site(self, obj):
        prefix = SHOP_INFO.get('url_prefix', '')
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
