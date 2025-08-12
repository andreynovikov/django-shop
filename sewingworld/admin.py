from django.contrib import admin
from django.urls import path
from django.utils.translation import gettext_lazy as _

import djconfig
from two_factor.admin import AdminSiteOTPRequired

from .models import SiteProfile
from .forms import SWConfigForm


class SWAdminSite(AdminSiteOTPRequired):  # admin.AdminSite):
    site_header = "Швейный Мир"
    site_title = "Административный сайт Швейный Мир"

    def get_urls(self):
        import shop.admin.views  # prevent circular import
        urls = super().get_urls()
        urls = [
            path('goto_order/', self.admin_view(shop.admin.views.goto_order), name='goto_order')
        ] + urls
        return urls

    def get_app_list(self, request, app_label=None):
        apps = super().get_app_list(request, app_label)

        shop = next((index for (index, app) in enumerate(apps) if app['app_label'] == 'shop'), None)
        if shop is not None:
            apps.insert(0, apps.pop(shop))
            shop = 0

        sewingworld = next((index for (index, app) in enumerate(apps) if app['app_label'] == 'sewingworld'), None)
        if sewingworld is not None:
            index = 0 if shop is None else 1
            apps.insert(index, apps.pop(sewingworld))
            sewingworld = index

        auth = next((index for (index, app) in enumerate(apps) if app['app_label'] == 'auth'), None)
        flatpages = next((index for (index, app) in enumerate(apps) if app['app_label'] == 'flatpages'), None)
        sites = next((index for (index, app) in enumerate(apps) if app['app_label'] == 'sites'), None)
        phonenumber = next((index for (index, app) in enumerate(apps) if app['app_label'] == 'phonenumber'), None)
        otp_static = next((index for (index, app) in enumerate(apps) if app['app_label'] == 'otp_static'), None)
        otp_totp = next((index for (index, app) in enumerate(apps) if app['app_label'] == 'otp_totp'), None)

        indexes = []

        if phonenumber is not None:
            apps[phonenumber]['name'] = 'Two Factor Authentication'
            apps[phonenumber]['app_url'] = '/admin/'
            if otp_static is not None:
                apps[phonenumber]['models'].extend(apps[otp_static]['models'])
                indexes.append(otp_static)
            if otp_totp is not None:
                apps[phonenumber]['models'].extend(apps[otp_totp]['models'])
                indexes.append(otp_totp)

        if shop is not None and auth is not None:
            user = next((index for (index, model) in enumerate(apps[shop]['models']) if model['object_name'] == 'ShopUser'), None)
            if user is not None:
                apps[auth]['models'].append(apps[shop]['models'][user])

        if sewingworld is not None:
            if flatpages is not None:
                apps[sewingworld]['models'].extend(apps[flatpages]['models'])
                indexes.append(flatpages)
            if sites is not None:
                apps[sewingworld]['models'].extend(apps[sites]['models'])
                indexes.append(sites)

        for i in sorted(indexes, reverse=True):
            del(apps[i])
        return apps


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


class SiteProfileInline(admin.StackedInline):
    model = SiteProfile
    can_delete = False


def get_site_prefix(obj):
    return obj.profile.order_prefix
get_site_prefix.short_description = 'префикс'


def get_manager_phones(obj):
    return obj.profile.manager_phones
get_manager_phones.short_description = 'телефоны менеджеров'


def get_manager_emails(obj):
    return obj.profile.manager_emails
get_manager_emails.short_description = 'адреса менеджеров'


def get_sites(obj):
    'returns a list of site names for a FlatPage object'
    return ", ".join((site.name for site in obj.sites.all()))
get_sites.short_description = 'Sites'


def configure_admin():
    admin.site.enable_nav_sidebar = False

    djconfig.admin.register(SWConfig, SWConfigAdmin)

    from django.contrib.sites.admin import SiteAdmin
    from django.contrib.sites.models import Site
    SWSiteAdmin = type('SWSiteAdmin', (SiteAdmin,), {
        'list_display': ('domain', 'name', get_site_prefix, get_manager_phones, get_manager_emails),
        'inlines': (SiteProfileInline,)
    })
    admin.site.unregister(Site)
    admin.site.register(Site, SWSiteAdmin)

    """
    from tagging.admin import TagAdmin
    from tagging.models import Tag
    SWTagAdmin = type('SWTagAdmin', (TagAdmin,), {'search_fields': ['name'], 'ordering': ['name']})
    admin.site.unregister(Tag)
    admin.site.register(Tag, SWTagAdmin)
    """

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
        # form = SWFlatPageForm
    })
    admin.site.unregister(FlatPage)
    admin.site.register(FlatPage, SWFlatPageAdmin)
