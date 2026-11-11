from django.contrib import admin

from adminsortable2.admin import SortableAdminMixin
from more_admin_filters import RelatedDropdownFilter

from sewingworld.admin import get_sites
from shop.models import Advert
from .forms import AdvertAdminForm


@admin.register(Advert)
class AdvertAdmin(SortableAdminMixin, admin.ModelAdmin):
    list_display = ['name', 'place', get_sites, 'active']
    list_display_links = ['name']
    search_fields = ['name']
    list_filter = ['active', 'place', ('categories', RelatedDropdownFilter)]
    form = AdvertAdminForm
    filter_vertical = ('categories',)
