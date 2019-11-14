from django.contrib import admin
from django.urls import path
from django.utils.translation import ugettext_lazy as _

import djconfig

from .forms import SWConfigForm


class SWAdminSite(admin.AdminSite):
    site_header = "Швейный Мир"
    site_title = "Административный сайт Швейный Мир"

    def get_urls(self):
        import shop.admin.views  # prevent circular import
        urls = super().get_urls()
        urls = [
            path('goto_order/', self.admin_view(shop.admin.views.goto_order), name='goto_order'),
            path('import1c/', shop.admin.views.import_1c, name='import_1c')
        ] + urls
        return urls


class SWConfigAdmin(djconfig.admin.ConfigAdmin):
    change_list_form = SWConfigForm

    def has_add_permission(self, request, obj=None):
        return False


class SWConfig(djconfig.admin.Config):
    app_label = 'sewingworld'
    verbose_name_plural = 'Настройки'
    name = 'swconfig'


"""
class SWFlatPageForm(ModelForm):
    class Meta:
        widgets = {
            #'content': AutosizedTextarea(attrs={'rows': 5, 'style': 'width: 95%; max-height: 500px'}),
        }
"""


def get_sites(obj):
    'returns a list of site names for a FlatPage object'
    return ", ".join((site.name for site in obj.sites.all()))
get_sites.short_description = 'Sites'


def configure_admin():
    djconfig.admin.register(SWConfig, SWConfigAdmin)

    from tagging.admin import TagAdmin
    from tagging.models import Tag
    SWTagAdmin = type('SWTagAdmin', (TagAdmin,), {'search_fields': ['name'], 'ordering': ['name']})
    admin.site.unregister(Tag)
    admin.site.register(Tag, SWTagAdmin)

    from lock_tokens.admin import LockTokenAdmin
    from lock_tokens.models import LockToken
    admin.site.register(LockToken, LockTokenAdmin)

    from django.contrib.flatpages.admin import FlatPageAdmin
    from django.contrib.flatpages.models import FlatPage
    SWFlatPageAdmin = type('SWFlatPageAdmin', (FlatPageAdmin,), {
        'list_display': ('url', 'title', get_sites),
        'fieldsets': (
            (None, {'fields': ('url', 'title', 'content', 'sites')}),
            (_('Advanced options'), {
                'classes': ('collapse', ),
                'fields': (
                    'enable_comments',
                    'registration_required',
                    'template_name',
                ),
            }),
        ),
        #form = SWFlatPageForm
    })
    admin.site.unregister(FlatPage)
    admin.site.register(FlatPage, SWFlatPageAdmin)
