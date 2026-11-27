from django import forms
from django.contrib import admin
from django.contrib.admin.views.autocomplete import AutocompleteJsonView
from django.db import models
from django.urls import path
from django.utils.translation import gettext_lazy as _

from two_factor.admin import AdminSiteOTPRequired
from mptt.forms import TreeNodeChoiceField

from filemanager.widgets import HTMLTextarea

from shop.models import Category
from . import admin_events
from .models import SiteProfile


class SWAutocompleteJsonView(AutocompleteJsonView):
    """
    Search results of the autocomplete fields. The model admin's autocomplete_labels(), when it has one, gives their
    labels by ID: categories show their paths, which tell those of the same name apart. Others show str().
    """
    def serialize_result(self, obj, to_field_name):
        result = super().serialize_result(obj, to_field_name)
        get_labels = getattr(self.model_admin, 'autocomplete_labels', None)
        if get_labels is not None:
            if not hasattr(self, 'labels'):
                self.labels = get_labels()  # once for the page of results
            result['text'] = self.labels.get(obj.pk, result['text'])
        return result


class SWAdminSite(AdminSiteOTPRequired):  # admin.AdminSite):
    site_header = "Швейный Мир"
    site_title = "Административный сайт Швейный Мир"
    # Tabs of the index page (templates/admin/index.html) with the app labels they list, in this order. The last one,
    # without labels, takes the apps the others leave, in get_app_list() order. The shop, with most models, spans its
    # tab, and the tab's other apps go beside it.
    index_tabs = (
        ('shop', 'Магазин', ('shop', 'sewingworld', 'django_comments', 'blog')),
        ('access', 'Доступ', ('auth', 'phonenumber', 'otp_static', 'otp_totp', 'authtoken')),
        ('system', 'Служебное', None),
    )

    def autocomplete_view(self, request):
        return SWAutocompleteJsonView.as_view(admin_site=self)(request)

    def get_urls(self):
        import shop.admin.views  # prevent circular import
        urls = super().get_urls()
        urls = [
            path('goto_order/', self.admin_view(shop.admin.views.goto_order), name='goto_order'),
            # async, it checks the user itself, see sewingworld/admin_events.py
            path('events/', admin_events.events, name='events'),
        ] + urls
        return urls

    def index(self, request, extra_context=None):
        response = super().index(request, extra_context)
        app_list = response.context_data['app_list']
        placed = {label for _, _, labels in self.index_tabs if labels for label in labels}
        tabs = []
        for tab_id, name, labels in self.index_tabs:
            if labels:
                apps = sorted((app for app in app_list if app['app_label'] in labels),
                              key=lambda app: labels.index(app['app_label']))
            else:
                apps = [app for app in app_list if app['app_label'] not in placed]
            if not apps:
                continue
            tab = {'id': tab_id, 'name': name, 'apps': apps}
            if apps[0]['app_label'] == 'shop' and len(apps) > 1:
                tab['main'], tab['side'] = apps[:1], apps[1:]
            tabs.append(tab)
        response.context_data['tabs'] = tabs
        return response

    def get_app_list(self, request, app_label=None):
        # The shop goes first, with the flat pages and the file manager, then a "Швейный Мир" group with the constance
        # settings and sites. The integrations' health is a "Мониторинг" group after the server errors. The OTP models
        # join "Two Factor Authentication", and the shop's users are listed under auth too. Comments are named in
        # Russian.
        apps = super().get_app_list(request, app_label)

        shop = next((index for (index, app) in enumerate(apps) if app['app_label'] == 'shop'), None)
        if shop is not None:
            apps.insert(0, apps.pop(shop))
            shop = 0

        sewingworld = {
            'name': 'Швейный Мир',
            'app_label': 'sewingworld',
            'models': []
        }
        index = 0 if shop is None else 1
        apps.insert(index, sewingworld)
        sewingworld = index

        auth = next((index for (index, app) in enumerate(apps) if app['app_label'] == 'auth'), None)
        constance = next((index for (index, app) in enumerate(apps) if app['app_label'] == 'constance'), None)
        flatpages = next((index for (index, app) in enumerate(apps) if app['app_label'] == 'flatpages'), None)
        filemanager = next((index for (index, app) in enumerate(apps) if app['app_label'] == 'filemanager'), None)
        sites = next((index for (index, app) in enumerate(apps) if app['app_label'] == 'sites'), None)
        phonenumber = next((index for (index, app) in enumerate(apps) if app['app_label'] == 'phonenumber'), None)
        otp_static = next((index for (index, app) in enumerate(apps) if app['app_label'] == 'otp_static'), None)
        otp_totp = next((index for (index, app) in enumerate(apps) if app['app_label'] == 'otp_totp'), None)
        comments = next((index for (index, app) in enumerate(apps) if app['app_label'] == 'django_comments'), None)

        indexes = []

        if comments is not None:
            apps[comments]['name'] = 'Комментарии'

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

        if shop is not None:
            for other in (flatpages, filemanager):
                if other is not None:
                    apps[shop]['models'].extend(apps[other]['models'])
                    indexes.append(other)
            apps[shop]['models'].sort(key=lambda model: model['name'])  # as Django sorts them

        # The integrations' health goes to a group of its own, placed below, which the index puts in the "system" tab
        checks = []
        if shop is not None and app_label is None:
            checks = [model for model in apps[shop]['models'] if model['object_name'] == 'IntegrationCheck']
            apps[shop]['models'] = [model for model in apps[shop]['models'] if model['object_name'] != 'IntegrationCheck']

        if sewingworld is not None:
            if constance is not None:
                apps[sewingworld]['models'].extend(apps[constance]['models'])
                indexes.append(constance)
            if sites is not None:
                apps[sewingworld]['models'].extend(apps[sites]['models'])
                indexes.append(sites)

        for i in sorted(indexes, reverse=True):
            del apps[i]

        if checks:
            # Right after the server errors, or last
            errors = next((index for (index, app) in enumerate(apps) if app['app_label'] == 'errors'), len(apps) - 1)
            apps.insert(errors + 1, {'name': 'Мониторинг', 'app_label': 'monitoring', 'models': checks})
        return [app for app in apps if app['models']]  # "Швейный Мир" is empty for staff without its models


"""
class SWFlatPageForm(ModelForm):
    class Meta:
        widgets = {
            #'content': AutosizedTextarea(attrs={'rows': 5, 'style': 'width: 95%; max-height: 500px'}),
        }
"""


class ProductAdminForm(forms.ModelForm):
    root_category = TreeNodeChoiceField(
        label='Корневая категория',
        queryset=Category.objects.root_nodes(),
        required=False
    )

    class Meta:
        model = SiteProfile
        fields = '__all__'


class SiteProfileInline(admin.StackedInline):
    model = SiteProfile
    form = ProductAdminForm
    can_delete = False


@admin.display(description='Sites')
def get_sites(obj):
    'returns a list of site names for a FlatPage object, an advert or a sales action'
    return ", ".join(site.name for site in obj.sites.all())


def configure_admin():
    admin.site.enable_nav_sidebar = False

    # Imported here, when the apps are ready: at the top they would register their admins while the site is made
    from django.contrib.sites.admin import SiteAdmin
    from django.contrib.sites.models import Site

    class SWSiteAdmin(SiteAdmin):
        list_display = ('domain', 'name', 'get_site_prefix', 'get_manager_phones', 'get_manager_emails')
        inlines = (SiteProfileInline,)
        list_select_related = ['profile']

        @admin.display(description='префикс')
        def get_site_prefix(self, obj):
            return obj.profile.order_prefix

        @admin.display(description='телефоны менеджеров')
        def get_manager_phones(self, obj):
            return obj.profile.manager_phones

        @admin.display(description='адреса менеджеров')
        def get_manager_emails(self, obj):
            return obj.profile.manager_emails

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
        formfield_overrides = {  # content is its only text field
            models.TextField: {'widget': HTMLTextarea(attrs={'rows': 15, 'style': 'width: 95%; max-height: 500px'})},
        }

        def get_queryset(self, request):
            return super().get_queryset(request).prefetch_related('sites')

    admin.site.unregister(FlatPage)
    admin.site.register(FlatPage, SWFlatPageAdmin)

    from rest_framework.authtoken.admin import TokenAdmin
    TokenAdmin.raw_id_fields = ['user']
