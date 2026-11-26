from django.contrib import admin
from django.utils.html import format_html

from shop.models import Courier


@admin.register(Courier)
class CourierAdmin(admin.ModelAdmin):
    @admin.display(description='цвет', ordering='color')
    def colorbar(self, obj):
        return format_html('<div style="width: 40px; background-color: {}">&nbsp;</div>', obj.color)

    list_display = ['name', 'colorbar', 'pos_terminal']
    list_display_links = ['name']
    search_fields = ['name']
    ordering = ['name']
