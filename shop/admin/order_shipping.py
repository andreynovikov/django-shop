"""
Shipping orders: boxes they are packed in, labels of Yandex.Market orders, acts that hand orders
over to delivery, and what the export of shipped orders to 1C needs.
"""
import re

from collections import defaultdict

from django.utils.safestring import mark_safe

import barcode

from shop.models import Order, Act, ActOrder


def measure_boxes(packed):
    """
    What the items packed in each box add up to, from (box, product, quantity) of the items: their count and weight,
    and dimensions of the product, which are the box's when it holds a single item
    """
    boxes = defaultdict(dict)
    for box, product, quantity in packed:
        contents = boxes[box]
        contents['count'] = contents.get('count', 0) + quantity
        contents['weight'] = contents.get('weight', 0) + product.prom_weight * quantity
        contents['length'] = product.length
        contents['width'] = product.width
        contents['height'] = product.height
    return boxes


def fill_box(box, contents, entered):
    """
    Fills in the box's weight, and its dimensions when it holds a single item, where they were entered as zero,
    from its contents measured by measure_boxes(). Returns whether anything changed.
    """
    changed = False
    if entered['weight'] == 0:
        box.weight = contents['weight']
        changed = True
    if contents['count'] == 1:
        for dimension in ['length', 'width', 'height']:
            if entered[dimension] == 0:
                setattr(box, dimension, contents[dimension])
                changed = True
    return changed


def code128_svg(code):
    """ Barcode for a label, an SVG element """
    svg = barcode.get_barcode_class('code128')(code).render(writer_options={'module_width': 0.5, 'module_height': 15, 'compress': True}).decode()
    return mark_safe(re.sub(r'^.*(?=<svg)', '', svg))


def ym_order_labels(orders):
    """
    Labels of Yandex.Market orders for each of their boxes, as the Market knows them, with barcodes of
    the order numbers here and at the Market, and of the boxes
    """
    from ym.tasks import get_labels_data

    labels = []
    for order in orders:
        market_order = get_labels_data(order.id)
        market_order_id = str(market_order.get('orderId', 0))

        boxes = order.boxes.all()
        count = 0
        shipments = []
        for label in market_order.get('parcelBoxLabels', []):
            box = boxes[count]
            count += 1
            code = label.get('fulfilmentId', '')
            shipments.append({
                'id': code,
                'code': box.code,
                'place': label.get('place', ''),
                'barcode': code128_svg(code),
                'products': box.products.all(),
                'weight': label.get('weight', ''),
                'delivery_service_name': label.get('deliveryServiceName', '').replace('INDIVIDUAL_ENTREPRENEURSHIP', 'ИП'),
                'delivery_service_id': label.get('deliveryServiceId', ''),
                'supplier_name': label.get('supplierName', '')
            })

        labels.append({
            'market_order': market_order,
            'order': order,
            'market_barcode': code128_svg(market_order_id),
            'barcode': code128_svg(str(order.id)),
            'shipments': shipments
        })
    return labels


def act_problems(orders):
    """ Orders that can't go in an act: ids of those not collected, and of those in another act already """
    wrong_status = set()
    already_acted = set()
    for order in orders:
        if order.status != Order.STATUS_COLLECTED:
            wrong_status.add(order.id)
        if order.acts.exists():
            already_acted.add(order.id)
    return wrong_status, already_acted


def make_act(orders):
    """ Act that hands the orders over to delivery: they become sent. See act_problems() for those that can't. """
    act = Act()
    act.save()
    # act.orders.add(*queryset) - will be available in Django 2.2
    for order in orders:
        ActOrder.objects.create(act=act, order=order)
    for order in orders:  # we do it in separate loops to correctly handle errors
        order.status = Order.STATUS_SENT
        order.save()
    return act


def missing_1c_data(orders):
    """ What the export to 1C needs and the orders lack: ids of those without contractors, without the warehouse, and without the wiring date """
    missing_contractors = set()
    missing_wirehouse = set()
    missing_wiring_date = set()
    for order in orders:
        if not order.buyer or not order.seller:
            missing_contractors.add(order.id)
        if not order.wirehouse:
            missing_wirehouse.add(order.id)
        if not order.wiring_date:
            missing_wiring_date.add(order.id)
    return missing_contractors, missing_wirehouse, missing_wiring_date
