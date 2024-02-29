import json
import logging
from datetime import datetime
from urllib.request import Request, urlopen
from urllib.error import HTTPError

import django.db
from django.db.models import Sum, F, Q

from celery import shared_task

from sewingworld.tasks import PRIORITY_IDLE

from shop.models import Integration, Order, Product


logger = logging.getLogger('beru')


class TaskFailure(Exception):
    pass


@shared_task(bind=True, autoretry_for=(OSError, django.db.Error, json.decoder.JSONDecodeError), retry_backoff=3, retry_jitter=False)
def notify_beru_order_status(self, order_id, status, substatus):
    order = Order.objects.get(id=order_id)

    beru_order = get_beru_order_details(order_id)
    beru_status = beru_order.get('status', 'PROCESSING')
    beru_substatus = beru_order.get('substatus', '')
    if status == beru_status and substatus == beru_substatus:
        # do not notify Beru if status already set (Beru raises error in that case)
        return '{}: {} {} (already set)'.format(order_id, status, substatus)

    campaign_id = order.integration.settings.get('ym_campaign', '')
    oauth_application = order.integration.settings.get('application', '')
    oauth_token = order.integration.settings.get('oauth_token', '')

    beru_order_id = str(beru_order.get('id', 0))
    if status == 'PROCESSING' and substatus == 'READY_TO_SHIP':
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
                'fulfilmentId': '%s-%d' % (beru_order_id, count),
                'weight': int(box.weight * 1000),
                'width': int(box.width),
                'height': int(box.height),
                'depth': int(box.length),
                'items': items
            })
        data = {'boxes': boxes}
        data_encoded = json.dumps(data).encode('utf-8')
        shipments = beru_order.get('delivery', {}).get('shipments', [])
        if not shipments:
            raise self.retry(countdown=60 * 60, max_retries=12)  # 60 minutes
        shipment_id = str(shipments[0].get('id', 0))
        url = 'https://api.partner.market.yandex.ru/v2/campaigns/{campaignId}/orders/{orderId}/delivery/shipments/{shipmentId}/boxes.json'.format(campaignId=campaign_id, orderId=beru_order_id, shipmentId=shipment_id)
        headers = {
            'Authorization': 'OAuth oauth_token="{oauth_token}", oauth_client_id="{oauth_application}"'.format(oauth_token=oauth_token, oauth_application=oauth_application),
            'Content-Type': 'application/json; charset=utf-8'
        }
        request = Request(url, data_encoded, headers, method='PUT')
        logger.info('<<< ' + request.full_url)
        logger.info(data_encoded)
        try:
            response = urlopen(request)
            result = json.loads(response.read().decode('utf-8'))
            boxes_status = result.get('status', 'ERROR')
            if boxes_status != 'OK':
                message = result.get('errors', [{}])[0].get('message', None)
                if message is not None:
                    order.status = Order.STATUS_PROBLEM
                    if order.delivery_info:
                        order.delivery_info = '\n'.join([order.delivery_info, message])
                    else:
                        order.delivery_info = message
                    order.save()
                raise self.retry(countdown=60 * 10, max_retries=12)  # 10 minutes
        except HTTPError as e:
            content = e.read()
            logger.error(content)
            """
            INFO <<< https://api.partner.market.yandex.ru/v2/campaigns/22478010/orders/168524598/delivery/shipments/163754467/boxes.json
            INFO b'{"boxes": [{"fulfilmentId": "168524598-1", "weight": 4200, "width": 27, "height": 33, "depth": 48, "items": [{"id": 248335221, "count": 1}]}]}'
            ERROR b'{"status":"ERROR","errors":[{"code":"BAD_REQUEST","message":"You could not change boxes for order 168524598 in this status PROCESSING (SHIPPED)"}]}'
            """
            error = json.loads(content.decode('utf-8'))
            message = error.get('errors', [{}])[0].get('message', 'Неизвестная ошибка взаимодействия с Беру!')
            order.status = Order.STATUS_PROBLEM
            if order.delivery_info:
                order.delivery_info = '\n'.join([order.delivery_info, message])
            else:
                order.delivery_info = message
            order.save()
            raise self.retry(countdown=60 * 10, max_retries=12, exc=Exception(content))  # 10 minutes

    data = {"order": {"status": status, "substatus": substatus}}
    data_encoded = json.dumps(data).encode('utf-8')

    url = 'https://api.partner.market.yandex.ru/v2/campaigns/{campaignId}/orders/{orderId}/status.json'.format(campaignId=campaign_id, orderId=beru_order_id)
    headers = {
        'Authorization': 'OAuth oauth_token="{oauth_token}", oauth_client_id="{oauth_application}"'.format(oauth_token=oauth_token, oauth_application=oauth_application),
        'Content-Type': 'application/json; charset=utf-8'
    }
    request = Request(url, data_encoded, headers, method='PUT')
    logger.info('<<< ' + request.full_url)
    logger.info(data_encoded)
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
        logger.error(content)
        """
        {"error":{"code":400,"message":"status update is not allowed if there are items unassigned to boxes"},"errors":[{"code":"BAD_REQUEST","message":"status update is not allowed if there are items unassigned to boxes"}],"status":"ERROR"}
        """
        error = json.loads(content.decode('utf-8'))
        message = error.get('errors', [{}])[0].get('message', 'Неизвестная ошибка взаимодействия с Беру!')
        order.status = Order.STATUS_PROBLEM
        if order.delivery_info:
            order.delivery_info = '\n'.join([order.delivery_info, message])
        else:
            order.delivery_info = message
        order.save()
        raise self.retry(countdown=60 * 10, max_retries=12, exc=Exception(content))  # 10 minutes


def get_beru_order_details(order_id):
    order = Order.objects.get(id=order_id)
    beru_order = order.delivery_tracking_number
    if not beru_order:
        raise TaskFailure('Order {} does not have beru order number'.format(order_id))

    campaign_id = order.integration.settings.get('ym_campaign', '')
    oauth_application = order.integration.settings.get('application', '')
    oauth_token = order.integration.settings.get('oauth_token', '')

    url = 'https://api.partner.market.yandex.ru/v2/campaigns/{campaignId}/orders/{orderId}.json'.format(campaignId=campaign_id, orderId=beru_order)
    headers = {
        'Authorization': 'OAuth oauth_token="{oauth_token}", oauth_client_id="{oauth_application}"'.format(oauth_token=oauth_token, oauth_application=oauth_application)
    }
    request = Request(url, None, headers)
    logger.info('<<< ' + request.full_url)
    try:
        response = urlopen(request)
        result = json.loads(response.read().decode('utf-8'))
        logger.debug(result)
        return result.get('order', {})
    except HTTPError as e:
        content = e.read()
        error = json.loads(content.decode('utf-8'))
        logger.error(error)
        message = error.get('errors', [{}])[0].get('message', 'Неизвестная ошибка взаимодействия с Беру!')
        raise TaskFailure(message) from e


def get_beru_labels_data(order_id):
    order = Order.objects.get(id=order_id)
    beru_order = order.delivery_tracking_number
    if not beru_order:
        raise TaskFailure('Order {} does not have beru order number'.format(order_id))

    campaign_id = order.integration.settings.get('ym_campaign', '')
    oauth_application = order.integration.settings.get('application', '')
    oauth_token = order.integration.settings.get('oauth_token', '')

    url = 'https://api.partner.market.yandex.ru/v2/campaigns/{campaignId}/orders/{orderId}/delivery/labels/data.json'.format(campaignId=campaign_id, orderId=beru_order)
    headers = {
        'Authorization': 'OAuth oauth_token="{oauth_token}", oauth_client_id="{oauth_application}"'.format(oauth_token=oauth_token, oauth_application=oauth_application)
    }
    request = Request(url, None, headers)
    logger.info('<<< ' + request.full_url)
    try:
        response = urlopen(request)
        result = json.loads(response.read().decode('utf-8'))
        logger.debug(result)
        return result.get('result', {})
    except HTTPError as e:
        content = e.read()
        error = json.loads(content.decode('utf-8'))
        logger.error(error)
        message = error.get('errors', [{}])[0].get('message', 'Неизвестная ошибка взаимодействия с Беру!')
        raise TaskFailure(message) from e


@shared_task(bind=True, autoretry_for=(OSError, django.db.Error, json.decoder.JSONDecodeError), rate_limit='1/s', retry_backoff=300, retry_jitter=False)
def notify_beru_product_stocks(self, products, account):
    integration = Integration.objects.get(utm_source=account)

    campaign_id = integration.settings.get('ym_campaign', '')
    oauth_application = integration.settings.get('application', '')
    oauth_token = integration.settings.get('oauth_token', '')

    url = 'https://api.partner.market.yandex.ru/campaigns/{campaignId}/offers/stocks'.format(campaignId=campaign_id)
    headers = {
        'Authorization': 'OAuth oauth_token="{oauth_token}", oauth_client_id="{oauth_application}"'.format(oauth_token=oauth_token, oauth_application=oauth_application),
        'Content-Type': 'application/json'
    }

    warehouseId = integration.settings.get('warehouse_id', '')
    updatedAt = datetime.utcnow().replace(microsecond=0).isoformat() + '+00:00'

    skus = []

    for product in Product.objects.filter(pk__in=products):
        skus.append({
            'sku': product.article,
            'warehouseId': int(warehouseId),
            'items': [
                {
                    'type': 'FIT',
                    'count': max(int(product.get_stock(integration=integration)), 0),
                    'updatedAt': updatedAt
                }
            ]
        })

    data = {'skus': skus}
    data_encoded = json.dumps(data).encode('utf-8')
    request = Request(url, data_encoded, headers, method='PUT')
    logger.info('<<< ' + request.full_url)
    logger.info(data_encoded)
    try:
        response = urlopen(request)
        result = json.loads(response.read().decode('utf-8'))
        return result
    except HTTPError as e:
        content = e.read()
        error = json.loads(content.decode('utf-8'))
        logger.error(error)
        message = error.get('errors', [{}])[0].get('message', 'Неизвестная ошибка взаимодействия с Беру!')
        raise TaskFailure(message) from e


@shared_task(bind=True, autoretry_for=(OSError, django.db.Error, json.decoder.JSONDecodeError), retry_backoff=300, retry_jitter=False)
def notify_beru_integration_stocks(self):
    for integration in Integration.objects.filter(settings__has_key='ym_campaign'):
        if integration.settings.get('warehouse_id', '') != '':
            products = Product.objects.order_by().filter(integration=integration)

            if integration.output_available:
                products = products.annotate(
                    quantity=Sum('stock_item__quantity', filter=Q(stock_item__supplier__integration=integration)),
                    correction=Sum('stock_item__correction', filter=Q(stock_item__supplier__integration=integration)),
                    available=F('quantity') + F('correction')
                ).filter(available__gt=0)

            products = list(products.values_list('id', flat=True).distinct())

            notify_beru_product_stocks.s(products, integration.utm_source).apply_async(priority=PRIORITY_IDLE)
