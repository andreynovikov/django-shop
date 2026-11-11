from django.conf import settings
from django.contrib import admin

from adminsortable2.admin import SortableAdminMixin

from sewingworld.admin import get_sites
from shop.models import SalesAction
from .forms import SalesActionAdminForm

SHOP_INFO = getattr(settings, 'SHOP_INFO', {})


@admin.register(SalesAction)
class SalesActionAdmin(SortableAdminMixin, admin.ModelAdmin):
    list_display = ['name', 'slug', get_sites, 'active', 'show_in_list']
    list_display_links = ['name']
    search_fields = ['name', 'slug']
    form = SalesActionAdminForm

    def view_on_site(self, obj):
        prefix = SHOP_INFO.get('url_prefix', '')
        return f'{prefix}/actions/{obj.slug}/'
