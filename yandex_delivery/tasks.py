from urllib.request import Request, urlopen
from urllib.error import HTTPError
import json

import django.db
from celery import shared_task
from djconfig import config, reload_maybe

from shop.models import Order


class TaskFailure(Exception):
    pass


def create_delivery_draft_order(order_id, warehouse, first_name, middle_name, last_name):
    order = Order.objects.get(id=order_id)

    boxes = []
    count = 0
    for box in order.boxes.all():
        count += 1
        items = []
        for item in order.items.all():
            if item.box == box:
                items.append({
                    'externalId': item.product.code,
                    'name': item.product.title,
                    'price': str(item.cost),
                    'tax': 'NO_VAT',
                    'count': item.quantity
                })
        boxes.append({
            'externalId': '%d-%d' % (order.id, count),
            'dimensions': {
                'weight': box.weight,
                'width': int(box.width),
                'height': int(box.height),
                'length': int(box.length)
            },
            'items': items
        })

    data = {
        'senderId': config.sw_yd_sender,
        'externalId': str(order.id),
        'deliveryType': 'COURIER',
        'recipient': {
            'firstName': first_name,
            'middleName': middle_name,
            'lastName': last_name,
            'email': order.email,
            'address': {
                'locality': order.city,
                'street': order.address,
                'postalCode': order.postcode
            }
        },
        'cost': {
            'manualDeliveryForCustomer': str(order.delivery_price),
            'assessedValue': str(order.total),
            'fullyPrepaid': order.paid
        },
        'contacts': [
            {
                'type': 'RECIPIENT',
                'phone': order.phone,
                'firstName': first_name,
                'middleName': middle_name,
                'lastName': last_name
            },
        ],
        'shipment': {
            'type': 'WITHDRAW',
            'warehouseFrom': warehouse
        },
        'places': boxes
    }
    if order.paid:
        data['cost']['paymentMethod'] = 'PREPAID'

    import sys
    print(json.dumps(data), file=sys.stderr)
    data_encoded = json.dumps(data).encode('utf-8')
    url = 'https://api.delivery.yandex.ru/orders'
    headers = {
        'Authorization': 'OAuth {oauth_token}'.format(oauth_token=config.sw_yd_token),
        'Content-Type': 'application/json; charset=utf-8'
    }
    request = Request(url, data_encoded, headers, method='POST')
    try:
        response = urlopen(request)
        result = json.loads(response.read().decode('utf-8'))
        print(result, file=sys.stderr)
        return result
    except HTTPError as e:
        content = e.read()
        error = json.loads(content.decode('utf-8'))
        message = '{}: {}'.format(error.get('type', 'UNKNOWN'), error.get('message', 'Неизвестная ошибка взаимодействия с Яндекс.Доставка'))
        print(message, file=sys.stderr)
        raise RuntimeError(message) from e


@shared_task(bind=True, autoretry_for=(OSError, django.db.Error, json.decoder.JSONDecodeError), retry_backoff=3, retry_jitter=False)
def create_delivery_draft_order_task(self, order_id, warehouse, first_name, middle_name, last_name):
    try:
        reload_maybe()
        return create_delivery_draft_order(order_id, warehouse, first_name, middle_name, last_name)
    except HTTPError as e:
        raise self.retry(countdown=60 * 10, max_retries=12, exc=e)  # 10 minutes


def get_delivery_options(total, paid, warehouse, city, weight, width, height, length):
    data = {
        'senderId': config.sw_yd_sender,
        'to': {
            'location': city,
        },
        'dimensions': {
            'weight': weight,
            'width': int(width),
            'height': int(height),
            'length': int(length)
        },
        'cost': {
            'assessedValue': str(total),
            'itemsSum': str(total),
            'fullyPrepaid': paid
        },
        'shipment': {
            'type': 'WITHDRAW',
            'warehouseId': warehouse,
            'includeNonDefault': False
        }
    }

    import sys
    print(json.dumps(data), file=sys.stderr)
    data_encoded = json.dumps(data).encode('utf-8')
    url = 'https://api.delivery.yandex.ru/delivery-options'
    headers = {
        'Authorization': 'OAuth {oauth_token}'.format(oauth_token=config.sw_yd_token),
        'Content-Type': 'application/json; charset=utf-8'
    }
    request = Request(url, data_encoded, headers, method='PUT')
    try:
        response = urlopen(request)
        result = json.loads(response.read().decode('utf-8'))
        print(result, file=sys.stderr)
        return result
    except HTTPError as e:
        content = e.read()
        error = json.loads(content.decode('utf-8'))
        print(error, file=sys.stderr)
        message = '{}: {}'.format(error.get('type', 'UNKNOWN'), error.get('message', 'Неизвестная ошибка взаимодействия с Яндекс.Доставка'))
        print(message, file=sys.stderr)
        raise RuntimeError(message) from e
