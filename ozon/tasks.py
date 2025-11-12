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
from django.contrib.sites.models import Site
from django.utils import timezone

from celery import shared_task

from sewingworld.tasks import PRIORITY_IDLE

from shop.models import Integration, Basket, Order, Product, ProductIntegration, ShopUser

logger = logging.getLogger('ozon')
SITE_OZON = Site.objects.get(domain='ozon.ru')

class TaskFailure(Exception):
    pass


@shared_task(bind=True, autoretry_for=(OSError, django.db.Error, json.decoder.JSONDecodeError), retry_backoff=300, retry_jitter=False)
def get_unfulfilled_orders(self, account):
    integration = Integration.objects.get(utm_source=account)
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
            if order is None:
                basket = Basket.objects.create(site=integration.site, session_id=session.session_key, utm_source=account, secondary=True)

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

                kwargs = {
                    'integration': integration,
                    'delivery_tracking_number': posting_number
                }
                if posting.get('is_express', False):
                    kwargs['delivery'] = Order.DELIVERY_EXPRESS
                date = posting.get('shipment_date', '')
                if date:
                    kwargs['delivery_dispatch_date'] = datetime.strptime(date.split('T')[0], '%Y-%m-%d')

                order = Order.register(basket, **kwargs)

            full_address = []
            analytics_data = posting.get('analytics_data', {}) or {}  # Ozon sometimes sets analytics_data to None
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

            order.save()
            num = num + 1
        return num
    except HTTPError as e:
        content = e.read()
        error = json.loads(content.decode('utf-8'))
        logger.error(error)
        message = error.get('message', 'Неизвестная ошибка взаимодействия с Ozon!')
        raise TaskFailure(message) from e


@shared_task(bind=True, autoretry_for=(OSError, django.db.Error, json.decoder.JSONDecodeError), rate_limit='1/s', retry_backoff=300, retry_jitter=False)
def notify_product_stocks(self, products, account):
    integration = Integration.objects.get(utm_source=account)
    client_id = integration.settings.get('client_id', '')
    api_key = integration.settings.get('api_key', '')

    url = 'https://api-seller.ozon.ru/v2/products/stocks'
    headers = {
        'Client-Id': client_id,
        'Api-Key': api_key,
        'Content-Type': 'application/json'
    }

    stocks = []

    products = Product.objects.filter(pk__in=products)
    for product in products:
        stock = max(0, min(20, int(product.get_stock(integration=integration))))
        express_stock = max(0, min(20, int(product.get_stock(integration=integration, express=True))))
        for warehouse in integration.settings.get('warehouses', []):
            if warehouse.get('is_express', False):
                warehouse_stock = express_stock
            else:
                warehouse_stock = stock
            stocks.append({
                "offer_id": product.article,
                "stock": warehouse_stock,
                "warehouse_id": warehouse.get('id', 0)
            })
        if len(stocks) > 99:
            break
    products = list(products)[:len(stocks)]

    data = {'stocks': stocks}
    data_encoded = json.dumps(data).encode('utf-8')
    request = Request(url, data_encoded, headers, method='POST')
    logger.info('<<< ' + request.full_url)
    logger.info(data_encoded)
    try:
        response = urlopen(request)
        result = json.loads(response.read().decode('utf-8'))

        for product in products:
            product_integration = ProductIntegration.objects.order_by().filter(product=product, integration=integration).first()
            if product_integration is not None:
                product_integration.notify_stock = False
                product_integration.save()

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


@shared_task(bind=True, autoretry_for=(OSError, django.db.Error, json.decoder.JSONDecodeError), retry_backoff=300, retry_jitter=False)
def notify_marked_stocks(self):
    for integration in Integration.objects.filter(site=SITE_OZON):
        products = ProductIntegration.objects.order_by().filter(integration=integration, notify_stock=True)
        products = list(products.values_list('product_id', flat=True).distinct())
        if products:
            notify_product_stocks.s(products, integration.utm_source).apply_async(priority=PRIORITY_IDLE)
        return len(products)
