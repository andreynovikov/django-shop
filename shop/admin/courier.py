from django.contrib import admin
from django.utils.safestring import mark_safe

from shop.models import Courier


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
