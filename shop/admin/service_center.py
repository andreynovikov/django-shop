from django.contrib import admin

from more_admin_filters import RelatedDropdownFilter

from shop.models import ServiceCenter


@admin.register(ServiceCenter)
class ServiceCenterAdmin(admin.ModelAdmin):
    list_display = ['city', 'address', 'enabled', 'latitude', 'longitude']
    list_display_links = ['address']
    list_filter = [('city', RelatedDropdownFilter), 'enabled']
    search_fields = ['address', 'city__name']
    ordering = ['city', 'address']
