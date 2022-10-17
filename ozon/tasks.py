import json
import logging
from datetime import datetime, timedelta
from importlib import import_module
from urllib.request import Request, urlopen
from urllib.error import HTTPError

from decimal import Decimal

import django.db
from django.conf import settings
from django.contrib import auth
from django.utils import timezone

from celery import shared_task

from shop.models import Integration, Basket, Order, Product, ShopUser


logger = logging.getLogger('ozon')


class TaskFailure(Exception):
    pass


@shared_task(bind=True, autoretry_for=(OSError, django.db.Error, json.decoder.JSONDecodeError), retry_backoff=300, retry_jitter=False)
def get_unfulfilled_orders(self):
    integration = Integration.objects.get(utm_source='ozon')
    client_id = integration.settings.get('client_id', '')
    api_key = integration.settings.get('api_key', '')

    url = 'https://api-seller.ozon.ru/v3/posting/fbs/list'
    headers = {
        'Client-Id': client_id,
        'Api-Key': api_key,
        'Content-Type': 'application/json'
    }
    now = timezone.now().replace(microsecond=0)
    week_ago = now - timedelta(days=7)

    data = {
        "dir": "ASC",
        "filter": {
            "since": week_ago.isoformat(),
            "to": now.isoformat(),
            "status": "awaiting_packaging"
        },
        "limit": 1000,
        "offset": 0,
        "with": {
            "analytics_data": True,
            "financial_data": True
        }
    }
    data_encoded = json.dumps(data).encode('utf-8')
    request = Request(url, data_encoded, headers, method='POST')
    logger.info('<<< ' + request.full_url)
    logger.info(data_encoded)
    try:
        response = urlopen(request)
        result = json.loads(response.read().decode('utf-8'))
        num = 0
        user = ShopUser.objects.get(phone='0002')
        SessionStore = import_module(settings.SESSION_ENGINE).SessionStore
        session = SessionStore()
        session.cycle_key()
        session[auth.SESSION_KEY] = user._meta.pk.value_to_string(user)
        session[auth.BACKEND_SESSION_KEY] = settings.AUTHENTICATION_BACKENDS[0]
        session[auth.HASH_SESSION_KEY] = user.get_session_auth_hash()
        session.save()
        for posting in result.get('result', {}).get('postings', []):
            logger.debug(posting)
            posting_number = posting.get('posting_number', '')
            if not posting_number:
                continue

            order = Order.objects.filter(delivery_tracking_number=posting_number).first()
            if order is not None:
                continue
            basket = Basket.objects.create(session_id=session.session_key, utm_source='ozon', secondary=True)

            for ozon_item in posting.get('products', []):
                try:
                    sku = ozon_item.get('offer_id', '#NO_SKU#')
                    product = Product.objects.get(article=sku)
                    price = Decimal(ozon_item.get('price', '0'))
                    quantity = ozon_item.get('quantity', 0)
                    item, _ = basket.items.get_or_create(product=product)
                    item.quantity = quantity
                    if product.price > price:
                        item.ext_discount = product.price - price
                    item.save()
                except Exception as e:
                    logger.exception(e)
                    continue

            basket.save()
            order = Order.register(basket)

            is_express = posting.get('is_express', False)
            if is_express:
                order.delivery = Order.DELIVERY_EXPRESS

            full_address = []
            analytics_data = posting.get('analytics_data', {})
            region = analytics_data.get('region', None)
            if region:
                full_address.append(region)
            city = analytics_data.get('city', None)
            if city:
                if city != region:
                    full_address.append(city)
                order.city = city
            if full_address:
                order.address = ', '.join(full_address)

            date = analytics_data.get('delivery_date_end', '')
            if date:
                order.delivery_handing_date = datetime.strptime(date.split('T')[0], '%Y-%m-%d')

            date = posting.get('shipment_date', '')
            if date:
                order.delivery_dispatch_date = datetime.strptime(date.split('T')[0], '%Y-%m-%d')

            order.delivery_tracking_number = posting_number
            order.save()
            num = num + 1
        return num
    except HTTPError as e:
        content = e.read()
        error = json.loads(content.decode('utf-8'))
        logger.error(error)
        message = error.get('message', 'Неизвестная ошибка взаимодействия с Ozon!')
        raise TaskFailure(message) from e


@shared_task(bind=True, autoretry_for=(OSError, django.db.Error, json.decoder.JSONDecodeError), retry_backoff=300, retry_jitter=False)
def notify_product_stocks(self, product_id):
    integration = Integration.objects.get(utm_source='ozon')
    client_id = integration.settings.get('client_id', '')
    api_key = integration.settings.get('api_key', '')

    url = 'https://api-seller.ozon.ru/v2/products/stocks'
    headers = {
        'Client-Id': client_id,
        'Api-Key': api_key,
        'Content-Type': 'application/json'
    }
    product = Product.objects.get(pk=product_id)

    stock = min(10, int(product.get_stock(integration=integration)))
    express_stock = min(10, int(product.get_stock(integration=integration, express=True)))

    data = {
        "stocks": []
    }

    for warehouse in integration.settings.get('warehouses', []):
        if warehouse.get('is_express', False):
            warehouse_stock = express_stock
        else:
            warehouse_stock = stock
        data['stocks'].append({
            "offer_id": product.article,
            "stock": warehouse_stock,
            "warehouse_id": warehouse.get('id', 0)
        })

    data_encoded = json.dumps(data).encode('utf-8')
    request = Request(url, data_encoded, headers, method='POST')
    logger.info('<<< ' + request.full_url)
    logger.info(data_encoded)
    try:
        response = urlopen(request)
        result = json.loads(response.read().decode('utf-8'))
        logger.debug(result)
        """
        {'result': [
            {'warehouse_id': 22936068942000, 'product_id': 0, 'offer_id': 'в92086', 'updated': False, 'errors': [
                {'code': 'TOO_MANY_REQUESTS', 'message': 'too many requests'}
            ]},
            {'warehouse_id': 22933327211000, 'product_id': 297361812, 'offer_id': 'в92086', 'updated': True, 'errors': []}]}
        """
        return None
    except HTTPError as e:
        content = e.read()
        error = json.loads(content.decode('utf-8'))
        logger.error(error)
        message = error.get('message', 'Неизвестная ошибка взаимодействия с Ozon!')
        raise TaskFailure(message) from e
