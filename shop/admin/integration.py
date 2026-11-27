from django.contrib import admin
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.urls import path
from django.utils import timezone
from django.utils.html import format_html
from django.utils.text import Truncator

from more_admin_filters import DropdownFilter, RelatedDropdownFilter

from shop import health
from shop.health import COLORS, GROUPS, LEVELS, OK, PROBLEM, WARNING
from shop.models import HealthCheck, Integration
from .forms import IntegrationAdminForm

LEVEL_NAMES = {OK: 'в порядке', WARNING: 'сбой', PROBLEM: 'проблема'}


@admin.register(Integration)
class IntegrationAdmin(admin.ModelAdmin):
    form = IntegrationAdminForm
    list_display = ['name', 'enabled', 'uses_api', 'utm_source', 'source_site', 'target_site', 'output_template', 'seller', 'supplier_list']
    list_filter = [('source_site', RelatedDropdownFilter), ('target_site', RelatedDropdownFilter), ('output_template', DropdownFilter), ('seller', RelatedDropdownFilter), 'enabled']
    list_select_related = ('source_site', 'target_site', 'seller')
    exclude = ['products']
    filter_horizontal = ('suppliers',)

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('suppliers')

    @admin.display(description='поставщики')
    def supplier_list(self, obj):
        # none shows as the admin's '-'
        return ', '.join(supplier.name for supplier in obj.suppliers.all())


class LevelFilter(admin.SimpleListFilter):
    title = 'состояние'
    parameter_name = 'level'

    def lookups(self, request, model_admin):
        return [(level, LEVEL_NAMES[level]) for level in reversed(LEVELS)]

    def queryset(self, request, queryset):
        # A stale check is a problem without a mark in the database, see health.stale_since()
        if self.value() in LEVELS:
            now = timezone.now()
            return queryset.filter(pk__in=[check.pk for check in queryset if health.level(check, now) == self.value()])
        return queryset


class GroupFilter(admin.SimpleListFilter):
    """ The indicators of the top bar, each of which links to its group """
    title = 'группа'
    parameter_name = 'group'

    def lookups(self, request, model_admin):
        return list(GROUPS.items())

    def queryset(self, request, queryset):
        if self.value() in GROUPS:
            return queryset.filter(operation__in=health.operations(self.value()))
        return queryset


@admin.register(HealthCheck)
class HealthCheckAdmin(admin.ModelAdmin):
    """
    The health of the integrations and of Celery, kept by shop/health.py: read only. "Reset" clears a check, such as
    one of an operation that no longer runs.
    """
    list_display = ['integration', 'operation_label', 'level_display', 'failures', 'first_failed_at', 'last_success_at', 'short_error']
    list_filter = [GroupFilter, LevelFilter, ('integration', RelatedDropdownFilter)]
    list_select_related = ['integration']
    fields = ['integration', 'operation_label', 'level_display', 'failures', 'first_failed_at', 'last_failed_at',
              'last_success_at', 'raised_at', 'created_at', 'full_error']
    readonly_fields = fields
    actions = ['reset']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def get_urls(self):
        info = self.opts.app_label, self.opts.model_name
        return [
            path('status/', self.admin_site.admin_view(self.status_view), name='%s_%s_status' % info),
        ] + super().get_urls()

    def status_view(self, request):
        """ The levels of the top bar's indicators, which poll it, by group """
        if not self.has_view_permission(request):
            raise PermissionDenied
        return JsonResponse({group: health.summary(group) for group in GROUPS})

    @admin.display(description='операция', ordering='operation')
    def operation_label(self, obj):
        return health.label(obj.operation)

    @admin.display(description='состояние')
    def level_display(self, obj):
        level = health.level(obj, timezone.now())
        return format_html('<span style="color: {}">&#9670;</span> {}', COLORS[level], LEVEL_NAMES[level])

    @admin.display(description='ошибка')
    def short_error(self, obj):
        lines = health.status_text(obj, timezone.now()).splitlines()
        return Truncator(lines[0]).chars(120) if lines else ''

    @admin.display(description='ошибка')
    def full_error(self, obj):
        return format_html('<pre style="white-space: pre-wrap; margin: 0">{}</pre>', health.status_text(obj, timezone.now()))

    @admin.action(description='Сбросить', permissions=['delete'])
    def reset(self, request, queryset):
        num = queryset.update(failures=0, error='', first_failed_at=None, raised_at=None, last_success_at=timezone.now())
        self.message_user(request, f'Сброшено: {num}')
