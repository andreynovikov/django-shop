from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Prefetch, prefetch_related_objects
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponseRedirect
from django.template.defaultfilters import floatformat
from django.urls import reverse
from django.utils.html import format_html, format_html_join
from django.utils.safestring import mark_safe

from shop.models import Stock, Order, OrderItem


@staff_member_required
def goto_order(request):
    order_id = request.GET.get('order', None)
    if order_id is not None:
        try:
            order = Order.objects.get(pk=order_id)
            return HttpResponseRedirect(reverse('admin:shop_order_change', args=[order.id]))
        except Order.DoesNotExist:
            messages.add_message(request, messages.ERROR, 'Заказ №{} отсутствует'.format(order_id))
        except ValueError:
            messages.add_message(request, messages.WARNING, 'Укажите номер заказа')
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))


def check_permission(model_admin, request, obj=None, change=False):
    """ Raises PermissionDenied unless the user may view the objects of the admin, or change them when change is set """
    if change:
        permitted = model_admin.has_change_permission(request, obj)
    else:
        permitted = model_admin.has_view_permission(request, obj)
    if not permitted:
        raise PermissionDenied


def permitted_object(model_admin, request, object_id, change=False):
    """
    The object of a custom admin view. It comes from the admin's queryset, so staff limited to some sites don't get
    the objects of others, and needs the permission to view it, or to change it for a view that changes it.
    """
    obj = model_admin.get_object(request, object_id)
    if obj is None:
        raise Http404
    check_permission(model_admin, request, obj, change)
    return obj


def join_html(parts, separator=''):
    """ HTML of the parts one after another, escaping those that are not marked safe """
    return format_html_join(mark_safe(separator), '{}', ((part,) for part in parts))


# What product_stock_view() reads of a product. A list prefetches them for all its products, see ProductChangeList.
STOCK_PREFETCH = (Prefetch('stock_items', queryset=Stock.objects.select_related('supplier')), 'set_constituents')


def product_stock_view(product, order=None):
    """
    HTML of the product's stock for the admin: the quantity and correction at each supplier shown in orders, and in
    an order, how many other orders in progress hold the product, linked. A set shows the stock counted.
    """
    prefetch_related_objects([product], *STOCK_PREFETCH)  # nothing more when a list prefetched them
    parts = []
    if not product.set_constituents.all():
        stocks = sorted((stock for stock in product.stock_items.all() if stock.supplier.show_in_order),
                        key=lambda stock: (stock.supplier.order, stock.supplier.pk))
        if stocks:
            if order is None:
                parts.append(format_html('<span style="color: var(--link-hover-color)">{}</span><br/>', floatformat(product.num)))
            for stock in stocks:
                supplier = stock.supplier
                quantity = floatformat(stock.quantity)
                if stock.quantity == 0:
                    quantity = format_html('<span style="color: var(--error-fg)">{}</span>', quantity)
                correction = ''
                if stock.correction != 0.0:
                    added = stock.correction > 0.0
                    correction = format_html('<span class="sw-c" style="--c: {}" title="{}">{}{}</span>', '#090' if added else 'var(--error-fg)',
                                             stock.reason, '+' if added else '', floatformat(stock.correction))
                parts.append(format_html('{}:&nbsp;{}{}<br/>', supplier.code, quantity, correction))
        else:
            parts.append(mark_safe('<span style="color: var(--error-fg)">отсутствует</span><br/>'))
        if order:
            items = OrderItem.objects.filter(
                product=product,
                # the statuses that hold stock, as in Product.get_stocks()
                order__status__in=[Order.STATUS_NEW, Order.STATUS_ACCEPTED, Order.STATUS_COLLECTING, Order.STATUS_COLLECTED, Order.STATUS_DELIVERED_SHOP, Order.STATUS_SENT]
            ).exclude(order=order).values_list('order_id', 'quantity')
            if items:
                ordered = 0
                ids = [str(order.id)]
                for order_id, quantity in items:
                    ids.append(str(order_id))
                    ordered = ordered + quantity
                url = '%s?id__in=%s&status=all' % (reverse("admin:shop_order_changelist"), ','.join(ids))
                parts.append(format_html('<a href="{}" style="color: var(--link-hover-color)">Зак:&nbsp;{}<br/></a>', url, floatformat(ordered)))
    else:
        parts.append(floatformat(product.instock))
    return join_html(parts)
