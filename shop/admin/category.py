from django.contrib import admin

from mptt.admin import DraggableMPTTAdmin

from shop.models import Category
from .forms import CategoryAdminForm


@admin.register(Category)
class CategoryAdmin(DraggableMPTTAdmin):
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    list_display = ('tree_actions', 'indented_title', 'slug', 'active', 'hidden', 'feed')
    # list_editable = ['active']
    list_display_links = ['indented_title']
    exclude = ('image_width', 'image_height', 'promo_image_width', 'promo_image_height')
    form = CategoryAdminForm
