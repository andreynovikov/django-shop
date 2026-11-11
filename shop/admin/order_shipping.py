"""
Shipping orders: boxes they are packed in, Yandex Delivery, labels of Beru (Yandex Market), acts that hand orders
over to delivery, and what the export of shipped orders to 1C needs.
"""
import datetime
import re

from collections import defaultdict

from django.utils.safestring import mark_safe

import barcode

from shop.models import Order, Act, ActOrder

# Colors of pickup points on the map, presets of Yandex Maps
DELIVERY_COLORS = [
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


def split_name(name, last_name_last):
    """
    First, middle and last names of the recipient for Yandex Delivery. One word is the first name, two are the last
    and first names, three the last, first and middle names; with last_name_last, the last name goes last instead.
    More words, or none, raise ValueError.
    """
    fio = name.split()
    first_name = ''
    middle_name = ''
    last_name = ''
    if len(fio) == 1:  # looks like it's a name only
        first_name = fio[0]
    elif len(fio) == 2:  # looks like it's name with surname
        if last_name_last:
            fio.reverse()
        last_name, first_name = fio
    else:
        if last_name_last:
            first_name, middle_name, last_name = fio
        else:
            last_name, first_name, middle_name = fio
    return first_name, middle_name, last_name


def delivery_options(results):
    """
    Options of Yandex Delivery, by delivery type, for the map and the list: each with its services and cost,
    the color of its pickup points, and the hours when they are open or the courier comes
    """
    deliveries = {}
    i = 0
    for result in results:
        delivery = result['delivery']
        delivery_type = deliveries.get(delivery['type'], None)
        if delivery_type is None:
            delivery_type = []
            deliveries[delivery['type']] = delivery_type
        # shop_cost = delivery['costWithRules']
        required_services = []
        optional_services = []
        for service in result['services']:
            # if service['optional']:
            #     optional_services.append(service)
            # else:
            required_services.append(service)
            # shop_cost = shop_cost + service['cost']
        delivery['required_services'] = required_services
        delivery['optional_services'] = optional_services
        delivery['cost'] = result['cost']
        pickup_points = delivery.get('pickupPoints', [])
        if len(pickup_points):
            delivery['color'] = DELIVERY_COLORS[i]
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
    return deliveries


def code128_svg(code):
    """ Barcode for a label, an SVG element """
    svg = barcode.get_barcode_class('code128')(code).render(writer_options={'module_width': 0.5, 'module_height': 15, 'compress': True}).decode()
    return mark_safe(re.sub(r'^.*(?=<svg)', '', svg))


def beru_order_labels(orders):
    """
    Labels of orders of Beru (Yandex Market) for each of their boxes, as Beru knows them, with barcodes of
    the order numbers here and at Beru, and of the boxes
    """
    from beru.tasks import get_beru_labels_data

    labels = []
    for order in orders:
        beru_order = get_beru_labels_data(order.id)
        beru_order_id = str(beru_order.get('orderId', 0))

        boxes = order.boxes.all()
        count = 0
        shipments = []
        for label in beru_order.get('parcelBoxLabels', []):
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
            'beru_order': beru_order,
            'order': order,
            'beru_barcode': code128_svg(beru_order_id),
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
