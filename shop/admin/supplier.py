from django.contrib import admin

from adminsortable2.admin import SortableAdminMixin

from shop.models import Supplier


@admin.register(Supplier)
class SupplierAdmin(SortableAdminMixin, admin.ModelAdmin):
    list_display = ['code', 'name', 'show_in_order', 'show_in_list', 'count_in_stock', 'express_count_in_stock']
    list_display_links = ['name']
    search_fields = ['code', 'code1c', 'name']
