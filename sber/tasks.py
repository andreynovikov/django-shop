import json
import logging
from urllib.request import Request, urlopen
from urllib.error import HTTPError

import django.db

from django.conf import settings
from django.utils import timezone

from celery import shared_task

from shop.models import Order


logger = logging.getLogger('sber')

SBER_MARKET = getattr(settings, 'SBER_MARKET', {})


class TaskFailure(Exception):
    pass


@shared_task(bind=True, autoretry_for=(OSError, django.db.Error, json.decoder.JSONDecodeError), retry_backoff=3, retry_jitter=False)
def confirm_sber_order(self, order_id):
    order = Order.objects.get(id=order_id)
    sber_order = order.delivery_tracking_number
    if not sber_order:
        raise TaskFailure('Order {} does not have sber order number'.format(order_id))

    items = []
    for item in order.items.all():
        items.append({
            'itemIndex': item.meta.get('itemIndex'),
            'offerId': item.product.id
        })

    data = {
        'data': {
            'token': SBER_MARKET.get('token', ''),
            'shipments': [{
                'shipmentId': sber_order,
                'orderCode': str(order.id),
                'items': items
            }]
        },
        'meta': {}
    }
    data_encoded = json.dumps(data).encode('utf-8')
    logger.info('>>> /order/confirm')
    logger.info(data_encoded)

    url = SBER_MARKET.get('api', '') + '/order/confirm'
    headers = {
        'Content-Type': 'application/json; charset=utf-8',
        'User-Agent': 'Mozilla/5.0'  # грёбаный Сбер считает, что Python-urllib - это попытка взлома!
    }
    request = Request(url, data_encoded, headers, method='POST')
    try:
        response = urlopen(request)
        result = json.loads(response.read().decode('utf-8'))
        status = result.get('data', {}).get('result', None)
        return '{}: {}'.format(order_id, status)
    except HTTPError as e:
        content = e.read()
        error = content.decode('utf-8')
        logger.error(error)
        order.status = Order.STATUS_PROBLEM
        if order.delivery_info:
            order.delivery_info = '\n'.join([order.delivery_info, error])
        else:
            order.delivery_info = error
        order.save()
        raise self.retry(countdown=60 * 10, max_retries=12, exc=e)  # 10 minutes


@shared_task(bind=True, autoretry_for=(OSError, django.db.Error, json.decoder.JSONDecodeError), retry_backoff=3, retry_jitter=False)
def reject_sber_order(self, order_id):
    order = Order.objects.get(id=order_id)
    sber_order = order.delivery_tracking_number
    if not sber_order:
        raise TaskFailure('Order {} does not have sber order number'.format(order_id))

    items = []
    for item in order.items.all():
        items.append({
            'itemIndex': item.meta.get('itemIndex'),
            'offerId': item.product.id
        })

    data = {
        'data': {
            'token': SBER_MARKET.get('token', ''),
            'shipments': [{
                'shipmentId': sber_order,
                'orderCode': str(order.id),
                'items': items
            }],
            'reason': {
                'type': 'OUT_OF_STOCK'
            }
        },
        'meta': {}
    }
    data_encoded = json.dumps(data).encode('utf-8')
    logger.info('>>> /order/reject')
    logger.info(data_encoded)

    url = SBER_MARKET.get('api', '') + '/order/reject'
    headers = {
        'Content-Type': 'application/json; charset=utf-8',
        'User-Agent': 'Mozilla/5.0'  # грёбаный Сбер считает, что Python-urllib - это попытка взлома!
    }
    request = Request(url, data_encoded, headers, method='POST')
    try:
        response = urlopen(request)
        result = json.loads(response.read().decode('utf-8'))
        status = result.get('data', {}).get('result', None)
        return '{}: {}'.format(order_id, status)
    except HTTPError as e:
        content = e.read()
        error = content.decode('utf-8')
        logger.error(error)
        order.status = Order.STATUS_PROBLEM
        if order.delivery_info:
            order.delivery_info = '\n'.join([order.delivery_info, error])
        else:
            order.delivery_info = error
        order.save()
        raise self.retry(countdown=60 * 10, max_retries=12, exc=e)  # 10 minutes


@shared_task(bind=True, autoretry_for=(OSError, django.db.Error, json.decoder.JSONDecodeError), retry_backoff=3, retry_jitter=False)
def notify_sber_order_packed(self, order_id):
    order = Order.objects.get(id=order_id)
    sber_order = order.delivery_tracking_number
    if not sber_order:
        raise TaskFailure('Order {} does not have sber order number'.format(order_id))

    items = []
    count = 0
    for box in order.boxes.all():
        count += 1
        for item in order.items.filter(box=box):
            items.append({
                'itemIndex': item.meta.get('itemIndex'),
                'boxes': [{
                    'boxIndex': count,
                    'boxCode': '{}*{}*{}'.format(SBER_MARKET.get('merchant_code', ''), order.id, count)
                }]
            })

    data = {
        'data': {
            'token': SBER_MARKET.get('token', ''),
            'shipments': [{
                'shipmentId': sber_order,
                'orderCode': str(order.id),
                'items': items
            }]
        },
        'meta': {}
    }
    data_encoded = json.dumps(data).encode('utf-8')
    logger.info('>>> /order/packing')
    logger.info(data_encoded)

    url = SBER_MARKET.get('api', '') + '/order/packing'
    headers = {
        'Content-Type': 'application/json; charset=utf-8',
        'User-Agent': 'Mozilla/5.0'  # грёбаный Сбер считает, что Python-urllib - это попытка взлома!
    }
    request = Request(url, data_encoded, headers, method='POST')
    try:
        response = urlopen(request)
        result = json.loads(response.read().decode('utf-8'))
        status = result.get('data', {}).get('result', None)
        return '{}: {}'.format(order_id, status)
    except HTTPError as e:
        content = e.read()
        error = content.decode('utf-8')
        logger.error(error)
        order.status = Order.STATUS_PROBLEM
        if order.delivery_info:
            order.delivery_info = '\n'.join([order.delivery_info, error])
        else:
            order.delivery_info = error
        order.save()
        raise self.retry(countdown=60 * 10, max_retries=12, exc=e)  # 10 minutes


@shared_task(bind=True, autoretry_for=(OSError, django.db.Error, json.decoder.JSONDecodeError), retry_backoff=3, retry_jitter=False)
def notify_sber_order_shipped(self, order_id):
    order = Order.objects.get(id=order_id)
    sber_order = order.delivery_tracking_number
    if not sber_order:
        raise TaskFailure('Order {} does not have sber order number'.format(order_id))

    boxes = []
    count = 0
    for box in order.boxes.all():
        count += 1
        boxes.append({
            'boxIndex': count,
            'boxCode': '{}*{}*{}'.format(SBER_MARKET.get('merchant_code', ''), order.id, count)
        })

    data = {
        'data': {
            'token': SBER_MARKET.get('token', ''),
            'shipments': [{
                'shipmentId': sber_order,
                'boxes': boxes,
                'shipping': {
                    'shippingDate': timezone.localtime(timezone.now()).replace(microsecond=0).isoformat()
                }
            }]
        },
        'meta': {}
    }
    data_encoded = json.dumps(data).encode('utf-8')
    logger.info('>>> /order/packing')
    logger.info(data_encoded)

    url = SBER_MARKET.get('api', '') + '/order/shipping'
    headers = {
        'Content-Type': 'application/json; charset=utf-8',
        'User-Agent': 'Mozilla/5.0'  # грёбаный Сбер считает, что Python-urllib - это попытка взлома!
    }
    request = Request(url, data_encoded, headers, method='POST')
    try:
        response = urlopen(request)
        result = json.loads(response.read().decode('utf-8'))
        status = result.get('data', {}).get('result', None)
        return '{}: {}'.format(order_id, status)
    except HTTPError as e:
        content = e.read()
        error = content.decode('utf-8')
        logger.error(error)
        order.status = Order.STATUS_PROBLEM
        if order.delivery_info:
            order.delivery_info = '\n'.join([order.delivery_info, error])
        else:
            order.delivery_info = error
        order.save()
        raise self.retry(countdown=60 * 10, max_retries=12, exc=e)  # 10 minutes
