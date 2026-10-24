from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponseRedirect
from django.template.defaultfilters import floatformat
from django.urls import reverse
from django.utils.html import escape
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


def product_stock_view(product, order=None):
    result = ''
    if product.constituents.count() == 0:
        suppliers = product.stock.filter(show_in_order=True).order_by('order')
        if suppliers.exists():
            if order is None:
                result = '<span style="color: var(--link-hover-color)">%s</span><br/>' % floatformat(product.num)
            for supplier in suppliers:
                stock = Stock.objects.get(product=product, supplier=supplier)
                result = result + ('%s:&nbsp;' % supplier.code)
                if stock.quantity == 0:
                    result = result + '<span style="color: var(--error-fg)">'
                result = result + ('%s' % floatformat(stock.quantity))
                if stock.quantity == 0:
                    result = result + '</span>'
                if stock.correction != 0.0:
                    result = result + '<span style="color: '
                    if stock.correction > 0.0:
                        result = result + '#090'
                    else:
                        result = result + 'var(--error-fg)'
                    result = result + ('" title="%s">' % escape(stock.reason))
                    if stock.correction > 0.0:
                        result = result + '+'
                    result = result + ('%s</span>' % floatformat(stock.correction))
                result = result + '<br/>'
        else:
            result = '<span style="color: var(--error-fg)">отсутствует</span><br/>'
        if order:
            items = OrderItem.objects.filter(
                product=product,
                order__status__in=[Order.STATUS_NEW, Order.STATUS_ACCEPTED, Order.STATUS_COLLECTING, Order.STATUS_COLLECTED, Order.STATUS_DELIVERED_SHOP, Order.STATUS_SENT]
            ).exclude(order=order).values_list('order_id', 'quantity')
            if items:
                ordered = 0
                ids = [str(order.id)]
                for order_id, quantity in items:
                    ids.append(str(order_id))
                    ordered = ordered + quantity
                url = '%s?id__in=%s&status=all' % (reverse("admin:shop_order_changelist"), ','.join(ids))
                result = result + '<a href="%s" style="color: var(--link-hover-color)">Зак:&nbsp;%s<br/></a>' % (url, floatformat(ordered))
    else:
        result = floatformat(product.instock)
    return mark_safe(result)
