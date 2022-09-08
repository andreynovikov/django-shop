from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.db import connection
from django.http import HttpResponseRedirect
from django.template.defaultfilters import floatformat
from django.urls import reverse
from django.utils.html import escape
from django.utils.safestring import mark_safe

from shop.models import Stock, Order


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
            for supplier in suppliers:
                stock = Stock.objects.get(product=product, supplier=supplier)
                result = result + ('%s:&nbsp;' % supplier.code)
                if stock.quantity == 0:
                    result = result + '<span style="color: #c00">'
                result = result + ('%s' % floatformat(stock.quantity))
                if stock.quantity == 0:
                    result = result + '</span>'
                if stock.correction != 0.0:
                    result = result + '<span style="color: '
                    if stock.correction > 0.0:
                        result = result + '#090'
                    else:
                        result = result + '#c00'
                    result = result + ('" title="%s">' % escape(stock.reason))
                    if stock.correction > 0.0:
                        result = result + '+'
                    result = result + ('%s</span>' % floatformat(stock.correction))
                result = result + '<br/>'
        else:
            result = '<span style="color: #f00">отсутствует</span><br/>'
        if order:
            cursor = connection.cursor()
            cursor.execute("""SELECT shop_orderitem.order_id, shop_orderitem.quantity AS quantity FROM shop_orderitem
                              INNER JOIN shop_order ON (shop_orderitem.order_id = shop_order.id) WHERE shop_order.status IN (0,1,4,64,256,1024)
                              AND shop_orderitem.product_id = %s AND shop_order.id != %s""", (product.id, order.id))
            if cursor.rowcount:
                ordered = 0
                ids = [str(order.id)]
                for row in cursor:
                    ids.append(str(row[0]))
                    ordered = ordered + int(row[1])
                url = '%s?id__in=%s&status=all' % (reverse("admin:shop_order_changelist"), ','.join(ids))
                result = result + '<a href="%s" style="color: #00c">Зак:&nbsp;%s<br/></a>' % (url, floatformat(ordered))
            cursor.close()
    else:
        result = floatformat(product.instock)
    return mark_safe(result)
