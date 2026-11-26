from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.urls import NoReverseMatch
from django.utils.html import format_html

from filemanager.widgets import HTMLTextarea

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

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name == 'content':
            kwargs['widget'] = HTMLTextarea(attrs={'rows': 15, 'style': 'width: 95%; max-height: 500px'})
        return super().formfield_for_dbfield(db_field, request, **kwargs)

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('categories', 'sites', 'tags')

    # Plain text, which the admin escapes: escaped here, a joined list was escaped twice
    @admin.display(description='категории')
    def get_categories(self, entry):
        return ', '.join(category.title for category in entry.categories.all())

    @admin.display(description='тэги')
    def get_tags(self, entry):
        return str(entry.tags)  # tagulous gives the tag string

    @admin.display(description='сайты')
    def get_sites(self, entry):
        return ', '.join(site.name for site in entry.sites.all())

    @admin.display(description='короткий url')
    def get_short_url(self, entry):
        try:
            short_url = entry.short_url
        except NoReverseMatch:
            short_url = entry.get_absolute_url()
        return format_html('<a href="{url}" target="blank">{url}</a>', url=short_url)

    @admin.display(description='видимая', boolean=True)
    def get_is_visible(self, entry):
        return entry.is_visible

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
