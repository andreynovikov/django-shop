import logging
import datetime
from urllib.parse import quote

from django import forms
from django.db.models import TextField, PositiveSmallIntegerField, PositiveIntegerField, DecimalField
from django.core.exceptions import PermissionDenied
from django.contrib import admin, messages
from django.http import HttpResponse, HttpResponseRedirect
from django.template.loader import get_template
from django.template.response import TemplateResponse
from django.conf import settings
from django.shortcuts import render
from django.urls import re_path, reverse
from django.utils import timezone
from django.utils.formats import date_format, number_format
from django.utils.safestring import mark_safe

from daterangefilter.filters import FutureDateRangeFilter, PastDateRangeFilter
from more_admin_filters import ChoicesDropdownFilter, RelatedDropdownFilter
# from tagging.utils import parse_tag_input

from constance import config

from yandex_delivery.tasks import create_delivery_draft_order, get_delivery_options

from shop.models import ShopUserManager, ShopUser, Supplier, Order, OrderItem, Box, Contractor
from shop.tasks.user_interaction import send_message

from .forms import WarrantyCardPrintForm, OrderAdminForm, OrderCombineForm, \
    OrderDiscountForm, SendSmsForm, SelectTagForm, SelectSupplierForm, \
    OrderItemInlineAdminForm, BoxInlineAdminForm, YandexDeliveryForm
from .order_editing import apply_discount, combine_orders, confirm_buyer_email
from .order_filters import OrderStatusListFilter, OrderDeliveryListFilter, BooleanDropdownFilter, OrderOwnerFilter, \
    OrderIntegrationFilter
from .order_shipping import measure_boxes, fill_box, split_name, delivery_options, beru_order_labels, act_problems, \
    make_act, missing_1c_data
from .order_supply import OWN_WAREHOUSE, DEFAULT_SUPPLIER, order_products, allocate_stock, stock_workbook, \
    products_workbook
from .views import product_stock_view


logger = logging.getLogger(__name__)


def parse_ids(values):
    """ Convert a list of strings into a list of integer IDs, skipping anything that is not one """
    ids = []
    for value in values:
        value = value.strip()
        if value.isascii() and value.isdigit():
            ids.append(int(value))
    return ids


def close_popup(script='opener.dismissPopupAndReload(window);'):
    """ Response that closes the popup with the script, by default the page that opened it reloads """
    return HttpResponse('<!DOCTYPE html><html><head><title></title></head><body>'
                        '<script type="text/javascript">%s</script>'
                        '</body></html>' % script)


class OrderItemInline(admin.TabularInline):
    @mark_safe
    def product_codes(self, obj):
        code = obj.product.code or '--'
        article = obj.product.article or '--'
        partnumber = obj.product.partnumber or '--'
        code = '<a href="{}">{}</a>'.format(reverse('admin:shop_product_change', args=[obj.product.id]), code)
        if obj.product.state:
            state = '<span title="{}" class="sw-product-state">'.format(obj.product.state)
        else:
            state = '<span>'
        return state + '<br/>'.join([code, article, partnumber]) + '</span>'
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
        if obj and obj.integration and obj.integration.uses_api:
            fields.extend(['val_discount', 'quantity', 'total', 'product_stock'])
        else:
            fields.extend(['product_price', 'pct_discount', 'val_discount', 'item_cost', 'quantity', 'total', 'product_stock'])
        if obj and ((obj.integration and obj.integration.uses_boxes) or obj.delivery == Order.DELIVERY_YANDEX):
            fields.append('box')
        return fields

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = [elem for elem in self.readonly_fields]
        if obj and obj.integration and obj.integration.uses_api:
            readonly_fields += ['val_discount', 'quantity']
        return readonly_fields

    def has_add_permission(self, request, obj=None):
        return not obj or not obj.integration or not obj.integration.uses_api

    def has_delete_permission(self, request, obj=None):
        return obj and not (obj.integration and obj.integration.uses_api)


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


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    @mark_safe
    def order_name(self, obj):
        manager = ''
        express = ''
        if obj.manager:
            manager = ' style="color: %s"' % obj.manager.color
        lock = ''
        if obj.owner:
            lock = '&nbsp;<i class="ti ti-lock" title="%s" style="font-weight: bold"></i>' % str(obj.owner)
        if obj.delivery == Order.DELIVERY_EXPRESS:
            express = ' class="is-express"'
        elif obj.integration and obj.integration.uses_api and obj.integration.settings:
            if obj.integration.settings.get('is_taxi', False):
                express = ' class="is-express"'
        return '<span style="white-space:nowrap"%s><b%s>%s</b>%s</span><br/><span style="white-space:nowrap">%s</span>' % \
            (express, manager, obj.title, lock, date_format(timezone.localtime(obj.created), "DATETIME_FORMAT"))
    order_name.admin_order_field = 'id'
    order_name.short_description = 'заказ'

    @mark_safe
    def combined_comments(self, obj):
        comment = []
        if obj.alert:
            comment.append('<span style="color:#ba2121">{}</span><br/>'.format(obj.alert))
        if obj.integration and obj.integration.uses_api:
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
                courier = ': %s <i class="ti ti-check" style="color: blue" title="%s"></i>' % (obj.courier.name, obj.hidden_tracking_number)
            else:
                courier = ': %s' % obj.courier.name
        return '%s<span style="white-space:nowrap">%s</span><br/>%s' % (obj.get_delivery_display(), courier, datetime)
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
            if obj.id > 152982:  # TODO: move to order.seller
                checkmark = '<a href="https://consumer.1-ofd.ru/ticket?s=%s&fn=%s&i=%s&fp=%s&n=1" target="_blank" style="color: green"><i class="ti ti-receipt"></i></a>' % (obj.meta['fiscalInfo']['sum'], obj.meta['fiscalInfo']['fnNumber'], obj.meta['fiscalInfo']['fnDocNumber'], obj.meta['fiscalInfo']['fnDocMark'])
            else:
                checkmark = '<a href="https://receipt.taxcom.ru/v01/show?fp=%s&s=%s" target="_blank" style="color: green"><i class="ti ti-receipt"></i></a>' % (obj.meta['fiscalInfo']['fnDocMark'], obj.meta['fiscalInfo']['sum'])
        elif obj.paid:
            style = 'color: green'
            checkmark = '<span style="color: green"><i class="ti ti-check"></i></span>'
        elif obj.payment in [Order.PAYMENT_CARD, Order.PAYMENT_TRANSFER, Order.PAYMENT_CREDIT]:
            style = 'color: red'
        return '<span style="display: grid; grid-template-columns: min-content auto; column-gap: 5px"><span style="%s">%s</span>%s</span>' % (style, obj.get_payment_display(), checkmark)
    combined_payment.admin_order_field = 'payment'
    combined_payment.short_description = 'оплата'

    @mark_safe
    def status1c(self, obj):
        if obj.status <= Order.STATUS_COLLECTED:
            return ''
        if not obj.seller or not obj.buyer or not obj.wirehouse or not obj.wiring_date:
            return '<span style="color: orange" title="Нет данных для проводки"><i class="ti ti-calendar-question"></i></span>'
        if obj.wiring_date == timezone.now().date():
            return '<span style="color: #2121ba" title="Проводка сегодня"><i class="ti ti-calendar-bolt"></i></span>'
        return '<span style="color: green"><i class="ti ti-calendar-check"></i></span>'
    status1c.short_description = '1С'

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
    def delivery_barcode(self, obj):
        if obj.meta is not None and obj.meta.get('barcode'):
            return '<span>%s<b>%s</b></span>' % (obj.meta.get('barcode')[:-4], obj.meta.get('barcode')[-4:])
        else:
            return ''
    delivery_barcode.short_description = 'штрих-код доставки'

    @mark_safe
    def pos_status(self, obj):
        if obj.hidden_tracking_number:
            return '<span style="color: blue; font-weight: bold" title="{}">&#10003;</span>'.format(obj.hidden_tracking_number)
        else:
            return ''
    pos_status.short_description = 'касса'

    list_display = ['order_name', 'name_and_phone', 'city', 'total_cost', 'combined_payment', 'combined_delivery',
                    'colored_status', 'status1c', 'combined_comments']
    readonly_fields = ['id', 'shop_name', 'credit_notice', 'total', 'delivery_barcode', 'products_price', 'created', 'link_to_user', 'link_to_orders', 'user_bonuses', 'pos_status',
                       'delivery_pickpoint_terminal', 'delivery_pickpoint_service', 'delivery_pickpoint_reception',  # these fields are disabled for massadmin
                       'delivery_size_length', 'delivery_size_width', 'delivery_size_height']  # these fields are disabled for massadmin
    list_filter = [OrderStatusListFilter, ('site', RelatedDropdownFilter), ('integration', OrderIntegrationFilter), ('created', PastDateRangeFilter),
                   ('seller', RelatedDropdownFilter), ('payment', ChoicesDropdownFilter), ('paid', BooleanDropdownFilter), OrderDeliveryListFilter,
                   ('delivery_dispatch_date', FutureDateRangeFilter), ('delivery_handing_date', FutureDateRangeFilter),
                   ('manager', RelatedDropdownFilter), ('courier', RelatedDropdownFilter), OrderOwnerFilter]  # , ('owner', RelatedDropdownFilter)]
    search_fields = ['id', 'name', 'phone', 'email', 'address', 'city', 'comment', 'manager_comment', 'delivery_tracking_number',
                     'delivery_info', 'delivery_yd_order', 'user__name', 'user__phone', 'user__email', 'user__address', 'user__postcode',
                     'item__serial_number']
    inlines = [OrderItemInline, BoxInline]
    show_facets = admin.ShowFacets.NEVER
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
            (None, {'fields': [['status', 'manager', 'site', 'payment', 'paid'], ['delivery', 'delivery_price'],
                               'delivery_dispatch_date', ['delivery_tracking_number'], 'delivery_info',
                               ['delivery_handing_date'], 'manager_comment', 'alert',
                               'products_price', 'total', 'id']}),
            ('1С', {'fields': (('buyer', 'seller'), ('wirehouse', 'wiring_date'))}),
            # ('PickPoint', {'fields': (('delivery_pickpoint_terminal', 'delivery_pickpoint_service', 'delivery_pickpoint_reception'),
            #                           ('delivery_size_length', 'delivery_size_width', 'delivery_size_height'),),}),
            ('Покупатель', {'fields': []})
        )
        if obj and obj.integration and obj.integration.uses_api:
            fieldsets[0][1]['fields'][0][2] = 'integration'
            fieldsets[2][1]['fields'].extend(obj.integration.admin_user_fields)
            if obj.meta is not None and obj.meta.get('barcode'):
                fieldsets[0][1]['fields'][3].append('delivery_barcode')
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
            is_integration_with_boxes = obj and obj.integration and obj.integration.uses_boxes
            is_yandex_delivery = obj and obj.delivery == Order.DELIVERY_YANDEX
            has_boxes_form = 'boxes-TOTAL_FORMS' in request.POST
            if not inline.model == Box or is_integration_with_boxes or (is_yandex_delivery and (has_boxes_form or request.method == 'GET')):
                yield inline.get_formset(request, obj), inline

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'owner':
            kwargs['queryset'] = ShopUser.objects.filter(is_staff=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def lookup_allowed(self, lookup, value, request):
        if lookup == 'item__product__pk':
            return True
        return super().lookup_allowed(lookup, value, request)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser and request.user.has_perm('shop.change_order_spb'):
            qs = qs.filter(site__in=[6, 14])
        return qs

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = [elem for elem in self.readonly_fields]
        if obj and not request.user.is_superuser:
            readonly_fields += ['site']
        # if obj and obj.integration and obj.integration.uses_api:
        #     readonly_fields += ['delivery_handing_date']
        if obj and obj.paid and obj.meta and 'fiscalInfo' in obj.meta:
            readonly_fields += ['paid']
        return readonly_fields

    def changelist_view(self, request, extra_context=None):
        if not request.user.is_staff:
            raise PermissionDenied
        if 'action' in request.POST and request.POST['action'] == 'order_product_list_action':
            if not request.POST.getlist(admin.helpers.ACTION_CHECKBOX_NAME):
                post = request.POST.copy()
                # '0' is special case for 'all'
                post.update({admin.helpers.ACTION_CHECKBOX_NAME: '0'})
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
        if 'email' in form.changed_data and obj.email:
            self.confirm_user_email(request, obj)

    def confirm_user_email(self, request, order):
        message = confirm_buyer_email(order)
        if message is not None:
            messages.add_message(request, *message)

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        if not (form.instance.integration and form.instance.integration.uses_api) and not form.instance.delivery == Order.DELIVERY_YANDEX:
            return
        packed = []
        for formset in filter(lambda f: isinstance(f.empty_form.instance, OrderItem), formsets):
            for inline in formset:
                if inline.cleaned_data.get('box', None) is not None:
                    packed.append((inline.cleaned_data['box'], inline.cleaned_data['product'], inline.instance.quantity))
        boxes = measure_boxes(packed)
        for formset in filter(lambda f: isinstance(f.empty_form.instance, Box), formsets):
            for inline in formset:
                if inline.instance.pk is None:
                    continue
                contents = boxes.get(inline.instance)
                if contents is not None and fill_box(inline.instance, contents, inline.cleaned_data):
                    inline.instance.save()

    def get_urls(self):
        urls = super(OrderAdmin, self).get_urls()
        my_urls = [
            re_path(r'(\d+)/document/([a-z]+)/$', self.admin_site.admin_view(self.document), name='shop_order_document'),
            re_path(r'products/$', self.admin_site.admin_view(self.order_product_list), name='shop_order_product_list'),
            re_path(r'(\d+)/item/(\d+)/print_warranty_card/$', self.admin_site.admin_view(self.print_warranty_card), name='print-warranty-card'),
            re_path(r'(\d+)/combine/$', self.admin_site.admin_view(self.combine_form), name='shop_order_combine'),
            re_path(r'(\d+)/discount/$', self.admin_site.admin_view(self.discount_form), name='shop_order_discount'),
            re_path(r'(\d+)/yandex_delivery/$', self.admin_site.admin_view(self.yandex_delivery_form), name='shop_order_yandex_delivery'),
            re_path(r'(\d+)/yandex_delivery_estimate/$', self.admin_site.admin_view(self.yandex_delivery_estimate), name='shop_order_yandex_delivery_estimate'),
            re_path(r'(\d+)/beru_labels/$', self.admin_site.admin_view(self.beru_labels), name='shop_order_beru_labels'),
            re_path(r'(\d+)/unlock/$', self.admin_site.admin_view(self.unlock), name='shop_order_unlock'),
            re_path(r'sms/(\+\d+)/$', self.admin_site.admin_view(self.send_sms_form), name='shop_order_send_sms'),
        ]
        return my_urls + urls

    def action_form_page(self, request, form, title, action_title, **context):
        """ Page with the form of a custom view or an action, see admin/shop/custom_action_form.html for more of its context """
        return TemplateResponse(request, 'admin/shop/custom_action_form.html', {
            **self.admin_site.each_context(request),
            'cl': self,
            'opts': self.model._meta,
            'form': form,
            'title': title,
            'action_title': action_title,
            **context,
        })

    def popup_form(self, request, form_class, apply, title, action_title, initial=None):
        """
        Custom view with a form in a popup. When the form is valid, apply(form) does the work and returns the response,
        a message to show over an empty form, or None to show the form again with the errors it added. An exception
        it raises becomes an error of the form.
        """
        notices = None  # instead of those queued for other pages
        if request.method != 'POST':
            form = form_class(initial=initial)
            is_popup = request.GET.get('_popup', 0)
        else:
            form = form_class(request.POST)
            is_popup = request.POST.get('_popup', 0)
            if form.is_valid():
                try:
                    result = apply(form)
                    if isinstance(result, str):
                        notices = [result]
                        form = form_class()
                    elif result is not None:
                        return result
                except Exception as e:
                    form.errors['__all__'] = form.error_class([str(e)])
        return self.action_form_page(request, form, title, action_title, is_popup=is_popup, messages=notices)

    def document(self, request, id, template):
        if not request.user.is_staff:
            raise PermissionDenied
        order = Order.objects.get(pk=id)
        return render(request, 'shop/order/' + template + '.html', {
            'owner_info': getattr(settings, 'SHOP_OWNER_INFO', {}),
            'default_seller': Contractor.objects.filter(pk=config.sw_default_seller).first(),
            'order': order,
            'opts': self.model._meta,
        })

    def order_product_list_action(self, request, queryset):
        if not request.user.is_staff:
            raise PermissionDenied
        selected = request.POST.getlist(admin.helpers.ACTION_CHECKBOX_NAME)
        return HttpResponseRedirect("products/?orders=%s" % ",".join(selected))
    order_product_list_action.short_description = "Показать товары для выбранных заказов"

    def order_product_list(self, request):
        if not request.user.is_staff:
            raise PermissionDenied
        ids = request.GET.get('orders', '0')
        order_ids = None
        if ids != '0':
            order_ids = parse_ids(ids.split(','))
            ids = ','.join(map(str, order_ids))
        sort = request.GET.get('o')
        return render(request, 'admin/shop/order/products.html', {
            'title': 'Товары для заказов',
            'products': order_products(order_ids, sort),
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
                        'default_seller': Contractor.objects.filter(pk=config.sw_default_seller).first(),
                        'order': order,
                        'product': item.product,
                        'serial_number': serial_number,
                        'admin': True,
                        'batched': False
                    }
                    return TemplateResponse(request, 'shop/warrantycard/index.html', context)

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

        def combine(form):
            other_order = Order.objects.get(pk=form.cleaned_data['order_number'])
            if combine_orders(order, other_order):
                return close_popup()
            form.add_error('order_number', "Разные пользователи у заказов")
            return None

        return self.popup_form(request, OrderCombineForm, combine, "Укажите заказ для объединения", "Объеденить")

    def discount_form(self, request, id):
        if not request.user.is_staff:
            raise PermissionDenied
        order = Order.objects.get(pk=id)

        def discount(form):
            apply_discount(order, form.cleaned_data['discount'], form.cleaned_data['unit'])
            return close_popup()

        return self.popup_form(request, OrderDiscountForm, discount, "Укажите скидку", "Применить")

    def yandex_delivery_form(self, request, id):
        if not request.user.is_staff:
            raise PermissionDenied
        order = Order.objects.get(pk=id)

        def create_draft(form):
            unpacked = [item for item in order.items.all() if item.box is None]
            for item in unpacked:
                form.add_error(None, "{} не упакован в коробку".format(item.product.code))
            if unpacked:
                return None
            first_name, middle_name, last_name = split_name(order.name, form.cleaned_data['fio_last'])
            yd_order = create_delivery_draft_order(order.id, form.cleaned_data['warehouse'], first_name, middle_name, last_name)
            return close_popup('opener.dismissYandexDeliveryPopup(window, "%s", "%s");' % (Order.DELIVERY_YANDEX, yd_order))

        return self.popup_form(request, YandexDeliveryForm, create_draft, "Создать черновик заказа", "Создать",
                               initial={'fio': order.name})

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
            context['deliveries'] = delivery_options(results)
            context['result'] = results

        except Exception as e:
            context['error'] = str(e)

        return TemplateResponse(request, 'admin/shop/order/yandex_delivery_estimate.html', context)

    def beru_labels(self, request, arg):
        if not request.user.is_staff:
            raise PermissionDenied

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
            context['orders'] = beru_order_labels(orders)
        except Exception as e:
            context['error'] = getattr(e, 'message', str(e))

        return TemplateResponse(request, 'shop/order/beru_labels.html', context)
    beru_labels.short_description = "Печать наклеек Беру"

    def send_sms_form(self, request, phone):
        if not request.user.is_staff:
            raise PermissionDenied

        def send(form):
            message = form.cleaned_data['message']
            if message:
                send_message.delay(phone, message)
            return "Сообщение отправлено, закройте окно"

        return self.popup_form(request, SendSmsForm, send, "Укажите текст сообщения для %s" % str(phone), "Отправить")

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
        missing_contractors, missing_wirehouse, missing_wiring_date = missing_1c_data(queryset)
        if missing_contractors:
            self.message_user(request, "В заказах не указан контрагент: %s" % ', '.join(map(str, missing_contractors)), level=messages.ERROR)
        if missing_wirehouse:
            self.message_user(request, "В заказах не указан склад отгрузки: %s" % ', '.join(map(str, missing_wirehouse)), level=messages.ERROR)
        if missing_wiring_date:
            self.message_user(request, "В заказах не указана дата проводки: %s" % ', '.join(map(str, missing_wiring_date)), level=messages.ERROR)
        if not (missing_contractors or missing_wirehouse or missing_wiring_date):
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
            own = Supplier.objects.get(code=OWN_WAREHOUSE)
            supplier = Supplier.objects.get(pk=request.POST.get('supplier'))
            if request.POST.get('aux_supplier'):
                aux_supplier = Supplier.objects.get(pk=request.POST.get('aux_supplier'))
            else:
                aux_supplier = None
            selected = parse_ids(request.POST.getlist(admin.helpers.ACTION_CHECKBOX_NAME))
            products = allocate_stock(selected, own, supplier, aux_supplier)
            if not products:
                self.message_user(request, "Нет товаров для отгрузки у этого поставщика", level=messages.WARNING)
                return
            else:
                response = HttpResponse(stock_workbook(products, own, supplier, aux_supplier),
                                        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                response['Content-Disposition'] = 'attachment; filename={0}-{2}.xlsx; filename*=UTF-8\'\'{1}-{2}.xlsx'.format(
                    'stock',
                    quote(supplier.code),
                    datetime.date.today().isoformat())
                return response

        form = SelectSupplierForm(initial={'supplier': Supplier.objects.get(code=DEFAULT_SUPPLIER).pk})
        return self.action_form_page(request, form, "Выберите поставщика", "Сформировать выгрузку", queryset=queryset,
                                     is_popup=0, action='order_stock_action', action_name='show_stock')
    order_stock_action.short_description = "Выгрузка поставщику"

    def order_products_action(self, request, queryset):
        if not request.user.is_staff:
            raise PermissionDenied
        selected = parse_ids(request.POST.getlist(admin.helpers.ACTION_CHECKBOX_NAME))
        response = HttpResponse(products_workbook(selected), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
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
            # tags = parse_tag_input(request.POST.get('tags'))
            # for order in queryset:
            #     order.append_user_tags(tags)
            self.message_user(request, "НЕ(!!!)добавлен тег {} пользователям".format(queryset.count()))
            return HttpResponseRedirect(request.get_full_path())

        form = SelectTagForm(model=ShopUser)
        return self.action_form_page(request, form, "Укажите один или несколько тегов", "Добавить", queryset=queryset,
                                     is_popup=0, messages=None, action='order_set_user_tag_action', action_name='set_user_tag')
    order_set_user_tag_action.short_description = "Добавить тег покупателю"

    def order_act_action(self, request, queryset):
        if not request.user.is_staff:
            raise PermissionDenied
        wrong_status, already_acted = act_problems(queryset)
        if wrong_status:
            self.message_user(request, "Нельзя выписать акт по несобранным заказам: %s" % ', '.join(map(str, wrong_status)), level=messages.ERROR)
        elif already_acted:
            self.message_user(request, "Некоторые заказы уже описаны в других актах: %s" % ', '.join(map(str, already_acted)), level=messages.ERROR)
        else:
            act = make_act(queryset)
            return HttpResponseRedirect(reverse('admin:shop_act_change', args=[act.pk]))
    order_act_action.short_description = "Сформировать акт"
