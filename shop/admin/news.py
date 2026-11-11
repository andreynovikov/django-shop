from django.contrib import admin

from shop.models import News
from .forms import NewsAdminForm


@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ['title', 'publish_date', 'active']
    list_display_links = ['title']
    search_fields = ['title']
    list_filter = ['active']
    exclude = ('image_width', 'image_height')
    form = NewsAdminForm
