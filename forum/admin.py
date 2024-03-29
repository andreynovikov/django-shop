from datetime import datetime

from django import forms
from django.db.models import F
from django.urls import reverse
from django.contrib import admin
from django.utils.safestring import mark_safe

from import_export import resources
from import_export.admin import ExportMixin

from shop.admin.decorators import admin_changelist_link

from . import models


@admin.register(models.Opinion)
class OpinionAdmin(admin.ModelAdmin):
    @mark_safe
    def author_link(self, obj):
        if obj.author.pk == '':
            return obj.author
        return "<a href={}>{}</a>".format(reverse('admin:{}_{}_change'.format(obj.author._meta.app_label, obj.author._meta.model_name), args=(obj.author.pk,)), obj.author)
    author_link.admin_order_field = 'author'
    author_link.short_description = 'author'

    list_display = ['id', 'tid', 'post', 'text', 'author_link', 'ip']
    list_display_links = ['id', 'tid']
    readonly_fields = ['tid', 'post', 'author', 'ip']
    search_fields = ['text', 'author__id', 'author__login', 'ip']

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(models.Thread)
class ThreadAdmin(admin.ModelAdmin):
    @mark_safe
    def owner_link(self, obj):
        if obj.owner.pk == '':
            return obj.owner
        return "<a href={}>{}</a>".format(reverse('admin:{}_{}_change'.format(obj.owner._meta.app_label, obj.owner._meta.model_name), args=(obj.owner.pk,)), obj.owner)
    owner_link.admin_order_field = 'owner'
    owner_link.short_description = 'owner'

    def discuss_count(self, obj):
        return models.Opinion.objects.filter(tid=obj.pk).count()
    discuss_count.short_description = 'len'

    @admin_changelist_link(None, 'ops', model=models.Opinion, query_string=lambda t: 'tid={}'.format(t.pk))
    def discuss_link(self, opinions):
        return '<i class="icon-list"></i>'

    list_display = ['id', 'topic', 'title', 'mtime', 'owner_link', 'ip', 'discuss_link', 'discuss_count']
    list_display_links = ['title']
    list_filter = ['topic', 'isopen', 'archived']
    readonly_fields = ['mtime', 'owner', 'ip']
    search_fields = ['title', 'owner__id', 'owner__login', 'ip']

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(models.Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ['title']
    list_display_links = ['title']

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(models.BassetUser)
class BassetUserAdmin(admin.ModelAdmin):
    list_display = ['id', 'login', 'fio', 'email', 'phone']
    list_display_links = ['id']
    search_fields = ['id', 'login', 'fio', 'email', 'phone']
    list_per_page = 100

    def has_add_permission(self, request, obj=None):
        return False


class TimestampWidget(forms.Widget):
    def __init__(self, original_value, display_value):
        self.original_value = original_value
        self.display_value = display_value
        super().__init__()

    def render(self, name, value, attrs=None):
        return str(datetime.fromtimestamp(self.original_value))

    def value_from_datadict(self, data, files, name):
        return self.original_value


class OrderItemInline(admin.TabularInline):
    model = models.OrderItem
    fields = ['pid', 'pq', 'pprice', 'pccode', 'ptax', 'pdiscount', 'pway', 'prate']
    readonly_fields = ['pid', 'pq', 'pprice', 'pccode', 'ptax', 'pdiscount', 'pway', 'prate']

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class OrderStatusListFilter(admin.SimpleListFilter):
    title = 'status'

    parameter_name = 'stat'

    def lookups(self, request, model_admin):
        """
        Returns a list of tuples. The first element in each
        tuple is the coded value for the option that will
        appear in the URL query. The second element is the
        human-readable name for the option that will appear
        in the right sidebar.
        """
        choices = [
            ('all', 'All'),
        ]
        statuses = list(models.OrderStatus.objects.all().values('id', 'name'))
        choices += map(lambda x: (x['id'], x['name']), statuses)
        return choices

    def choices(self, cl):
        for lookup, title in self.lookup_choices:
            yield {
                'selected': str(self.value()) == str(lookup),
                'query_string': cl.get_query_string({
                    self.parameter_name: lookup,
                }, []),
                'display': title[0].upper() + title[1:],
            }

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via
        `self.value()`.
        """
        if self.value() == 'all':
            return None
        if self.value():
            return queryset.filter(stat__gt=0).annotate(stats=F('stat').bitand(int(self.value()))).filter(stats__gt=0)
        return None


class OrderResource(resources.ModelResource):
    class Meta:
        model = models.Order
        import_id_fields = ['id']
        fields = ('id', 'otime', 'stat', 'uid__id', 'uid__fio', 'uid__email', 'uid__phone', 'uid__phoneaux')


@admin.register(models.Order)
class OrderAdmin(ExportMixin, admin.ModelAdmin):
    @mark_safe
    def user_link(self, obj):
        if obj.uid.pk == '':
            return obj.uid
        return "<a href={}>{}</a>".format(reverse('admin:{}_{}_change'.format(obj.uid._meta.app_label, obj.uid._meta.model_name), args=(obj.uid.pk,)), obj.uid)
    user_link.admin_order_field = 'uid'
    user_link.short_description = 'uid'

    def otime_datetime(self, obj):
        return datetime.fromtimestamp(obj.otime)
    otime_datetime.admin_order_field = 'otime'
    otime_datetime.short_description = 'otime'

    def status(self, obj):
        stats = list(filter(lambda x: (obj.stat & x), map(lambda x: 1 << x, range(0, 15))))
        if not stats:
            return '-'
        return ', '.join(list(models.OrderStatus.objects.filter(id__in=stats).values_list('name', flat=True)))
    status.admin_order_field = 'stat'
    status.short_description = 'stat'

    list_display = ['id', 'user_link', 'otime_datetime', 'status']
    list_display_links = ['id']
    list_filter = [OrderStatusListFilter]
    readonly_fields = ['uid']
    search_fields = ['=item__pid__code']
    inlines = [OrderItemInline]
    resource_class = OrderResource

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['otime'].widget = TimestampWidget(getattr(obj, 'otime', ''), '')
        return form

    def has_add_permission(self, request, obj=None):
        return False
