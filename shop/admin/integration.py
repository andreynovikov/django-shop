from django.contrib import admin

from shop.models import Integration, SupplierIntegration
from .forms import IntegrationAdminForm


class SupplierInline(admin.TabularInline):
    model = SupplierIntegration
    fields = ['supplier', 'count_in_stock']
    ordering = ['supplier__order']
    extra = 0
    verbose_name = "учитываемый поставщик"
    verbose_name_plural = "учитываемые поставщики"


@admin.register(Integration)
class IntegrationAdmin(admin.ModelAdmin):
    form = IntegrationAdminForm
    list_display = ['name', 'utm_source', 'site', 'suppliers', 'uses_api']
    exclude = ['products']
    inlines = [SupplierInline]

    def suppliers(self, obj):
        suppliers = SupplierIntegration.objects.filter(integration=obj).order_by('supplier__order')
        if suppliers:
            return ', '.join([s.supplier.name for s in suppliers])
        else:
            return '-'
    suppliers.short_description = "поставщики"
