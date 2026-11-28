from django.contrib import admin
from django.conf import settings
from django.template.response import TemplateResponse
from django.urls import path

from constance import config

from shop.models import Act, ActOrder
from .forms import ActOrderInlineAdminForm
from .views import permitted_object


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
    @admin.display(description='№', ordering='id')
    def title(self, obj):
        return str(obj)

    list_display = ('title',)
    search_fields = ('id',)
    ordering = ('-id',)
    inlines = (ActOrderInline,)
    date_hierarchy = 'created'

    # Acts are made from the order list, by its action
    def has_add_permission(self, request, obj=None):
        return False

    def get_urls(self):
        urls = super(ActAdmin, self).get_urls()
        my_urls = [
            path('<int:id>/print/', self.admin_site.admin_view(self.print_document), name='shop_act_print'),
        ]
        return my_urls + urls

    def print_document(self, request, id):
        act = permitted_object(self, request, id)
        context = self.admin_site.each_context(request)
        context['opts'] = self.model._meta
        context['is_popup'] = request.GET.get('_popup', 0)
        context['act'] = act
        context['owner_info'] = getattr(settings, 'SHOP_OWNER_INFO', {})
        context['ym_delivery'] = config.sw_ym_delivery

        return TemplateResponse(request, 'shop/act/document.html', context)
