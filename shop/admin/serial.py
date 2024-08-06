from django.contrib import admin

from daterangefilter.filters import PastDateRangeFilter

from shop.models import Serial


@admin.register(Serial)
class SerialAdmin(admin.ModelAdmin):
    list_display = ['number', 'product', 'order', 'purchase_date', 'approved']
    autocomplete_fields = ('product', 'order')
    readonly_fields = ['user']
    search_fields = ['number', 'comment']
    list_filter = [('purchase_date', PastDateRangeFilter), 'approved']
