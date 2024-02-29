from django.contrib import admin

from shop.models import Integration
from .forms import IntegrationAdminForm


@admin.register(Integration)
class IntegrationAdmin(admin.ModelAdmin):
    form = IntegrationAdminForm
    list_display = ['name', 'uses_api', 'utm_source', 'site', 'output_template', 'seller', 'supplier_list']
    exclude = ['products']
    filter_horizontal = ('suppliers',)

    def supplier_list(self, obj):
        if obj.suppliers.all().count():
            return ', '.join([s.name for s in obj.suppliers.all()])
        else:
            return '-'
    supplier_list.short_description = "поставщики"
