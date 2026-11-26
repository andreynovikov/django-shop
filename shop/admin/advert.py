from django.contrib import admin

from adminsortable2.admin import SortableAdminMixin
from sewingworld.admin import get_sites
from shop.models import Advert
from .forms import AdvertAdminForm
from .product import CategoryDropdownFilter


@admin.register(Advert)
class AdvertAdmin(SortableAdminMixin, admin.ModelAdmin):
    list_display = ['name', 'place', get_sites, 'active']
    list_display_links = ['name']
    search_fields = ['name']
    list_filter = ['active', 'place', ('categories', CategoryDropdownFilter)]
    form = AdvertAdminForm
    filter_vertical = ('categories',)

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('sites')  # for get_sites
