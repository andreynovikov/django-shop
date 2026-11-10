import json

from django.contrib import admin
from django.template.defaultfilters import floatformat
from django.template.loader import render_to_string
from django.utils.html import format_html
from django.utils.text import Truncator
from django.utils.translation import gettext_lazy as _

from .models import Error, ErrorTrace


class ErrorTraceInline(admin.StackedInline):
    model = ErrorTrace
    extra = 0
    can_delete = False
    fields = ('message', 'context_display', 'frames_display', 'traceback_display')  # the time is in the title
    readonly_fields = fields

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    @admin.display(description=_('context'))
    def context_display(self, trace):
        return format_html('<pre style="margin: 0">{}</pre>', json.dumps(trace.context, ensure_ascii=False, indent=2))

    @admin.display(description=_('stack'))
    def frames_display(self, trace):
        return render_to_string('admin/errors/frames.html', {'frames': trace.frames})

    @admin.display(description=_('traceback'))
    def traceback_display(self, trace):
        return format_html(
            '<details><summary>{}</summary><pre style="margin: 0">{}</pre></details>', _('as text'), trace.traceback,
        )


@admin.register(Error)
class ErrorAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'short_message', 'source', 'location', 'count', 'frequency_display', 'severity', 'first_seen', 'last_seen',
    )
    list_editable = ('severity',)
    list_filter = ('severity', 'kind', 'last_seen')
    search_fields = ('name', 'message', 'source', 'location')
    date_hierarchy = 'last_seen'
    fields = (
        'name', 'message', 'kind', 'source', 'location', 'count', 'frequency_display', 'first_seen', 'last_seen', 'severity',
    )
    readonly_fields = fields[:-1]
    inlines = (ErrorTraceInline,)

    def has_add_permission(self, request):
        return False

    @admin.display(description=_('message'))
    def short_message(self, error):
        return Truncator(error.message).chars(100)

    @admin.display(description=_('frequency, per day'))
    def frequency_display(self, error):
        return floatformat(error.frequency, 1)
