from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.urls import NoReverseMatch
from django.utils.html import conditional_escape, format_html, format_html_join

from .models import Category, Entry


@admin.register(Entry)
class EntryAdmin(admin.ModelAdmin):
    date_hierarchy = 'publication_date'
    fieldsets = (
        ('Контент', {
            'fields': (('title', 'status'), 'content')
        }),
        ('Иллюстрация', {
            'fields': ('image', 'image_caption'),
            'classes': ('collapse', 'collapse-closed')
        }),
        ('Публикация', {
            'fields': ('publication_date', 'sites'),
            'classes': ('collapse', 'collapse-closed')
        }),
        ('Метаданные', {
            'fields': ('featured', 'author', 'related'),
            'classes': ('collapse', 'collapse-closed')
        }),
        (None, {
            'fields': ('categories', 'tags', 'slug')
        })
    )
    list_filter = ('categories', 'publication_date', 'sites', 'status')
    list_display = ('title', 'get_categories', 'get_tags', 'get_sites', 'get_is_visible', 'featured',
                    'get_short_url', 'publication_date')
    filter_horizontal = ('categories', 'related')
    prepopulated_fields = {'slug': ('title',)}
    search_fields = ('title', 'content', 'tags')

    def get_categories(self, entry):
        return ', '.join([conditional_escape(category.title) for category in entry.categories.all()])
    get_categories.short_description = 'категории'

    def get_tags(self, entry):
        return conditional_escape(entry.tags)
    get_tags.short_description = 'тэги'

    def get_sites(self, entry):
        return ', '.join([conditional_escape(site.name) for site in entry.sites.all()])
    get_sites.short_description = 'сайты'

    def get_short_url(self, entry):
        try:
            short_url = entry.short_url
        except NoReverseMatch:
            short_url = entry.get_absolute_url()
        return format_html('<a href="{url}" target="blank">{url}</a>', url=short_url)
    get_short_url.short_description = 'короткий url'

    def get_is_visible(self, entry):
        return entry.is_visible
    get_is_visible.boolean = True
    get_is_visible.short_description = 'видимая'

    def get_changeform_initial_data(self, request):
        get_data = super(EntryAdmin, self).get_changeform_initial_data(request)
        return get_data or {
            'sites': [Site.objects.get_current().pk],
            'author': [request.user.pk]
        }

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'author':
            kwargs['queryset'] = get_user_model().objects.filter(is_staff=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug')
    prepopulated_fields = {'slug': ('title',)}
