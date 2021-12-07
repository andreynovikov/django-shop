import re
import datetime
from collections import defaultdict
from decimal import Decimal, ROUND_UP

from django import forms
from django.urls import reverse
from django.db import connection
from django.db.models import TextField, PositiveSmallIntegerField, PositiveIntegerField, \
    DateTimeField, DecimalField, Q
from django.core.exceptions import PermissionDenied
from django.contrib import admin, messages
from django.http import HttpResponse, HttpResponseRedirect
from django.template.loader import get_template
from django.template.defaultfilters import floatformat
from django.template.response import TemplateResponse
from django.conf import settings
from django.conf.urls import url
from django.shortcuts import render
from django.utils import timezone
from django.utils.formats import date_format, number_format
from django.utils.http import urlquote
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from daterangefilter.filters import FutureDateRangeFilter, PastDateRangeFilter
from django_admin_listfilter_dropdown.filters import ChoiceDropdownFilter
from tagging.utils import parse_tag_input

from yandex_delivery.tasks import create_delivery_draft_order, get_delivery_options

from shop.models import ShopUserManager, ShopUser, Supplier, Order, OrderItem, Box, \
    Act, ActOrder
from shop.tasks import send_message

from .forms import WarrantyCardPrintForm, OrderAdminForm, OrderCombineForm, \
    OrderDiscountForm, SendSmsForm, SelectTagForm, SelectSupplierForm, \
    OrderItemInlineAdminForm, BoxInlineAdminForm, YandexDeliveryForm
from .views import product_stock_view


class OrderItemInline(admin.TabularInline):
    @mark_safe
    def product_codes(self, obj):
        code = obj.product.code or '--'
        article = obj.product.article or '--'
        partnumber = obj.product.partnumber or '--'
        code = '<a href="{}">{}</a>'.format(reverse('admin:shop_product_change', args=[obj.product.id]), code)
        return '<br/>'.join([code, article, partnumber])
    product_codes.admin_order_field = 'product__code'
    product_codes.short_description = 'Ид/1С/PN'

    def product_stock(self, obj):
        return product_stock_view(obj.product, obj.order)
    product_stock.short_description = 'склад'

    def item_cost(self, obj):
        return obj.cost
    item_cost.short_description = 'стоимость'

    model = OrderItem
    form = OrderItemInlineAdminForm
    extra = 0
    autocomplete_fields = ('product',)
    readonly_fields = ['product_codes', 'product_stock', 'item_cost']

    def get_fields(self, request, obj=None):
        fields = ['product_codes', 'product']
        if obj and (obj.is_beru or obj.is_sber):
            fields.extend(['val_discount', 'quantity', 'total', 'product_stock'])
        else:
            fields.extend(['product_price', 'pct_discount', 'val_discount', 'item_cost', 'quantity', 'total', 'product_stock'])
        if obj and (obj.is_beru or obj.is_sber or obj.delivery == Order.DELIVERY_YANDEX):
            fields.append('box')
        return fields

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = [elem for elem in self.readonly_fields]
        if obj and (obj.is_beru or obj.is_sber):
            readonly_fields += ['val_discount', 'quantity']
        return readonly_fields

    def has_add_permission(self, request, obj=None):
        return not obj or (not obj.is_beru and not obj.is_sber)

    def has_delete_permission(self, request, obj=None):
        return obj and not obj.is_beru and not obj.is_sber


class BoxInline(admin.TabularInline):
    def title(self, obj):
        if obj.pk:
            return "{:010d}".format(obj.pk)
        else:
            return '-'
    title.admin_order_field = 'id'
    title.short_description = '№'

    model = Box
    form = BoxInlineAdminForm
    extra = 0
    fields = ['title', 'weight', 'length', 'width', 'height']
    readonly_fields = ['title']
    ordering = ['id']


class OrderStatusListFilter(admin.SimpleListFilter):
    title = _('статус')
    template = 'django_admin_listfilter_dropdown/dropdown_filter.html'

    parameter_name = 'status'

    def lookups(self, request, model_admin):
        """
        Returns a list of tuples. The first element in each
        tuple is the coded value for the option that will
        appear in the URL query. The second element is the
        human-readable name for the option that will appear
        in the right sidebar.
        """
        choices = (
            ('all', _('All')),
            (None, _('активный')),
        )
        choices += Order.STATUS_CHOICES
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
            return queryset.filter(status__exact=self.value())
        if self.value() is None:
            return queryset.filter(status__in=[Order.STATUS_NEW, Order.STATUS_ACCEPTED, Order.STATUS_COLLECTING, Order.STATUS_COLLECTED, Order.STATUS_SENT, Order.STATUS_DELIVERED_SHOP, Order.STATUS_CONSULTATION, Order.STATUS_PROBLEM, Order.STATUS_SERVICE])


class OrderDeliveryListFilter(admin.SimpleListFilter):
    title = _('доставка')
    template = 'django_admin_listfilter_dropdown/dropdown_filter.html'

    parameter_name = 'delivery'

    def lookups(self, request, model_admin):
        """
        Returns a list of tuples. The first element in each
        tuple is the coded value for the option that will
        appear in the URL query. The second element is the
        human-readable name for the option that will appear
        in the right sidebar.
        """
        choices = (
            ('all', _('All')),
            (-Order.DELIVERY_YANDEX, _('кроме Яндекс.Доставки')),
        )
        choices += Order.DELIVERY_CHOICES
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
            value = int(self.value())
            if value < 0:
                return queryset.exclude(delivery__exact=(-value))
            else:
                return queryset.filter(delivery__exact=value)


class FutureDateFieldListFilter(admin.FieldListFilter):
    template = 'django_admin_listfilter_dropdown/dropdown_filter.html'

    def __init__(self, field, request, params, model, model_admin, field_path):
        self.field_generic = '%s__' % field_path
        self.date_params = {k: v for k, v in params.items()
                            if k.startswith(self.field_generic)}

        now = timezone.now()
        # When time zone support is enabled, convert "now" to the user's time
        # zone so Django's definition of "Today" matches what the user expects.
        if timezone.is_aware(now):
            now = timezone.localtime(now)

        if isinstance(field, DateTimeField):
            today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        else:       # field is a models.DateField
            today = now.date()
        tomorrow = today + datetime.timedelta(days=1)
        # if today.month == 12:
        #     next_month = today.replace(year=today.year + 1, month=1, day=1)
        # else:
        #     next_month = today.replace(month=today.month + 1, day=1)
        # next_year = today.replace(year=today.year + 1, month=1, day=1)
        shop_epoch = datetime.date(2000, 1, 1)

        self.lookup_kwarg_since = '%s__gte' % field_path
        self.lookup_kwarg_until = '%s__lt' % field_path
        self.links = (
            (_('Any date'), {}),
            (_('Просрочена'), {
                self.lookup_kwarg_since: str(shop_epoch),
                self.lookup_kwarg_until: str(today),
            }),
            (_('Today'), {
                self.lookup_kwarg_since: str(today),
                self.lookup_kwarg_until: str(tomorrow),
            }),
            (_('Завтра'), {
                self.lookup_kwarg_since: str(tomorrow),
                self.lookup_kwarg_until: str(tomorrow + datetime.timedelta(days=1)),
            }),
            (_('Следующие 2 дня'), {
                self.lookup_kwarg_since: str(tomorrow),
                self.lookup_kwarg_until: str(tomorrow + datetime.timedelta(days=2)),
            }),
            (_('Следующие 7 дней'), {
                self.lookup_kwarg_since: str(tomorrow),
                self.lookup_kwarg_until: str(tomorrow + datetime.timedelta(days=7)),
            }),
        )
        if field.null:
            self.lookup_kwarg_isnull = '%s__isnull' % field_path
            self.links += (
                (_('Без даты'), {self.field_generic + 'isnull': 'True'}),
                (_('С датой'), {self.field_generic + 'isnull': 'False'}),
            )
        super(FutureDateFieldListFilter, self).__init__(
            field, request, params, model, model_admin, field_path)

    def expected_parameters(self):
        params = [self.lookup_kwarg_since, self.lookup_kwarg_until]
        if self.field.null:
            params.append(self.lookup_kwarg_isnull)
        return params

    def choices(self, changelist):
        for title, param_dict in self.links:
            yield {
                'selected': self.date_params == param_dict,
                'query_string': changelist.get_query_string(param_dict, [self.field_generic]),
                'display': title,
            }


class SiteListFilter(admin.filters.RelatedFieldListFilter):
    template = 'django_admin_listfilter_dropdown/dropdown_filter.html'

    def __init__(self, field, request, params, model, model_admin, field_path):
        self.lookup_kwarg_integrated = 'not__%s__%s__in' % (field_path, field.target_field.name)
        self.lookup_val_integrated = params.get(self.lookup_kwarg_integrated)
        super().__init__(field, request, params, model, model_admin, field_path)

    def expected_parameters(self):
        return [self.lookup_kwarg, self.lookup_kwarg_isnull, self.lookup_kwarg_integrated]

    def queryset(self, request, queryset):
        excludes = {}
        for key in list(self.used_parameters.keys()):
            if key.startswith('not__'):
                excludes[key[5:]] = self.used_parameters[key]
                del self.used_parameters[key]
        qs = super().queryset(request, queryset)
        if excludes:
            qs = qs.filter(~Q(**excludes))
        return qs

    def choices(self, changelist):
        yield {
            'selected': self.lookup_val is None and self.lookup_val_integrated is None and not self.lookup_val_isnull,
            'query_string': changelist.get_query_string(remove=[self.lookup_kwarg, self.lookup_kwarg_isnull, self.lookup_kwarg_integrated]),
            'display': _('All'),
        }
        yield {
            'selected': bool(self.lookup_val_integrated),
            'query_string': changelist.get_query_string({self.lookup_kwarg_integrated: '13,8,5,11,12,14,9'}, [self.lookup_kwarg, self.lookup_kwarg_isnull]),
            'display': 'Кроме интеграций'
        }
        for pk_val, val in self.lookup_choices:
            yield {
                'selected': self.lookup_val == str(pk_val),
                'query_string': changelist.get_query_string({self.lookup_kwarg: pk_val}, [self.lookup_kwarg_isnull, self.lookup_kwarg_integrated]),
                'display': val,
            }
        if self.include_empty_choice:
            yield {
                'selected': bool(self.lookup_val_isnull),
                'query_string': changelist.get_query_string({self.lookup_kwarg_isnull: 'True'}, [self.lookup_kwarg, self.lookup_kwarg_integrated]),
                'display': self.empty_value_display,
            }


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    @mark_safe
    def order_name(self, obj):
        manager = ''
        if obj.manager:
            manager = ' style="color: %s"' % obj.manager.color
        lock = ''
        if obj.owner:
            lock = '<span style="font-weight: 400" title="%s">&#9919;&nbsp;</span>' % str(obj.owner)
        return '<span style="white-space:nowrap">%s<b%s>%s</b></span><br/><span style="white-space:nowrap">%s</span>' % \
            (lock, manager, obj.title, date_format(timezone.localtime(obj.created), "DATETIME_FORMAT"))
    order_name.admin_order_field = 'id'
    order_name.short_description = 'заказ'

    @mark_safe
    def combined_comments(self, obj):
        comment = []
        if obj.alert:
            comment.append('<span style="color:#ba2121">{}</span><br/>'.format(obj.alert))
        if obj.is_beru or obj.is_sber:
            comment.append('<span style="color:#2121ba">№{}</span> '.format(obj.delivery_tracking_number))
        else:
            if obj.delivery_yd_order:
                comment.append('<span style="color:#2121ba">{}</span> '.format(obj.delivery_yd_order))
            if obj.delivery_tracking_number:
                if obj.delivery_yd_order:
                    comment.append('<span style="color:#2121ba">&#10095;</span> ')
                comment.append('<span style="color:#21baba">{}</span> '.format(obj.delivery_tracking_number))
        comment.append('{}<br/><em>{}</em>'.format(obj.delivery_info, obj.manager_comment))
        return ''.join(comment)
    combined_comments.admin_order_field = 'manager_comment'
    combined_comments.short_description = 'Комментарии'

    @mark_safe
    def combined_delivery(self, obj):
        datetime = ''
        if obj.delivery_dispatch_date:
            datetime = date_format(obj.delivery_dispatch_date, "d.m")
        if obj.delivery_handing_date:
            datetime = datetime + '<span style="color:#21baba">&#8594;' + date_format(obj.delivery_handing_date, "d.m") + '</span>'
        courier = ''
        if obj.courier:
            if obj.hidden_tracking_number:
                courier = ': %s&nbsp;<span style="color: blue; font-weight: bold" title="%s">&#10003;</span>' % (obj.courier.name, obj.hidden_tracking_number)
            else:
                courier = ': %s' % obj.courier.name
        return '%s%s<br/>%s' % (obj.get_delivery_display(), courier, datetime)
    combined_delivery.admin_order_field = 'delivery_dispatch_date'
    combined_delivery.short_description = 'Доставка'

    @mark_safe
    def name_and_phone(self, obj):
        name = obj.name if obj.name else '---'
        phone = ShopUserManager.format_phone(obj.user.phone) if obj.user.phone[0] == '+' else '---'
        return '{}<br/>{}'.format(name, phone)
    name_and_phone.admin_order_field = 'phone'
    name_and_phone.short_description = 'Покупатель'

    @mark_safe
    def colored_status(self, obj):
        return '<span style="color: %s">%s</span>' % (obj.STATUS_COLORS[obj.status], obj.get_status_display())
    colored_status.admin_order_field = 'status'
    colored_status.short_description = 'статус'

    @mark_safe
    def combined_payment(self, obj):
        style = ''
        checkmark = ''
        if obj.paid and obj.has_fiscal:
            style = '; color: green'
            checkmark = '<a href="https://receipt.taxcom.ru/v01/show?fp=%s&s=%s" target="_blank" style="color: green; font-size: 150%%">&#128457;</a>' % (obj.meta['fiscalInfo']['fnDocMark'], obj.meta['fiscalInfo']['sum'])
        elif obj.paid:
            style = 'color: green'
            checkmark = '<span style="color: green; font-size: 120%%">&#10003;</span>'
        elif obj.payment in [Order.PAYMENT_CARD, Order.PAYMENT_TRANSFER, Order.PAYMENT_CREDIT]:
            style = 'color: red'
        return '<span style="display: grid; grid-template-columns: min-content auto; column-gap: 5px"><span style="%s">%s</span>%s</span>' % (style, obj.get_payment_display(), checkmark)
    combined_payment.admin_order_field = 'payment'
    combined_payment.short_description = 'оплата'

    @mark_safe
    def total_cost(self, obj):
        if obj.total == int(obj.total):
            return number_format(int(obj.total), force_grouping=True)
        else:
            return number_format(obj.total, force_grouping=True)
    total_cost.short_description = 'всего'

    @mark_safe
    def link_to_user(self, obj):
        inconsistency = '-'
        if obj.name != obj.user.name or obj.phone != obj.user.phone or \
           obj.email != obj.user.email or obj.postcode != obj.user.postcode or \
           obj.address != obj.user.address:
            inconsistency = '<span style="color: red" title="Несоответствие данных!">&#10033;</span>'
        return inconsistency
    link_to_user.short_description = 'несоответствие'

    @mark_safe
    def link_to_orders(self, obj):
        orders = Order.objects.filter(user=obj.user.id).exclude(pk=obj.id).values_list('id', flat=True)
        if not orders:
            return '<span>нет</span>'
        else:
            url = '%s?pk__in=%s,%s&status=all' % (reverse("admin:shop_order_changelist"), obj.id, ','.join(map(lambda x: str(x), list(orders))))
            return '<span><a href="%s">%s</a></span>' % (url, orders.count())
    link_to_orders.short_description = 'заказы'

    @mark_safe
    def user_bonuses(self, obj):
        return '<span>%d</span>' % obj.user.bonuses
    user_bonuses.short_description = 'бонусы'

    @mark_safe
    def credit_notice(self, obj):
        credit_allowed = False
        for item in obj.items.all():
            credit_allowed = credit_allowed or item.product.credit_allowed
        if credit_allowed:
            return '''
                   <div id="yandex-credit"></div>
                   <script src="https://static.yandex.net/kassa/pay-in-parts/ui/v1"></script>
                   <script>
                   $(document).ready(function() {
                     const $checkoutCreditUI = YandexCheckoutCreditUI({ shopId: '42873', sum: '%d' });
                     const checkoutCreditText = $checkoutCreditUI({ type: 'info', domSelector: '#yandex-credit' });
                   });
                   </script>
                   ''' % obj.total
        else:
            return 'нет'
    credit_notice.short_description = 'кредит'

    @mark_safe
    def pos_status(self, obj):
        if obj.hidden_tracking_number:
            return '<span style="color: blue; font-weight: bold" title="{}">&#10003;</span>'.format(obj.hidden_tracking_number)
        else:
            return ''
    pos_status.short_description = 'касса'

    list_display = ['order_name', 'name_and_phone', 'city', 'total_cost', 'combined_payment', 'combined_delivery',
                    'colored_status', 'combined_comments']
    readonly_fields = ['id', 'shop_name', 'credit_notice', 'total', 'products_price', 'created', 'link_to_user', 'link_to_orders', 'user_bonuses', 'pos_status',
                       'delivery_pickpoint_terminal', 'delivery_pickpoint_service', 'delivery_pickpoint_reception',  # these fields are disabled for massadmin
                       'delivery_size_length', 'delivery_size_width', 'delivery_size_height']  # these fields are disabled for massadmin
    list_filter = [OrderStatusListFilter, ('site', SiteListFilter), ('created', PastDateRangeFilter), ('payment', ChoiceDropdownFilter),
                   'paid', OrderDeliveryListFilter, ('delivery_dispatch_date', FutureDateRangeFilter),
                   ('delivery_handing_date', FutureDateRangeFilter), 'manager', 'courier']
    search_fields = ['id', 'name', 'phone', 'email', 'address', 'city', 'comment', 'manager_comment', 'delivery_tracking_number',
                     'delivery_yd_order', 'user__name', 'user__phone', 'user__email', 'user__address', 'user__postcode',
                     'item__serial_number']
    inlines = [OrderItemInline, BoxInline]
    form = OrderAdminForm
    autocomplete_fields = ('store', 'user')
    formfield_overrides = {
        TextField: {'widget': forms.Textarea(attrs={'style': 'width: 60%; height: 4em'})},
        PositiveSmallIntegerField: {'widget': forms.TextInput(attrs={'style': 'width: 4em'})},
        PositiveIntegerField: {'widget': forms.TextInput(attrs={'style': 'width: 6em'})},
        DecimalField: {'widget': forms.TextInput(attrs={'style': 'width: 6em'})},
    }
    actions = ['order_product_list_action', 'order_1c_action', 'order_pickpoint_action', 'order_stock_action',
               'order_products_action', 'order_beru_action', 'order_set_user_tag_action', 'beru_labels', 'order_act_action']
    save_as = True
    save_on_top = True
    list_per_page = 50

    def get_fieldsets(self, request, obj=None):
        fieldsets = (
            (None, {'fields': [['status', 'payment', 'paid', 'manager', 'site'], ['delivery', 'delivery_price'],
                               'delivery_dispatch_date', ['delivery_tracking_number'], 'delivery_info',
                               ['delivery_handing_date'], 'manager_comment', 'alert',
                               'products_price', 'total', 'id']}),
            ('1С', {'fields': (('buyer', 'seller', 'wiring_date'),)}),
            # ('PickPoint', {'fields': (('delivery_pickpoint_terminal', 'delivery_pickpoint_service', 'delivery_pickpoint_reception'),
            #                           ('delivery_size_length', 'delivery_size_width', 'delivery_size_height'),),}),
            ('Покупатель', {'fields': []})
        )
        if obj and obj.is_beru:
            fieldsets[2][1]['fields'].extend(('address', ('city', 'postcode')))
        elif obj and obj.is_sber:
            fieldsets[2][1]['fields'].extend(('name', 'address', ('city', 'postcode')))
        else:
            fieldsets[0][1]['fields'].append('store')
            fieldsets[0][1]['fields'][0].append('credit_notice')
            fieldsets[0][1]['fields'][1].append('courier')
            fieldsets[0][1]['fields'][3].append('delivery_yd_order')
            fieldsets[0][1]['fields'][5].extend(('delivery_time_from', 'delivery_time_till'))
            fieldsets[2][1]['fields'].extend((('name', 'user', 'link_to_user', 'link_to_orders', 'user_bonuses'), ('phone', 'phone_aux', 'email'),
                                              'address', ('city', 'postcode'), 'comment', ('firm_name', 'is_firm')))
            if obj and obj.hidden_tracking_number:
                fieldsets[0][1]['fields'][1].append('pos_status')
            if obj is None or obj.is_firm:
                fieldsets[2][1]['fields'].extend(('firm_address', 'firm_details'))
            fieldsets[2][1]['fields'].append('user_tags')
        return fieldsets

    def get_formsets_with_inlines(self, request, obj=None):
        for inline in self.get_inline_instances(request, obj):
            # показываем встроенную форму коробок только для заказов Беру и Яндекс.Доставки:
            # тут немного сложная логика, так как этот метод вызывается и при показе формы, и при сохранении
            # и надо правильно отработать ситуацию, когда способ доставки уже поменяли, а встроенной формы
            # с коробками ещё не было
            is_beru = obj and obj.is_beru
            is_sber = obj and obj.is_sber
            is_yandex_delivery = obj and obj.delivery == Order.DELIVERY_YANDEX
            has_boxes_form = 'boxes-TOTAL_FORMS' in request.POST
            if not inline.model == Box or is_beru or is_sber or (is_yandex_delivery and (has_boxes_form or request.method == 'GET')):
                yield inline.get_formset(request, obj), inline

    def lookup_allowed(self, lookup, value):
        if lookup == 'item__product__pk':
            return True
        return super().lookup_allowed(lookup, value)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser and request.user.has_perm('shop.change_order_spb'):
            qs = qs.filter(site__in=[6, 14])
        return qs

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = [elem for elem in self.readonly_fields]
        if obj and not request.user.is_superuser:
            readonly_fields += ['site']
        if obj and (obj.is_beru or obj.is_sber):
            readonly_fields += ['delivery_handing_date']
        if obj and obj.paid and obj.meta and 'fiscalInfo' in obj.meta:
            readonly_fields += ['paid']
        return readonly_fields

    def changelist_view(self, request, extra_context=None):
        if not request.user.is_staff:
            raise PermissionDenied
        if 'action' in request.POST and request.POST['action'] == 'order_product_list_action':
            if not request.POST.getlist(admin.ACTION_CHECKBOX_NAME):
                post = request.POST.copy()
                # '0' is special case for 'all'
                post.update({admin.ACTION_CHECKBOX_NAME: '0'})
                request._set_post(post)
        return super().changelist_view(request, extra_context)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        if not request.user.is_staff:
            raise PermissionDenied
        order = Order.objects.get(pk=object_id)
        if not order.owner:
            order.owner = request.user
            order.save()
        return super().change_view(request, object_id, form_url, extra_context)

    def save_model(self, request, obj, form, change):
        if "_unlock" in request.POST:
            obj.owner = None
            obj.save()
            return
        if "_save" in request.POST:
            obj.owner = None
        super().save_model(request, obj, form, change)

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        if not form.instance.is_beru and not form.instance.is_sber and not form.instance.delivery == Order.DELIVERY_YANDEX:
            return
        boxes = defaultdict(dict)
        for formset in filter(lambda f: isinstance(f.empty_form.instance, OrderItem), formsets):
            for inline in formset:
                if inline.cleaned_data.get('box', None) is not None:
                    product = inline.cleaned_data['product']
                    quantity = inline.instance.quantity
                    box = boxes[inline.cleaned_data['box']]
                    box['count'] = box.get('count', 0) + quantity
                    box['weight'] = box.get('weight', 0) + product.prom_weight * quantity
                    box['length'] = product.length
                    box['width'] = product.width
                    box['height'] = product.height
        for formset in filter(lambda f: isinstance(f.empty_form.instance, Box), formsets):
            for inline in formset:
                if inline.instance.pk is None:
                    continue
                box = boxes.get(inline.instance)
                if box is not None:
                    changed = False
                    if inline.cleaned_data['weight'] == 0:
                        inline.instance.weight = box['weight']
                        changed = True
                    if box['count'] == 1:
                        for dimension in ['length', 'width', 'height']:
                            if inline.cleaned_data[dimension] == 0:
                                setattr(inline.instance, dimension, box[dimension])
                                changed = True
                    if changed:
                        inline.instance.save()

    def get_urls(self):
        urls = super(OrderAdmin, self).get_urls()
        my_urls = [
            url(r'(\d+)/document/([a-z]+)/$', self.admin_site.admin_view(self.document), name='shop_order_document'),
            url(r'products/$', self.admin_site.admin_view(self.order_product_list), name='shop_order_product_list'),
            url(r'(\d+)/item/(\d+)/print_warranty_card/$', self.admin_site.admin_view(self.print_warranty_card), name='print-warranty-card'),
            url(r'(\d+)/combine/$', self.admin_site.admin_view(self.combine_form), name='shop_order_combine'),
            url(r'(\d+)/discount/$', self.admin_site.admin_view(self.discount_form), name='shop_order_discount'),
            url(r'(\d+)/yandex_delivery/$', self.admin_site.admin_view(self.yandex_delivery_form), name='shop_order_yandex_delivery'),
            url(r'(\d+)/yandex_delivery_estimate/$', self.admin_site.admin_view(self.yandex_delivery_estimate), name='shop_order_yandex_delivery_estimate'),
            url(r'(\d+)/beru_labels/$', self.admin_site.admin_view(self.beru_labels), name='shop_order_beru_labels'),
            url(r'(\d+)/unlock/$', self.admin_site.admin_view(self.unlock), name='shop_order_unlock'),
            url(r'sms/(\+\d+)/$', self.admin_site.admin_view(self.send_sms_form), name='shop_order_send_sms'),
        ]
        return my_urls + urls

    def document(self, request, id, template):
        if not request.user.is_staff:
            raise PermissionDenied
        order = Order.objects.get(pk=id)
        return render(request, 'shop/order/' + template + '.html', {
            'owner_info': getattr(settings, 'SHOP_OWNER_INFO', {}),
            'order': order,
            'opts': self.model._meta,
        })

    def order_product_list_action(self, request, queryset):
        if not request.user.is_staff:
            raise PermissionDenied
        selected = request.POST.getlist(admin.ACTION_CHECKBOX_NAME)
        return HttpResponseRedirect("products/?orders=%s" % ",".join(selected))
    order_product_list_action.short_description = "Показать товары для выбранных заказов"

    def order_product_list(self, request):
        if not request.user.is_staff:
            raise PermissionDenied
        suppliers = Supplier.objects.filter(show_in_order=True)
        list_of_ids = suppliers.values_list('id', flat=True)
        format_strings = ','.join(['%s'] * len(list_of_ids))
        ids = request.GET.get('orders', '0')
        where = ''
        if ids != '0':
            where = ' WHERE shop_order.id IN (' + ids + ')'
        sort = request.GET.get('o', 'shop_product.title')
        cursor = connection.cursor()
        inner_cursor = connection.cursor()
        cursor.execute("""SELECT shop_product.id AS product_id, shop_product.article, shop_product.partnumber, shop_product.title,
                          shop_order.id AS order_id, shop_order.status AS order_status,
                          SUM(shop_orderitem.quantity) AS quantity
                          FROM shop_product
                          INNER JOIN shop_orderitem ON (shop_product.id = shop_orderitem.product_id)
                          INNER JOIN shop_order ON (shop_orderitem.order_id = shop_order.id)""" + where +
                       """ GROUP BY shop_order.id, shop_product.id ORDER BY """ + sort)
        products = []
        for row in cursor.fetchall():
            columns = (x[0] for x in cursor.description)
            product = dict(zip(columns, row))
            product['order_status_value'] = dict(Order.STATUS_CHOICES)[product['order_status']]
            product['order_status_color'] = dict(Order.STATUS_COLORS)[product['order_status']]
            stock = ''
            inner_cursor.execute("""SELECT supplier_id, quantity FROM shop_stock LEFT JOIN shop_supplier ON (shop_supplier.id = supplier_id)
                                    WHERE product_id = %s AND supplier_id IN (%s) ORDER BY shop_supplier.order""" % (product['product_id'], format_strings), list_of_ids)
            if inner_cursor.rowcount:
                for row in inner_cursor.fetchall():
                    stock = stock + ('%s:&nbsp;' % suppliers.get(pk=row[0]).code)
                    if row[1] == 0:
                        stock = stock + '<span style="color: #c00">'
                    stock = stock + ('%s' % floatformat(row[1]))
                    if row[1] == 0:
                        stock = stock + '</span>'
                    stock = stock + '<br/>'
            else:
                stock = '<span style="color: #ff0000">отсутствует</span>'
            product['stock'] = stock
            products.append(product)
        cursor.close()
        inner_cursor.close()
        return render(request, 'admin/shop/order/products.html', {
            'title': 'Товары для заказов',
            'products': products,
            'orders': ids,
            'o': sort,
            'cl': self,
            'opts': self.model._meta,
            **self.admin_site.each_context(request)
        })

    def print_warranty_card(self, request, order_id, item_id):
        order = self.get_object(request, order_id)
        item = order.items.get(pk=item_id)

        if request.method != 'POST':
            form = WarrantyCardPrintForm({'serial_number': item.serial_number})
            is_popup = request.GET.get('_popup', 0)
        else:
            form = WarrantyCardPrintForm(request.POST)
            is_popup = request.POST.get('_popup', 0)
            if form.is_valid():
                try:
                    serial_number = form.cleaned_data['serial_number']
                    item.serial_number = serial_number
                    item.save()
                    context = {
                        'owner_info': getattr(settings, 'SHOP_OWNER_INFO', {}),
                        'order': order,
                        'product': item.product,
                        'serial_number': serial_number
                    }
                    return TemplateResponse(request, 'shop/order/warrantycard.html', context)

                except Exception:
                    # If save() raised, the form will a have a non
                    # field error containing an informative message.
                    pass

        context = self.admin_site.each_context(request)
        context['opts'] = self.model._meta
        context['form'] = form
        context['is_popup'] = is_popup
        context['title'] = "Печать гарантийного талона"

        return TemplateResponse(request, 'admin/shop/order/print_warranty_card.html', context)

    def combine_form(self, request, id):
        if not request.user.is_staff:
            raise PermissionDenied
        order = Order.objects.get(pk=id)
        messages = None
        if request.method != 'POST':
            form = OrderCombineForm()
            is_popup = request.GET.get('_popup', 0)
        else:
            form = OrderCombineForm(request.POST)
            is_popup = request.POST.get('_popup', 0)
            if form.is_valid():
                try:
                    order_number = form.cleaned_data['order_number']
                    other_order = Order.objects.get(pk=order_number)
                    if order.user != other_order.user:
                        form.add_error('order_number', "Разные пользователи у заказов")
                    else:
                        for item in other_order.items.all():
                            item.pk = None
                            item.order = order
                            item.save()
                        return HttpResponse('<!DOCTYPE html><html><head><title></title></head><body>'
                                            '<script type="text/javascript">opener.dismissPopupAndReload(window);</script>'
                                            '</body></html>')

                except Exception as e:
                    form.errors['__all__'] = form.error_class([str(e)])

        context = self.admin_site.each_context(request)
        context['cl'] = self
        context['opts'] = self.model._meta
        context['form'] = form
        context['is_popup'] = is_popup
        context['messages'] = messages
        context['title'] = "Укажите заказ для объединения"
        context['action_title'] = "Объеденить"

        return TemplateResponse(request, 'admin/shop/custom_action_form.html', context)

    def discount_form(self, request, id):
        if not request.user.is_staff:
            raise PermissionDenied
        order = Order.objects.get(pk=id)
        messages = None
        if request.method != 'POST':
            form = OrderDiscountForm()
            is_popup = request.GET.get('_popup', 0)
        else:
            form = OrderDiscountForm(request.POST)
            is_popup = request.POST.get('_popup', 0)
            if form.is_valid():
                try:
                    unit = form.cleaned_data['unit']
                    for item in order.items.all():
                        if unit == 'pct':
                            discount = int(form.cleaned_data['discount'])
                            if discount > item.pct_discount:
                                if discount <= item.product.max_discount:
                                    item.pct_discount = discount
                                else:
                                    item.pct_discount = item.product.max_discount
                                item.save()
                        elif unit == 'val':
                            discount = float(form.cleaned_data['discount'])
                            if discount > item.val_discount:
                                item.val_discount = discount
                                item.save()

                    return HttpResponse('<!DOCTYPE html><html><head><title></title></head><body>'
                                        '<script type="text/javascript">opener.dismissPopupAndReload(window);</script>'
                                        '</body></html>')

                except Exception as e:
                    form.errors['__all__'] = form.error_class([str(e)])

        context = self.admin_site.each_context(request)
        context['cl'] = self
        context['opts'] = self.model._meta
        context['form'] = form
        context['is_popup'] = is_popup
        context['messages'] = messages
        context['title'] = "Укажите скидку"
        context['action_title'] = "Применить"

        return TemplateResponse(request, 'admin/shop/custom_action_form.html', context)

    def yandex_delivery_form(self, request, id):
        if not request.user.is_staff:
            raise PermissionDenied
        order = Order.objects.get(pk=id)
        messages = None
        if request.method != 'POST':
            initial = {
                'fio': order.name,
            }
            form = YandexDeliveryForm(initial=initial)
            is_popup = request.GET.get('_popup', 0)
        else:
            form = YandexDeliveryForm(request.POST)
            is_popup = request.POST.get('_popup', 0)
            for item in order.items.all():
                if item.box is None:
                    form.add_error(None, "{} не упакован в коробку".format(item.product.code))
            if form.is_valid():
                try:
                    fio_last = form.cleaned_data['fio_last']
                    warehouse = form.cleaned_data['warehouse']

                    fio = order.name.split()
                    first_name = ''
                    middle_name = ''
                    last_name = ''
                    if len(fio) == 1:  # looks like it's a name only
                        first_name = fio[0]
                    elif len(fio) == 2:  # looks like it's name with surname
                        if fio_last:
                            fio.reverse()
                        last_name, first_name = fio
                    else:
                        if fio_last:
                            first_name, middle_name, last_name = fio
                        else:
                            last_name, first_name, middle_name = fio

                    yd_order = create_delivery_draft_order(order.id, warehouse, first_name, middle_name, last_name)

                    return HttpResponse('<!DOCTYPE html><html><head><title></title></head><body>'
                                        '<script type="text/javascript">opener.dismissYandexDeliveryPopup(window, "%s", "%s");</script>'
                                        '</body></html>' % (Order.DELIVERY_YANDEX, yd_order))

                except Exception as e:
                    form.errors['__all__'] = form.error_class([str(e)])

        context = self.admin_site.each_context(request)
        context['cl'] = self
        context['opts'] = self.model._meta
        context['form'] = form
        context['is_popup'] = is_popup
        context['messages'] = messages
        context['title'] = "Создать черновик заказа"
        context['action_title'] = "Создать"

        return TemplateResponse(request, 'admin/shop/custom_action_form.html', context)

    def yandex_delivery_estimate(self, request, id):
        if not request.user.is_staff:
            raise PermissionDenied

        order = Order.objects.get(pk=id)

        context = self.admin_site.each_context(request)
        context['opts'] = self.model._meta
        context['is_popup'] = request.GET.get('_popup', 0)
        context['title'] = "Варианты доставки"
        context['order'] = order
        context['city'] = request.GET.get('city', '{} {}'.format(order.postcode, order.city))
        context['weight'] = request.GET.get('weight', 10)
        context['height'] = request.GET.get('height', 27)
        context['length'] = request.GET.get('length', 50)
        context['width'] = request.GET.get('width', 40)

        try:
            results = get_delivery_options(order.total, order.paid, settings.YANDEX_DOSTAVKA['warehouses'][0]['id'], context['city'],
                                          context['weight'], context['width'], context['height'], context['length'])

            colors = [
                '#1E98FF',  # blue
                '#1BAD03',  # darkGreen
                '#ED4543',  # red
                '#E6761B',  # darkOrange
                '#B51EFF',  # violet
                '#0E4779',  # night
                '#FFD21E',  # yellow
                '#177BC9',  # darkBlue
                '#56DB40',  # green
                '#F371D1',  # pink
                '#FF931E',  # orange
                '#B3B3B3',  # gray
                '#82CDFF',  # lightBlue
                '#793D0E',  # brown
                '#97A100',  # olive
            ]
            deliveries = {}
            i = 0
            for result in results:
                delivery = result['delivery']
                delivery_type = deliveries.get(delivery['type'], None)
                if delivery_type is None:
                    delivery_type = []
                    deliveries[delivery['type']] = delivery_type
                #shop_cost = delivery['costWithRules']
                required_services = []
                optional_services = []
                for service in result['services']:
                    #if service['optional']:
                    #    optional_services.append(service)
                    #else:
                    required_services.append(service)
                    #shop_cost = shop_cost + service['cost']
                delivery['required_services'] = required_services
                delivery['optional_services'] = optional_services
                delivery['cost'] = result['cost']
                pickup_points = delivery.get('pickupPoints', [])
                if len(pickup_points):
                    delivery['color'] = colors[i]
                    i = i + 1
                else:
                    delivery['color'] = '#FFFFFF'
                dmf = datetime.time.max
                dmt = datetime.time.min
                for point in pickup_points:
                    mf = datetime.time.max
                    mt = datetime.time.min
                    for schedule in point.get('schedules', []):
                        fr = datetime.datetime.strptime(schedule['from'], '%H:%M:%S').time()
                        tl = datetime.datetime.strptime(schedule['to'], '%H:%M:%S').time()
                        if fr < mf:
                            mf = fr
                        if tl > mt:
                            mt = tl
                        if fr < dmf:
                            dmf = fr
                        if tl > dmt:
                            dmt = tl
                    if mf != datetime.time.max and mt != datetime.time.min:
                        point['delivery_interval'] = mark_safe('{}&ndash;{}'.format(mf.strftime('%H:%M'), mt.strftime('%H:%M')))
                if dmf == datetime.time.max or dmt == datetime.time.min:
                    for delivery_interval in delivery.get('deliveryIntervals', []):
                        fr = datetime.datetime.strptime(delivery_interval['from'], '%H:%M:%S').time()
                        tl = datetime.datetime.strptime(delivery_interval['to'], '%H:%M:%S').time()
                        if fr < dmf:
                            dmf = fr
                        if tl > dmt:
                            dmt = tl
                if dmf != datetime.time.max and dmt != datetime.time.min:
                    delivery['delivery_interval'] = mark_safe('{}&ndash;{}'.format(dmf.strftime('%H:%M'), dmt.strftime('%H:%M')))
                delivery_type.append(delivery)

            context['deliveries'] = deliveries
            context['result'] = results

        except Exception as e:
            context['error'] = str(e)

        return TemplateResponse(request, 'admin/shop/order/yandex_delivery_estimate.html', context)

    def beru_labels(self, request, arg):
        if not request.user.is_staff:
            raise PermissionDenied

        from beru.tasks import get_beru_labels_data
        import barcode

        context = self.admin_site.each_context(request)
        context['opts'] = self.model._meta
        context['is_popup'] = request.GET.get('_popup', 0)

        # this method is called both from order change form with single id argument and order list with selected orders queryset
        if isinstance(arg, str):
            orders = [Order.objects.get(pk=arg)]
        else:
            orders = arg.all()

        context['orders'] = []
        try:
            for order in orders:
                beru_order = get_beru_labels_data(order.id)
                beru_order_id = str(beru_order.get('orderId', 0))

                CODE128 = barcode.get_barcode_class('code128')
                order_barcode = CODE128(str(order.id)).render(writer_options={'module_width': 0.5, 'module_height': 15, 'compress': True}).decode()
                order_barcode = re.sub(r'^.*(?=<svg)', '', order_barcode)
                beru_order_barcode = CODE128(beru_order_id).render(writer_options={'module_width': 0.5, 'module_height': 15, 'compress': True}).decode()
                beru_order_barcode = re.sub(r'^.*(?=<svg)', '', beru_order_barcode)

                boxes = order.boxes.all()
                count = 0
                shipments = []
                for label in beru_order.get('parcelBoxLabels', []):
                    box = boxes[count]
                    count += 1
                    code = label.get('fulfilmentId', '')
                    item_barcode = CODE128(code).render(writer_options={'module_width': 0.5, 'module_height': 15, 'compress': True}).decode()
                    item_barcode = re.sub(r'^.*(?=<svg)', '', item_barcode)
                    shipments.append({
                        'id': code,
                        'code': box.code,
                        'place': label.get('place', ''),
                        'barcode': mark_safe(item_barcode),
                        'products': box.products.all(),
                        'weight': label.get('weight', ''),
                        'delivery_service_name': label.get('deliveryServiceName', '').replace('INDIVIDUAL_ENTREPRENEURSHIP', 'ИП'),
                        'delivery_service_id': label.get('deliveryServiceId', ''),
                        'supplier_name': label.get('supplierName', '')
                    })

                context['orders'].append({
                    'beru_order': beru_order,
                    'order': order,
                    'beru_barcode': mark_safe(beru_order_barcode),
                    'barcode': mark_safe(order_barcode),
                    'shipments': shipments
                })
        except Exception as e:
            context['error'] = getattr(e, 'message', str(e))

        return TemplateResponse(request, 'shop/order/beru_labels.html', context)
    beru_labels.short_description = "Печать наклеек Беру"

    def send_sms_form(self, request, phone):
        if not request.user.is_staff:
            raise PermissionDenied
        messages = None
        if request.method != 'POST':
            form = SendSmsForm()
            is_popup = request.GET.get('_popup', 0)
        else:
            form = SendSmsForm(request.POST)
            is_popup = request.POST.get('_popup', 0)
            if form.is_valid():
                try:
                    message = form.cleaned_data['message']
                    if message:
                        send_message.delay(phone, message)
                    messages = ["Сообщение отправлено, закройте окно"]
                    form = SendSmsForm()
                except Exception as e:
                    form.errors['__all__'] = form.error_class([str(e)])

        context = self.admin_site.each_context(request)
        context['cl'] = self
        context['opts'] = self.model._meta
        context['form'] = form
        context['is_popup'] = is_popup
        context['messages'] = messages
        context['title'] = "Укажите текст сообщения для %s" % str(phone)
        context['action_title'] = "Отправить"

        return TemplateResponse(request, 'admin/shop/custom_action_form.html', context)

    def unlock(self, request, id):
        if not request.user.is_staff:
            raise PermissionDenied
        order = Order.objects.get(pk=id)
        if order.owner == request.user:
            order.owner = None
            order.save()
        return HttpResponse('<!DOCTYPE html><html/>')

    def order_1c_action(self, request, queryset):
        if not request.user.is_staff:
            raise PermissionDenied
        missing_contractors = set()
        missing_wiring_date = set()
        for order in queryset:
            if not order.buyer or not order.seller:
                missing_contractors.add(order.id)
            if not order.wiring_date:
                missing_wiring_date.add(order.id)
        if missing_contractors:
            self.message_user(request, "В заказах не указан контрагент: %s" % ', '.join(map(str, missing_contractors)), level=messages.ERROR)
        elif missing_wiring_date:
            self.message_user(request, "В заказах не указана дата проводки: %s" % ', '.join(map(str, missing_wiring_date)), level=messages.ERROR)
        else:
            template = get_template('admin/shop/order/1c.txt')
            response = HttpResponse(template.render({'orders': queryset}).replace('\n', '\r\n'), content_type='text/xml; charset=utf8')
            response['Content-Disposition'] = 'attachment; filename=1C-{0}.xml'.format(datetime.date.today().isoformat())
            return response
    order_1c_action.short_description = "Выгрузка в 1С"

    def order_pickpoint_action(self, request, queryset):
        if not request.user.is_staff:
            raise PermissionDenied
        missing_terminal = False
        for order in queryset:
            if not order.delivery_pickpoint_terminal:
                missing_terminal = True
        if missing_terminal:
            self.message_user(request, "Для одного из заказов не указан терминал", level=messages.ERROR)
        else:
            template = get_template('admin/shop/order/pickpoint.xml')
            response = HttpResponse(template.render({'orders': queryset}), content_type='text/plain; charset=utf-8')
            response['Content-Disposition'] = 'attachment; filename=PickPoint-{0}.xml'.format(datetime.date.today().isoformat())
            return response
    order_pickpoint_action.short_description = "Выгрузка в ПикПоинт"

    def order_stock_action(self, request, queryset):
        if not request.user.is_staff:
            raise PermissionDenied
        if 'show_stock' in request.POST:
            supplier_ur = Supplier.objects.get(code='Ур')
            supplier = Supplier.objects.get(pk=request.POST.get('supplier'))
            if request.POST.get('aux_supplier'):
                aux_supplier = Supplier.objects.get(pk=request.POST.get('aux_supplier'))
            else:
                aux_supplier = None
            selected = request.POST.getlist(admin.ACTION_CHECKBOX_NAME)
            cursor = connection.cursor()
            inner_cursor = connection.cursor()
            cursor.execute("""SELECT shop_product.id AS product_id, shop_product.article,
                              SUM(shop_orderitem.quantity) AS quantity
                              FROM shop_product
                              INNER JOIN shop_orderitem ON (shop_product.id = shop_orderitem.product_id)
                              INNER JOIN shop_order ON (shop_orderitem.order_id = shop_order.id)
                              WHERE shop_order.id IN (""" + ','.join(selected) + """)
                              GROUP BY shop_product.id ORDER BY shop_product.article""")
            products = []
            suppliers = [supplier_ur.id, supplier.id]
            if aux_supplier:
                suppliers.append(aux_supplier.id)
            supplier_ids = ','.join(map(str, suppliers))
            for row in cursor.fetchall():
                columns = (x[0] for x in cursor.description)
                product = dict(zip(columns, row))
                stock = ''
                inner_cursor.execute("""SELECT supplier_id, quantity, correction FROM shop_stock
                                        LEFT JOIN shop_supplier ON (shop_supplier.id = supplier_id)
                                        WHERE product_id = %s AND supplier_id IN (""" + supplier_ids + """)
                                        ORDER BY shop_supplier.order""", (product['product_id'],))
                quantity = float(product['quantity'])
                stock = 0
                aux_stock = 0
                if inner_cursor.rowcount:
                    for row in inner_cursor.fetchall():
                        if row[0] == supplier_ur.id:
                            quantity = quantity - row[1] - row[2]
                        if row[0] == supplier.id:
                            stock = row[1] + row[2]
                        if aux_supplier and row[0] == aux_supplier.id:
                            aux_stock = row[1] + row[2]
                if quantity > 0:
                    if stock > 0:
                        product['stock'] = Decimal(quantity).quantize(Decimal('1'), rounding=ROUND_UP)
                    if aux_stock > 0 and quantity - stock > 0:
                        product['aux_stock'] = Decimal(quantity-stock).quantize(Decimal('1'), rounding=ROUND_UP)
                    products.append(product)
            cursor.close()
            inner_cursor.close()
            if not products:
                self.message_user(request, "Нет товаров для отгрузки у этого поставщика", level=messages.WARNING)
                return
            else:
                import io
                import xlsxwriter

                output = io.BytesIO()
                workbook = xlsxwriter.Workbook(output)
                sheet = workbook.add_worksheet(supplier.name)
                idx = 0
                for product in products:
                    stock = product.get('stock', None)
                    if stock:
                        sheet.write(idx, 0, product['article'])
                        sheet.write(idx, 1, product['stock'])
                        idx += 1
                if aux_supplier:
                    sheet = workbook.add_worksheet(aux_supplier.name)
                    idx = 0
                    for product in products:
                        aux_stock = product.get('aux_stock', None)
                        if aux_stock:
                            sheet.write(idx, 0, product['article'])
                            sheet.write(idx, 1, aux_stock)
                            idx += 1
                workbook.close()

                response = HttpResponse(output.getvalue(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                response['Content-Disposition'] = 'attachment; filename={0}-{2}.xlsx; filename*=UTF-8\'\'{1}-{2}.xlsx'.format(
                    'stock',
                    urlquote(supplier.code),
                    datetime.date.today().isoformat())
                return response

        form = SelectSupplierForm(initial={'supplier': Supplier.objects.get(code='С3').pk})
        context = self.admin_site.each_context(request)
        context['cl'] = self
        context['opts'] = self.model._meta
        context['form'] = form
        context['queryset'] = queryset
        context['is_popup'] = 0
        context['title'] = "Выберите поставщика"
        context['action'] = 'order_stock_action'
        context['action_name'] = 'show_stock'
        context['action_title'] = "Сформировать выгрузку"

        return TemplateResponse(request, 'admin/shop/custom_action_form.html', context)
    order_stock_action.short_description = "Выгрузка поставщику"

    def order_products_action(self, request, queryset):
        if not request.user.is_staff:
            raise PermissionDenied
        selected = request.POST.getlist(admin.ACTION_CHECKBOX_NAME)
        cursor = connection.cursor()
        cursor.execute("""SELECT shop_orderitem.product_id, shop_product.article, SUM(shop_orderitem.quantity) AS quantity
                          FROM shop_orderitem INNER JOIN shop_product ON (shop_product.id = shop_orderitem.product_id)
                          INNER JOIN shop_order ON (shop_orderitem.order_id = shop_order.id)
                          WHERE shop_orderitem.order_id IN (""" + ','.join(selected) + """)
                          GROUP BY shop_orderitem.product_id, shop_product.article""")
        products = []
        for row in cursor.fetchall():
            columns = (x[0] for x in cursor.description)
            product = dict(zip(columns, row))
            products.append(product)
        cursor.close()
        import io
        import xlsxwriter

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        sheet = workbook.add_worksheet('Products')
        for idx, product in enumerate(products):
            sheet.write(idx, 0, product['article'])
            sheet.write(idx, 1, product['quantity'])
        workbook.close()

        response = HttpResponse(output.getvalue(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename=products-{}.xlsx'.format(datetime.date.today().isoformat())
        return response
    order_products_action.short_description = "Выгрузка товаров"

    def order_beru_action(self, request, queryset):
        if not request.user.is_staff:
            raise PermissionDenied
        return TemplateResponse(request, 'admin/shop/order/beru.html', {'orders': queryset})
    order_beru_action.short_description = "Список заказов Беру"

    def order_set_user_tag_action(self, request, queryset):
        if not request.user.is_staff:
            raise PermissionDenied
        if 'set_user_tag' in request.POST:
            tags = parse_tag_input(request.POST.get('tags'))
            for order in queryset:
                order.append_user_tags(tags)
            self.message_user(request, "Добавлен тег {} пользователям".format(queryset.count()))
            return HttpResponseRedirect(request.get_full_path())

        messages = None
        form = SelectTagForm(model=ShopUser)
        """
            if form.is_valid():
                try:
                    message = form.cleaned_data['message']
                    if message:
                        send_message.delay(phone, message)
                    messages = ["Сообщение отправлено, закройте окно"]
                    form = SendSmsForm()
                except Exception as e:
                    form.errors['__all__'] = form.error_class([str(e)])
        """
        context = self.admin_site.each_context(request)
        context['cl'] = self
        context['opts'] = self.model._meta
        context['form'] = form
        context['queryset'] = queryset
        context['is_popup'] = 0
        context['messages'] = messages
        context['title'] = "Укажите один или несколько тегов"
        context['action'] = 'order_set_user_tag_action'
        context['action_name'] = 'set_user_tag'
        context['action_title'] = "Добавить"

        return TemplateResponse(request, 'admin/shop/custom_action_form.html', context)
    order_set_user_tag_action.short_description = "Добавить тег покупателю"

    def order_act_action(self, request, queryset):
        if not request.user.is_staff:
            raise PermissionDenied
        wrong_status = set()
        already_acted = set()
        for order in queryset:
            if order.status != Order.STATUS_COLLECTED:
                wrong_status.add(order.id)
            if order.acts.exists():
                already_acted.add(order.id)
        if wrong_status:
            self.message_user(request, "Нельзя выписать акт по несобранным заказам: %s" % ', '.join(map(str, wrong_status)), level=messages.ERROR)
        elif already_acted:
            self.message_user(request, "Некоторые заказы уже описаны в других актах: %s" % ', '.join(map(str, already_acted)), level=messages.ERROR)
        else:
            act = Act()
            act.save()
            # act.orders.add(*queryset) - will be available in Django 2.2
            for order in queryset:
                ActOrder.objects.create(act=act, order=order)
            for order in queryset:  # we do it in separate loops to correctly handle errors
                order.status = Order.STATUS_SENT
                order.save()
            return HttpResponseRedirect(reverse('admin:shop_act_change', args=[act.pk]))
    order_act_action.short_description = "Сформировать акт"
