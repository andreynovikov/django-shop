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
        # order = Order.objects.get(delivery_tracking_number=order_id)
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
        raise TaskFailure(e)
        # raise self.retry(countdown=60 * 10, max_retries=12, exc=e)  # 10 minutes
