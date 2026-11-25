from django.contrib import admin

from more_admin_filters import RelatedDropdownFilter

from shop.models import Integration
from .forms import IntegrationAdminForm, integration_label


@admin.register(Integration)
class IntegrationAdmin(admin.ModelAdmin):
    form = IntegrationAdminForm
    list_display = ['display_name', 'enabled', 'uses_api', 'utm_source', 'source_site', 'target_site', 'output_template', 'seller', 'supplier_list']
    list_filter = ['source_site', 'target_site', 'output_template', ('seller', RelatedDropdownFilter), 'enabled']
    list_select_related = ('source_site', 'target_site', 'seller')
    exclude = ['products']
    filter_horizontal = ('suppliers',)

    @admin.display(description='название', ordering='name')
    def display_name(self, obj):
        return integration_label(obj)

    def supplier_list(self, obj):
        if obj.suppliers.all().count():
            return ', '.join([s.name for s in obj.suppliers.all()])
        else:
            return '-'
    supplier_list.short_description = "поставщики"
