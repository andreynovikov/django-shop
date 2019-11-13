from urllib.request import Request, urlopen
from urllib.error import HTTPError
import json

import django.db
from celery import shared_task
from djconfig import config, reload_maybe

from shop.models import Order


class TaskFailure(Exception):
    pass


@shared_task(bind=True, autoretry_for=(OSError, django.db.Error), retry_backoff=3, retry_jitter=False)
def notify_beru_order_status(self, order_id, status, substatus):
    order = Order.objects.get(id=order_id)
    beru_order = order.delivery_tracking_number
    if not beru_order:
        raise TaskFailure('Order {} does not have beru order number'.format(order_id))

    reload_maybe()

    if status == 'PROCESSING' and substatus == 'READY_TO_SHIP':
        beru_order = get_beru_order_details(order_id)
        beru_product_ids = {item['offerId']: item['id'] for item in beru_order.get('items', [])}
        boxes = []
        count = 0
        for box in order.boxes.all():
            count += 1
            items = []
            for item in order.items.all():
                if item.box == box:
                    items.append({
                        'id': beru_product_ids[item.product.article],
                        'count': item.quantity
                    })
            boxes.append({
                'fulfilmentId': '%d-%d' % (order.id, count),
                'weight': int(box.weight * 1000),
                'width': int(box.width),
                'height': int(box.height),
                'depth': int(box.length),
                'items': items
            })
        data = {'boxes': boxes}
        import sys
        print(json.dumps(data), file=sys.stderr)
        data_encoded = json.dumps(data).encode('utf-8')
        shipments = beru_order.get('delivery', {}).get('shipments', [])
        if not shipments:
            raise self.retry(countdown=60 * 60, max_retries=12)  # 60 minutes
        shipment_id = str(shipments[0].get('id', 0))
        beru_order = str(beru_order.get('id', 0))
        url = 'https://api.partner.market.yandex.ru/v2/campaigns/{campaignId}/orders/{orderId}/delivery/shipments/{shipmentId}/boxes.[format]json'.format(campaignId=config.sw_beru_campaign, orderId=beru_order, shipmentId=shipment_id)
        headers = {
            'Authorization': 'OAuth oauth_token="{oauth_token}", oauth_client_id="{oauth_application}"'.format(oauth_token=config.sw_beru_token, oauth_application=config.sw_beru_application),
            'Content-Type': 'application/json; charset=utf-8'
        }
        request = Request(url, data_encoded, headers, method='PUT')
        try:
            response = urlopen(request)
            result = json.loads(response.read().decode('utf-8'))
            boxes_status = result.get('status', 'ERROR')
            if boxes_status != 'OK':
                raise self.retry(countdown=60 * 10, max_retries=12)  # 10 minutes
        except HTTPError as e:
            content = e.read()
            error = json.loads(content.decode('utf-8'))
            message = error.get('error', {}).get('message', 'Неизвестная ошибка взаимодействия с Беру!')
            order.status = Order.STATUS_PROBLEM
            if order.delivery_info:
                order.delivery_info = '\n'.join([order.delivery_info, message])
            else:
                order.delivery_info = message
            order.save()
            raise self.retry(countdown=60 * 10, max_retries=12, exc=e)  # 10 minutes

    data = {"order": {"status": status, "substatus": substatus}}
    data_encoded = json.dumps(data).encode('utf-8')

    url = 'https://api.partner.market.yandex.ru/v2/campaigns/{campaignId}/orders/{orderId}/status.json'.format(campaignId=config.sw_beru_campaign, orderId=beru_order)
    headers = {
        'Authorization': 'OAuth oauth_token="{oauth_token}", oauth_client_id="{oauth_application}"'.format(oauth_token=config.sw_beru_token, oauth_application=config.sw_beru_application),
        'Content-Type': 'application/json; charset=utf-8'
    }
    request = Request(url, data_encoded, headers, method='PUT')
    try:
        response = urlopen(request)
        result = json.loads(response.read().decode('utf-8'))
        beru_order = result.get('order', {})
        order_id = str(beru_order.get('id', 0))
        status = beru_order.get('status', 'PROCESSING')
        substatus = beru_order.get('substatus', '')
        return '{}: {} {}'.format(order_id, status, substatus)
    except HTTPError as e:
        content = e.read()
        """
        {"error":{"code":400,"message":"status update is not allowed if there are items unassigned to boxes"},"errors":[{"code":"BAD_REQUEST","message":"status update is not allowed if there are items unassigned to boxes"}],"status":"ERROR"}
        """
        error = json.loads(content.decode('utf-8'))
        message = error.get('error', {}).get('message', 'Неизвестная ошибка взаимодействия с Беру!')
        order.status = Order.STATUS_PROBLEM
        if order.delivery_info:
            order.delivery_info = '\n'.join([order.delivery_info, message])
        else:
            order.delivery_info = message
        order.save()
        raise self.retry(countdown=60 * 10, max_retries=12, exc=e)  # 10 minutes


def get_beru_order_details(order_id):
    order = Order.objects.get(id=order_id)
    beru_order = order.delivery_tracking_number
    if not beru_order:
        raise TaskFailure('Order {} does not have beru order number'.format(order_id))

    reload_maybe()

    url = 'https://api.partner.market.yandex.ru/v2/campaigns/{campaignId}/orders/{orderId}.json'.format(campaignId=config.sw_beru_campaign, orderId=beru_order)
    headers = {
        'Authorization': 'OAuth oauth_token="{oauth_token}", oauth_client_id="{oauth_application}"'.format(oauth_token=config.sw_beru_token, oauth_application=config.sw_beru_application)
    }
    request = Request(url, None, headers)
    try:
        response = urlopen(request)
        result = json.loads(response.read().decode('utf-8'))
        import sys
        print(result, file=sys.stderr)
        return result.get('order', {})
    except HTTPError as e:
        content = e.read()
        """
        {"error":{"code":400,"message":"status update is not allowed if there are items unassigned to boxes"},"errors":[{"code":"BAD_REQUEST","message":"status update is not allowed if there are items unassigned to boxes"}],"status":"ERROR"}
        """
        error = json.loads(content.decode('utf-8'))
        message = error.get('error', {}).get('message', 'Неизвестная ошибка взаимодействия с Беру!')
        raise TaskFailure(message) from e
