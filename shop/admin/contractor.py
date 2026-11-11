from django.contrib import admin

from shop.models import Contractor, PosTerminal
from .forms import PosTerminalAdminForm


@admin.register(Contractor)
class ContractorAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'inn', 'is_seller', 'tax_system', 'yookassa_id', 'modulkassa_login']
    list_display_links = ['name']
    search_fields = ['name']
    ordering = ['code']


@admin.register(PosTerminal)
class PosTerminalAdmin(admin.ModelAdmin):
    list_display = ['id', 'seller']
    ordering = ['id']
    form = PosTerminalAdminForm
