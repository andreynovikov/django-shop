"""
Products of orders and where to take them: the list to collect orders by, and spreadsheets for suppliers
to ship what the shop's own warehouse lacks.
"""
import io

from decimal import Decimal, ROUND_UP

from django.db.models import F, Sum
from django.template.defaultfilters import floatformat

import xlsxwriter

from shop.models import Order, OrderItem, Stock, Supplier

OWN_WAREHOUSE = 'Ур'  # code of the shop's warehouse, taken from first
DEFAULT_SUPPLIER = 'С3'  # code of the supplier offered first

# Columns of the product list to sort by, as the list's links number them
PRODUCT_LIST_SORT = {
    '1': 'product_id',
    '2': 'article',
    '3': 'partnumber',
    '4': 'title',
    '5': 'order_id',
    '6': 'order_status',
    '7': 'total_quantity',
}


def order_products(order_ids, sort):
    """
    Products of the orders, all orders when order_ids is None: a row for each product of each order with its quantity,
    status of the order, and stock of the suppliers shown in orders, in HTML
    """
    suppliers = Supplier.objects.filter(show_in_order=True)
    items = OrderItem.objects.all()
    if order_ids is not None:
        items = items.filter(order__in=order_ids)
    items = items.values(
        'product_id',
        'order_id',
        article=F('product__article'),
        partnumber=F('product__partnumber'),
        title=F('product__title'),
        comment_packer=F('product__comment_packer'),
        order_status=F('order__status'),
    ).annotate(total_quantity=Sum('quantity')).order_by(PRODUCT_LIST_SORT.get(sort, 'title'))
    products = []
    for product in items:
        product['quantity'] = product.pop('total_quantity')
        product['order_status_value'] = dict(Order.STATUS_CHOICES)[product['order_status']]
        product['order_status_color'] = dict(Order.STATUS_COLORS)[product['order_status']]
        stock = ''
        stock_items = Stock.objects.filter(product_id=product['product_id'], supplier__in=suppliers) \
            .select_related('supplier').order_by('supplier__order')
        if stock_items:
            for stock_item in stock_items:
                stock = stock + ('%s:&nbsp;' % stock_item.supplier.code)
                if stock_item.quantity == 0:
                    stock = stock + '<span style="color: #c00">'
                stock = stock + ('%s' % floatformat(stock_item.quantity))
                if stock_item.quantity == 0:
                    stock = stock + '</span>'
                stock = stock + '<br/>'
        else:
            stock = '<span style="color: #ff0000">отсутствует</span>'
        product['stock'] = stock
        products.append(product)
    return products


def allocate_stock(order_ids, own, supplier, aux_supplier=None):
    """
    Splits the products of the orders between warehouses: the shop's own one first, then the supplier, then
    the auxiliary supplier. A row for each product has its article and quantity, and how much to take: 'own',
    'stock' from the supplier, 'aux_stock', and 'missing' what none of them has.
    """
    items = OrderItem.objects.filter(order__in=order_ids).values(
        'product_id',
        article=F('product__article'),
    ).annotate(total_quantity=Sum('quantity')).order_by('article')
    products = []
    suppliers = [own.id, supplier.id]
    if aux_supplier:
        suppliers.append(aux_supplier.id)
    for product in items:
        product['quantity'] = product.pop('total_quantity')
        stock_items = Stock.objects.filter(
            product_id=product['product_id'],
            supplier__in=suppliers
        ).values_list('supplier_id', 'quantity', 'correction')
        quantity = float(product['quantity'])
        available = 0
        stock = 0
        aux_stock = 0
        for supplier_id, stock_quantity, correction in stock_items:
            if supplier_id == own.id:
                available = stock_quantity + correction
            if supplier_id == supplier.id:
                stock = stock_quantity + correction
            if aux_supplier and supplier_id == aux_supplier.id:
                aux_stock = stock_quantity + correction
        if available < quantity:
            product['own'] = Decimal(available).quantize(Decimal('1'), rounding=ROUND_UP)
            if stock > 0:
                taken = min(stock, quantity - available)
                available += taken
                product['stock'] = Decimal(taken).quantize(Decimal('1'), rounding=ROUND_UP)
            if aux_stock > 0 and available < quantity:
                taken = min(aux_stock, quantity - available)
                available += taken
                product['aux_stock'] = Decimal(taken).quantize(Decimal('1'), rounding=ROUND_UP)
            if available < quantity:
                product['missing'] = quantity - available
        else:
            product['own'] = product['quantity']
        products.append(product)
    return products


def stock_workbook(products, own, supplier, aux_supplier=None):
    """ Spreadsheet of allocate_stock(): a sheet for each warehouse with articles and quantities, and one of what is missing """
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
    sheet = workbook.add_worksheet(own.name)
    idx = 0
    for product in products:
        own_stock = product.get('own', None)
        if own_stock and own_stock > 0:
            sheet.write(idx, 0, product['article'])
            sheet.write(idx, 1, product['own'])
            idx += 1
    if any(product.get('missing') for product in products):
        sheet = workbook.add_worksheet('Нет на складах')
        idx = 0
        for product in products:
            missing = product.get('missing', None)
            if missing:
                sheet.write(idx, 0, product['article'])
                sheet.write(idx, 1, missing)
                idx += 1
    workbook.close()
    return output.getvalue()


def products_workbook(order_ids):
    """ Spreadsheet of the products of the orders: articles and quantities """
    products = OrderItem.objects.filter(order__in=order_ids).values(
        'product_id',
        article=F('product__article'),
    ).annotate(total_quantity=Sum('quantity')).order_by()
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output)
    sheet = workbook.add_worksheet('Products')
    for idx, product in enumerate(products):
        sheet.write(idx, 0, product['article'])
        sheet.write(idx, 1, product['total_quantity'])
    workbook.close()
    return output.getvalue()
