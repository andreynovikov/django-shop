"""
Wildberries FBS orders and stocks, all by polling.

get_new_orders registers the new orders. An order for another warehouse of the account than the integration's
warehouse_id is registered as delivered to the store, with the warehouse's name in manager_comment;
get_detached_orders picks up such orders of the last 30 minutes. get_order_statuses brings the statuses of open
orders, see WB_ORDER_STATUS.

Stocks are sent by chrtID, the id of a size of a product card, looked up by the product's GTIN and kept in
ProductIntegration.meta.
A product that Wildberries doesn't know loses its integration, and the managers get an SMS about it.
"""
import json
import logging
from datetime import datetime
from importlib import import_module
from itertools import batched
from time import sleep
from urllib.request import Request, urlopen
from urllib.error import HTTPError

import django.db
from django.db.models import Sum, F, Q
from django.conf import settings
from django.contrib import auth
from django.views.decorators.debug import sensitive_variables

from celery import shared_task

from sewingworld.tasks import PRIORITY_IDLE

from shop.health import IntegrationFailure, monitor, read_body
from shop.models import Integration, Basket, Order, Product, ProductIntegration, ShopUser
from shop.tasks.user_interaction import send_message
from shop.tasks.workflow import update_order


logger = logging.getLogger('wb')

# Local status for a Wildberries status of an assembly task (сборочное задание, an order), None to keep the status.
# wbStatus takes precedence over supplierStatus, see get_integration_order_statuses.
WB_ORDER_STATUS = {
    # supplierStatus
    'new': None,                        # new assembly task
    'confirm': None,                    # being assembled
    'complete': None,                   # in delivery
    'cancel': Order.STATUS_CANCELED,    # cancelled by the seller
    'receive': None,                    # received by the customer (wbgo)
    'reject': None,                     # refused by the customer on receipt (wbgo)
    # wbStatus
    'waiting': None,                                  # assembly task in progress
    'sorted': None,                                   # assembly task sorted
    'sold': Order.STATUS_DONE,                        # assembly task received by the buyer
    'canceled': Order.STATUS_CANCELED,                # assembly task cancelled
    'canceled_by_client': Order.STATUS_CANCELED,      # the buyer cancelled the order on receipt
    'declined_by_client': Order.STATUS_CANCELED,      # the buyer cancelled within the first hour, before assembly
    'defect': Order.STATUS_CANCELED,                  # assembly task cancelled because of a defect
    'ready_to_pickup': Order.STATUS_DELIVERED_STORE,  # assembly task arrived at the pickup point
    'postponed_delivery': None,                       # courier delivery postponed
}


class TaskFailure(IntegrationFailure):
    """ Wildberries' error reply; reply is its JSON """
    reply = None


class ApiUnavailable(IntegrationFailure, OSError):
    """ An error reply that isn't Wildberries' JSON, such as a proxy's 502: an OSError, which the tasks retry """


WB_MARKETPLACE = 'https://marketplace-api.wildberries.ru'
WB_CONTENT = 'https://content-api.wildberries.ru'


@sensitive_variables()
def _wb_request(integration, method, url, data=None):
    """ The JSON of Wildberries' reply, None for an empty one """
    headers = {'Authorization': integration.settings.get('api_key', '')}
    body = None
    if data is not None:
        headers['Content-Type'] = 'application/json; charset=utf-8'
        body = json.dumps(data).encode('utf-8')
    request = Request(url, body, headers, method=method)
    logger.info('<<< ' + request.full_url)
    if body is not None:
        logger.info(body)
    try:
        with urlopen(request, timeout=30) as response:
            content = response.read()
    except HTTPError as e:
        text = read_body(e)
        try:
            error = json.loads(text)
        except ValueError:
            raise ApiUnavailable(f'Ошибка взаимодействия с Wildberries (HTTP {e.code})', status=e.code, body=text) from e
        logger.error(error)
        message = error.get('detail') if isinstance(error, dict) else None
        failure = TaskFailure(message or 'Неизвестная ошибка взаимодействия с Wildberries!', status=e.code, body=text)
        failure.reply = error
        raise failure from e
    return json.loads(content.decode('utf-8')) if content else None


def get_warehouses(integration):
    result = _wb_request(integration, 'GET', f'{WB_MARKETPLACE}/api/v3/warehouses')
    logger.debug(result)
    return {warehouse['id']: warehouse['name'] for warehouse in result}


@shared_task(bind=True, autoretry_for=(OSError, django.db.Error, json.decoder.JSONDecodeError), retry_backoff=300, retry_jitter=False)
def get_integration_new_orders(self, account, target_site_id=None):
    integration = Integration.get_for_utm_source(account, target_site_id)
    warehouseId = integration.settings.get('warehouse_id', '')

    with monitor(integration, self.name):
        warehouses = get_warehouses(integration)
        result = _wb_request(integration, 'GET', f'{WB_MARKETPLACE}/api/v3/orders/new')
        logger.debug(result)
        num = 0
        user = ShopUser.objects.get(phone='0003')
        """
        {'orders': [{'address': None, 'deliveryType': 'fbs', 'user': None, 'orderUid': '16826002_17413001083567049', 'article': 'ЦБ-0232800', 'rid': '17413001083567049.0.0',
         'createdAt': '2023-10-13T06:35:01Z', 'offices': ['Москва_Север'], 'skus': ['4650254750105'], 'id': 1119437040, 'warehouseId': 825523, 'nmId': 181465736,
         'chrtId': 299656738, 'price': 53900, 'convertedPrice': 53900, 'currencyCode': 643, 'convertedCurrencyCode': 643, 'cargoType': 1, 'isLargeCargo': False}]}
        """
        # Order.register() takes the buyer from the basket's session: the service user of Wildberries orders
        SessionStore = import_module(settings.SESSION_ENGINE).SessionStore
        session = SessionStore()
        session.cycle_key()
        session[auth.SESSION_KEY] = user._meta.pk.value_to_string(user)
        session[auth.BACKEND_SESSION_KEY] = settings.AUTHENTICATION_BACKENDS[0]
        session[auth.HASH_SESSION_KEY] = user.get_session_auth_hash()
        session.save()
        for wb_order in result.get('orders', []):
            logger.debug(wb_order)
            wirehouse_id = wb_order.get('warehouseId', 0)
            order_number = wb_order.get('id', 0)
            if not order_number:
                continue

            order = Order.objects.filter(integration=integration, delivery_tracking_number=str(order_number)).first()
            if order is not None:
                continue

            basket = Basket.objects.create(site=integration.source_site, session_id=session.session_key, utm_source=account, secondary=True)

            has_problem = False
            for sku in wb_order.get('skus', []):
                product = Product.objects.filter(gtin=sku, integration=integration).first()  # filter by integration because GTIN is not unique
                if product is None:
                    product = Product.objects.filter(gtins__contains=[sku], integration=integration).first()
                if product is not None:
                    item, _ = basket.items.get_or_create(product=product)
                    # item.quantity = 1
                    item.save()
                else:
                    logger.error("Couldn't find product with SKU: {}".format(sku))
                    has_problem = True

            basket.save()

            if wirehouse_id != warehouseId:
                status = Order.STATUS_DELIVERED_STORE
            else:
                status = Order.STATUS_NEW

            kwargs = {
                'integration': integration,
                'delivery_tracking_number': str(order_number),
                'status': status,
                'comment': wb_order.get('comment')
            }
            if wirehouse_id != warehouseId:
                kwargs['manager_comment'] = warehouses.get(wirehouse_id)
            if has_problem:
                kwargs['alert'] = 'Ошибка при добавлении товара в заказ'
            order = Order.register(basket, **kwargs)

            num = num + 1
        return num


@shared_task
def get_new_orders():
    total = 0
    for integration in Integration.objects.filter(source_site__domain='wildberries.ru', enabled=True):
        get_integration_new_orders.s(integration.utm_source, target_site_id=integration.target_site_id).apply_async(priority=PRIORITY_IDLE)
        total += 1
    return total


@shared_task(bind=True, autoretry_for=(OSError, django.db.Error, json.decoder.JSONDecodeError), retry_backoff=300, retry_jitter=False)
def get_integration_detached_orders(self, account, target_site_id=None):
    integration = Integration.get_for_utm_source(account, target_site_id)
    warehouseId = integration.settings.get('warehouse_id', '')

    with monitor(integration, self.name):
        warehouses = get_warehouses(integration)
        if len(list(filter(lambda k: k != warehouseId, warehouses.keys()))) == 0:
            return

        date_from = int(datetime.now().timestamp()) - 30 * 60  # last 30 minutes
        result = _wb_request(integration, 'GET', f'{WB_MARKETPLACE}/api/v3/orders?limit=1000&next=0&dateFrom={date_from}')
        logger.debug(result)
        num = 0
        user = ShopUser.objects.get(phone='0003')
        """
        {'orders': [{'address': None, 'deliveryType': 'fbs', 'user': None, 'orderUid': '16826002_17413001083567049', 'article': 'ЦБ-0232800', 'rid': '17413001083567049.0.0',
         'createdAt': '2023-10-13T06:35:01Z', 'offices': ['Москва_Север'], 'skus': ['4650254750105'], 'id': 1119437040, 'warehouseId': 825523, 'nmId': 181465736,
         'chrtId': 299656738, 'price': 53900, 'convertedPrice': 53900, 'currencyCode': 643, 'convertedCurrencyCode': 643, 'cargoType': 1, 'isLargeCargo': False}]}
        """
        SessionStore = import_module(settings.SESSION_ENGINE).SessionStore
        session = SessionStore()
        session.cycle_key()
        session[auth.SESSION_KEY] = user._meta.pk.value_to_string(user)
        session[auth.BACKEND_SESSION_KEY] = settings.AUTHENTICATION_BACKENDS[0]
        session[auth.HASH_SESSION_KEY] = user.get_session_auth_hash()
        session.save()
        for wb_order in result.get('orders', []):
            logger.debug(wb_order)
            warehouse_id = wb_order.get('warehouseId', 0)
            if not warehouse_id or warehouse_id == warehouseId:
                continue
            order_number = wb_order.get('id', 0)
            if not order_number:
                continue

            order = Order.objects.filter(integration=integration, delivery_tracking_number=str(order_number)).first()
            if order is not None:
                continue

            basket = Basket.objects.create(site=integration.source_site, session_id=session.session_key, utm_source=account, secondary=True)

            has_problem = False
            for sku in wb_order.get('skus', []):
                product = Product.objects.filter(gtin=sku, integration=integration).first()  # filter by integration because GTIN is not unique
                if product is None:
                    product = Product.objects.filter(gtins__contains=[sku], integration=integration).first()
                if product is not None:
                    item, _ = basket.items.get_or_create(product=product)
                    # item.quantity = 1
                    item.save()
                else:
                    logger.error("Couldn't find product with SKU: {}".format(sku))
                    has_problem = True

            basket.save()

            kwargs = {
                'integration': integration,
                'delivery_tracking_number': str(order_number),
                'status': Order.STATUS_DELIVERED_STORE,
                'manager_comment': warehouses.get(warehouse_id),
                'comment': wb_order.get('comment')
            }
            if has_problem:
                kwargs['alert'] = 'Ошибка при добавлении товара в заказ'
            order = Order.register(basket, **kwargs)

            num = num + 1
        return num


@shared_task
def get_detached_orders():
    total = 0
    for integration in Integration.objects.filter(source_site__domain='wildberries.ru', enabled=True):
        get_integration_detached_orders.s(integration.utm_source, target_site_id=integration.target_site_id).apply_async(priority=PRIORITY_IDLE)
        total += 1
    return total


@shared_task(bind=True, autoretry_for=(OSError, django.db.Error, json.decoder.JSONDecodeError), retry_backoff=300, retry_jitter=False)
def get_integration_order_statuses(self, account, target_site_id=None):
    integration = Integration.get_for_utm_source(account, target_site_id)

    orders = list(map(lambda n: int(n), Order.objects.filter(integration=integration, status__lt=Order.STATUS_DONE).values_list('delivery_tracking_number', flat=True)))
    if not orders:
        return 0

    with monitor(integration, self.name):
        result = _wb_request(integration, 'POST', f'{WB_MARKETPLACE}/api/v3/orders/status', {'orders': orders})
        logger.debug(result)
        num = 0
        for wb_order in result.get('orders', []):
            order_number = wb_order.get('id', 0)
            order = Order.objects.filter(integration=integration, delivery_tracking_number=str(order_number)).first()
            if order is None:
                continue

            supplierStatus = wb_order.get('supplierStatus', '')
            wbStatus = wb_order.get('wbStatus', '')
            status = WB_ORDER_STATUS.get(wbStatus, None) or WB_ORDER_STATUS.get(supplierStatus, None)
            if status is None:
                continue

            update = {}
            if status == Order.STATUS_CANCELED and order.status not in (Order.STATUS_NEW, Order.STATUS_CANCELED):  # Flag cancellations during fulfillment for staff review.
                update['alert'] = wbStatus or 'canceled'
            elif status != order.status:
                update['status'] = status
            if update:
                update_order.delay(order.pk, update)
                num = num + 1
        return num


@shared_task
def get_order_statuses():
    total = 0
    for integration in Integration.objects.filter(source_site__domain='wildberries.ru', enabled=True):
        get_integration_order_statuses.s(integration.utm_source, target_site_id=integration.target_site_id).apply_async(priority=PRIORITY_IDLE)
        total += 1
    return total


@shared_task(bind=True, autoretry_for=(OSError, django.db.Error, json.decoder.JSONDecodeError), rate_limit='1/s', retry_backoff=300, retry_jitter=False)
def notify_product_stocks(self, products, account, zero_out=False, target_site_id=None):
    integration = Integration.get_for_utm_source(account, target_site_id)
    with monitor(integration, self.name):
        return _notify_product_stocks(integration, products, zero_out)


def _notify_product_stocks(integration, products, zero_out):
    products = Product.objects.filter(pk__in=products)
    product_integrations = {}
    chrtIDs = {}

    for product in products:
        product_integration = ProductIntegration.objects.order_by().filter(product=product, integration=integration).first()
        product_integrations[product.pk] = product_integration
        if product_integration.meta is None or product_integration.meta.get('chrtID', None) is None:
            if not product.gtin:
                product_integration.delete()
                for phone in integration.source_site.profile.manager_phones.split(','):
                    send_message.s(phone, 'У товара {} отключена интеграция "{}" (отсутствует штрих-код)'.format(product.code, integration.utm_source)).apply_async(priority=PRIORITY_IDLE)
                continue
            data = {'settings': {'filter': {'textSearch': product.gtin, 'withPhoto': -1}}}
            try:
                sleep(10)
                result = _wb_request(integration, 'POST', f'{WB_CONTENT}/content/v2/get/cards/list', data)
                for card in result.get('cards', []):
                    for size in card.get('sizes', []):
                        if product.gtin in size.get('skus', []):
                            product_integration.meta = {'chrtID': size.get('chrtID')}
                            product_integration.save()
                if product_integration.meta is None or product_integration.meta.get('chrtID', None) is None:
                    product_integration.delete()
                    for phone in integration.source_site.profile.manager_phones.split(','):
                        send_message.s(phone, 'У товара {} отключена интеграция "{}" (не найден штрих-код)'.format(product.code, integration.utm_source)).apply_async(priority=PRIORITY_IDLE)
                    continue
            except TaskFailure as e:
                if e.status == 429:
                    return False  # the products keep notify_stock for the next run
                else:
                    continue
        chrtIDs[product.gtin] = product_integration.meta.get('chrtID')

    warehouseId = integration.settings.get('warehouse_id', '')

    stocks = []
    notified_products = []

    products = [product for product in products if product.gtin in chrtIDs]
    counted = {} if zero_out else Product.get_stocks([product.pk for product in products], integration=integration)
    for product in products:
        if zero_out:
            amount = 0
        else:
            amount = max(0, min(20, int(counted[product.pk])))
        stocks.append({
            'chrtId': chrtIDs[product.gtin],
            'amount': amount
        })
        notified_products.append(product)

    if len(stocks) == 0:
        return False

    try:
        _wb_request(integration, 'PUT', f'{WB_MARKETPLACE}/api/v3/stocks/{warehouseId}', {'stocks': stocks})
    except TaskFailure as e:
        error = e.reply
        if not isinstance(error, list):
            raise
        first_error = error[0] if error else {}
        if 'data' in first_error:
            for item in first_error['data']:
                if item.get('code') == 'NotFound' and 'sku' in item:
                    sku = item.get('sku')
                    ProductIntegration.objects.filter(product__gtin=sku, integration=integration).delete()
                    # {'data': [{'sku': '374318830018', 'chrtId': 0, 'amount': 4}], 'code': 'NotFound', 'message': 'Not found'}
                    for phone in integration.source_site.profile.manager_phones.split(','):
                        send_message.s(phone, 'У товара с штрих-кодом {} отключена интеграция WB'.format(sku)).apply_async(priority=PRIORITY_IDLE)
        return True
    for product in notified_products:
        product_integration = product_integrations[product.pk]
        product_integration.notify_stock = False
        product_integration.save()
    return True


@shared_task(bind=True, autoretry_for=(OSError, django.db.Error, json.decoder.JSONDecodeError), retry_backoff=300, retry_jitter=False)
def notify_marked_stocks(self):
    total = 0
    for integration in Integration.objects.filter(source_site__domain='wildberries.ru', enabled=True):
        if integration.settings.get('warehouse_id', 0) == 0:
            continue

        products = ProductIntegration.objects.order_by().filter(integration=integration, notify_stock=True)
        products = list(products.values_list('product_id', flat=True).distinct())
        if products:
            countdown = 0
            for chunk in batched(products, 20):
                notify_product_stocks.s(chunk, integration.utm_source, target_site_id=integration.target_site_id).apply_async(countdown=countdown, priority=PRIORITY_IDLE)
                countdown += 20
        total += len(products)
    return total


@shared_task(bind=True, autoretry_for=(OSError, django.db.Error, json.decoder.JSONDecodeError), retry_backoff=300, retry_jitter=False)
def notify_integration_stocks(self):
    total = 0
    for integration in Integration.objects.filter(source_site__domain='wildberries.ru', enabled=True):
        if integration.settings.get('warehouse_id', 0) == 0:
            continue

        products = Product.objects.order_by().filter(integration=integration).exclude(gtin__exact='')

        if integration.output_available:
            products = products.annotate(
                quantity=Sum('stock_item__quantity', filter=Q(stock_item__supplier__integration=integration)),
                correction=Sum('stock_item__correction', filter=Q(stock_item__supplier__integration=integration)),
                available=F('quantity') + F('correction')
            ).filter(available__gt=0)

        products = list(products.values_list('id', flat=True).distinct())

        countdown = 0
        for chunk in batched(products, 20):
            notify_product_stocks.s(chunk, integration.utm_source, target_site_id=integration.target_site_id).apply_async(countdown=countdown, priority=PRIORITY_IDLE)
            countdown += 60

        total += len(products)

    return total
