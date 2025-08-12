from django.contrib import admin
from django.core.exceptions import PermissionDenied
from django.conf import settings
from django.template.response import TemplateResponse
from django.urls import re_path

from djconfig import config, reload_maybe

from shop.models import Act, ActOrder
from .forms import ActOrderInlineAdminForm


class ActOrderInline(admin.TabularInline):
    model = ActOrder
    form = ActOrderInlineAdminForm
    fk_name = 'act'
    ordering = ('order__pk',)
    autocomplete_fields = ('order',)
    extra = 0
    verbose_name = "заказ"
    verbose_name_plural = "заказы"


@admin.register(Act)
class ActAdmin(admin.ModelAdmin):
    def title(self, obj):
        return str(obj)
    title.admin_order_field = 'id'
    title.short_description = '№'

    list_display = ('title',)
    search_fields = ('id',)
    ordering = ('-id',)
    inlines = (ActOrderInline,)
    date_hierarchy = 'created'

    def has_add_permission(self, request, obj=None):
        return False

    def get_urls(self):
        urls = super(ActAdmin, self).get_urls()
        my_urls = [
            re_path(r'(\d+)/print/$', self.admin_site.admin_view(self.print_document), name='shop_act_print'),
        ]
        return my_urls + urls

    def print_document(self, request, id):
        if not request.user.is_staff:
            raise PermissionDenied

        reload_maybe()

        context = self.admin_site.each_context(request)
        context['opts'] = self.model._meta
        context['is_popup'] = request.GET.get('_popup', 0)
        context['act'] = Act.objects.get(pk=id)
        context['owner_info'] = getattr(settings, 'SHOP_OWNER_INFO', {})
        context['beru_delivery'] = config.sw_beru_delivery


        return TemplateResponse(request, 'shop/act/document.html', context)
