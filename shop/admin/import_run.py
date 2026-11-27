from django.contrib import admin
from django.utils.html import format_html

from shop.models import ImportRun


@admin.register(ImportRun)
class ImportRunAdmin(admin.ModelAdmin):
    """ The runs of the 1C import, read only, see ImportRun """
    list_display = ['started_at', 'stage_display', 'finished_at', 'file_date', 'imported', 'updated', 'errors', 'short_error']
    list_filter = ['stage']
    date_hierarchy = 'started_at'
    fields = ['file', 'file_date', 'stage_display', 'started_at', 'finished_at', 'imported', 'updated', 'errors', 'full_error']
    readonly_fields = fields

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    @admin.display(description='этап', ordering='stage')
    def stage_display(self, obj):
        return format_html('<span style="color: {}">&#9670;</span> {}', ImportRun.COLORS[obj.stage], obj.get_stage_display())

    @admin.display(description='ошибка')
    def short_error(self, obj):
        lines = obj.error.splitlines()
        return lines[0][:120] if lines else ''

    @admin.display(description='ошибка')
    def full_error(self, obj):
        return format_html('<pre style="white-space: pre-wrap; margin: 0">{}</pre>', obj.error)
