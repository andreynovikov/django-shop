from django.contrib import admin
from django.contrib.flatpages.admin import FlatPageAdmin
from django.contrib.flatpages.models import FlatPage
from django.utils.translation import ugettext_lazy as _


def get_sites(obj):
    'returns a list of site names for a FlatPage object'
    return ", ".join((site.name for site in obj.sites.all()))
get_sites.short_description = 'Sites'

# Define a new FlatPageAdmin
class SWFlatPageAdmin(FlatPageAdmin):
    list_display = ('url', 'title', get_sites)
    fieldsets = (
        (None, {'fields': ('url', 'title', 'content', 'sites')}),
        (_('Advanced options'), {
            'classes': ('collapse', ),
            'fields': (
                'enable_comments',
                'registration_required',
                'template_name',
            ),
        }),
    )

# Re-register FlatPageAdmin
admin.site.unregister(FlatPage)
admin.site.register(FlatPage, SWFlatPageAdmin)
