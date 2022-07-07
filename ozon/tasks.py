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

    url = 'https://api-seller.ozon.ru/v3/posting/fbs/unfulfilled/list'
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
            "cutoff_from": week_ago.isoformat(),
            "cutoff_to": now.isoformat(),
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
