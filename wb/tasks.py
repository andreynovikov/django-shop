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
from django.contrib.sites.models import Site

from celery import shared_task

from sewingworld.tasks import PRIORITY_IDLE

from shop.models import Integration, Basket, Order, Product, ProductIntegration, ShopUser
from shop.tasks import send_message, update_order


logger = logging.getLogger('wb')
SITE_WB = Site.objects.get(domain='wildberries.ru')

WB_ORDER_STATUS = {
    # supplierStatus
    'new': None,                        # новое сборочное задание
    'confirm': None,                    # на сборке
    'complete': None,                   # в доставке
    'cancel': Order.STATUS_CANCELED,    # отменено продавцом
    'receive': None,                    # получено клиентом (wbgo)
    'reject': None,                     # отказ клиента при получении (wbgo)
    # wbStatus
    'waiting': None,                                  # сборочное задание в работе
    'sorted': None,                                   # сборочное задание отсортировано
    'sold': Order.STATUS_DONE,                        # сборочное задание получено покупателем
    'canceled': Order.STATUS_CANCELED,                # отмена сборочного задания
    'canceled_by_client': Order.STATUS_CANCELED,      # покупатель отменил заказ при получении
    'declined_by_client': Order.STATUS_CANCELED,      # покупатель отменил заказ в первый чаc, если заказ не переведён на сборку
    'defect': Order.STATUS_CANCELED,                  # отмена сборочного задания по причине брака
    'ready_to_pickup': Order.STATUS_DELIVERED_STORE,  # сборочное задание прибыло на ПВЗ
    'postponed_delivery': None,                       # курьерская доставка отложена
}


class TaskFailure(Exception):
    pass


def get_warehouses(account):
    integration = Integration.objects.get(utm_source=account)

    api_key = integration.settings.get('api_key', '')

    url = 'https://marketplace-api.wildberries.ru/api/v3/warehouses'
    headers = {
        'Authorization': api_key
    }
    request = Request(url, None, headers)
    logger.info('<<< ' + request.full_url)
    try:
        response = urlopen(request)
        result = json.loads(response.read().decode('utf-8'))
        logger.debug(result)
        warehouses = {warehouse['id']: warehouse['name'] for warehouse in result}
        return warehouses
    except HTTPError as e:
        content = e.read()
        error = json.loads(content.decode('utf-8'))
        logger.error(error)
        try:
            message = error.get('detail', 'Неизвестная ошибка взаимодействия с Wildberries!')
        except:  # noqa #722
            message = error
        raise TaskFailure(message) from e


@shared_task(bind=True, autoretry_for=(OSError, django.db.Error, json.decoder.JSONDecodeError), retry_backoff=300, retry_jitter=False)
def get_integration_new_orders(self, account):
    integration = Integration.objects.get(utm_source=account)
    warehouseId = integration.settings.get('warehouse_id', '')
    warehouses = get_warehouses(account)

    api_key = integration.settings.get('api_key', '')

    url = 'https://marketplace-api.wildberries.ru/api/v3/orders/new'
    headers = {
        'Authorization': api_key
    }
    request = Request(url, None, headers)
    logger.info('<<< ' + request.full_url)
    try:
        response = urlopen(request)
        result = json.loads(response.read().decode('utf-8'))
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
            wirehouse_id = wb_order.get('warehouseId', 0)
            order_number = wb_order.get('id', 0)
            if not order_number:
                continue

            order = Order.objects.filter(delivery_tracking_number=str(order_number)).first()
            if order is not None:
                continue

            basket = Basket.objects.create(site=integration.site, session_id=session.session_key, utm_source=account, secondary=True)

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
    except HTTPError as e:
        content = e.read()
        error = json.loads(content.decode('utf-8'))
        logger.error(error)
        try:
            message = error.get('detail', 'Неизвестная ошибка взаимодействия с Wildberries!')
        except:  # noqa E722
            message = error
        raise TaskFailure(message) from e


@shared_task
def get_new_orders():
    total = 0
    for integration in Integration.objects.filter(site=SITE_WB, enabled=True):
        get_integration_new_orders.s(integration.utm_source).apply_async(priority=PRIORITY_IDLE)
        total += 1
    return total


@shared_task(bind=True, autoretry_for=(OSError, django.db.Error, json.decoder.JSONDecodeError), retry_backoff=300, retry_jitter=False)
def get_integration_detached_orders(self, account):
    integration = Integration.objects.get(utm_source=account)
    warehouseId = integration.settings.get('warehouse_id', '')
    warehouses = get_warehouses(account)
    if len(list(filter(lambda k: k != warehouseId, warehouses.keys()))) == 0:
        return

    api_key = integration.settings.get('api_key', '')

    date_from = int(datetime.now().timestamp()) - 30 * 60  # last 30 minutes
    url = 'https://marketplace-api.wildberries.ru/api/v3/orders?limit=1000&next=0&dateFrom=' + str(date_from)
    headers = {
        'Authorization': api_key
    }
    request = Request(url, None, headers)
    logger.info('<<< ' + request.full_url)
    try:
        response = urlopen(request)
        result = json.loads(response.read().decode('utf-8'))
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

            order = Order.objects.filter(delivery_tracking_number=str(order_number)).first()
            if order is not None:
                continue

            basket = Basket.objects.create(site=integration.site, session_id=session.session_key, utm_source=account, secondary=True)

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
    except HTTPError as e:
        content = e.read()
        error = json.loads(content.decode('utf-8'))
        logger.error(error)
        try:
            message = error.get('detail', 'Неизвестная ошибка взаимодействия с Wildberries!')
        except:  # noqa E722
            message = error
        raise TaskFailure(message) from e


@shared_task
def get_detached_orders():
    total = 0
    for integration in Integration.objects.filter(site=SITE_WB, enabled=True):
        get_integration_detached_orders.s(integration.utm_source).apply_async(priority=PRIORITY_IDLE)
        total += 1
    return total


@shared_task(bind=True, autoretry_for=(OSError, django.db.Error, json.decoder.JSONDecodeError), retry_backoff=300, retry_jitter=False)
def get_integration_order_statuses(self, account):
    integration = Integration.objects.get(utm_source=account)
    api_key = integration.settings.get('api_key', '')

    url = 'https://marketplace-api.wildberries.ru/api/v3/orders/status'
    headers = {
        'Authorization': api_key,
        'Content-Type': 'application/json; charset=utf-8'
    }

    orders = list(map(lambda n: int(n), Order.objects.filter(integration=integration, status__lt=Order.STATUS_DONE).values_list('delivery_tracking_number', flat=True)))
    if not orders:
        return 0

    data = {'orders': orders}
    data_encoded = json.dumps(data).encode('utf-8')
    request = Request(url, data_encoded, headers, method='POST')
    logger.info('<<< ' + request.full_url)
    logger.info(data_encoded)
    try:
        response = urlopen(request)
        result = json.loads(response.read().decode('utf-8'))
        logger.debug(result)
        num = 0
        for wb_order in result.get('orders', []):
            order_number = wb_order.get('id', 0)
            order = Order.objects.filter(delivery_tracking_number=str(order_number)).first()
            if order is None:
                continue

            supplierStatus = wb_order.get('supplierStatus', '')
            wbStatus = wb_order.get('wbStatus', '')
            status = WB_ORDER_STATUS.get(wbStatus, None) or WB_ORDER_STATUS.get(supplierStatus, None)
            if status is None:
                continue

            update = {}
            if status == Order.STATUS_CANCELED and order.status not in (Order.STATUS_NEW, Order.STATUS_CANCELED):  # если заказ в обработке, выставляем флаг тревоги, не меняя статус
                update['alert'] = wbStatus or 'canceled'
            elif status != order.status:
                update['status'] = status
            if update:
                update_order.delay(order.pk, update)
                num = num + 1
        return num
    except HTTPError as e:
        content = e.read()
        error = json.loads(content.decode('utf-8'))
        logger.error(error)
        try:
            message = error.get('detail', 'Неизвестная ошибка взаимодействия с Wildberries!')
        except:  # noqa E722
            message = error
        raise TaskFailure(message) from e


@shared_task
def get_order_statuses():
    total = 0
    for integration in Integration.objects.filter(site=SITE_WB, enabled=True):
        get_integration_order_statuses.s(integration.utm_source).apply_async(priority=PRIORITY_IDLE)
        total += 1
    return total


@shared_task(bind=True, autoretry_for=(OSError, django.db.Error, json.decoder.JSONDecodeError), rate_limit='1/s', retry_backoff=300, retry_jitter=False)
def notify_product_stocks(self, products, account, zero_out=False):
    integration = Integration.objects.get(utm_source=account)

    api_key = integration.settings.get('api_key', '')

    headers = {
        'Authorization': api_key,
        'Content-Type': 'application/json; charset=utf-8'
    }

    products = Product.objects.filter(pk__in=products)
    product_integrations = {}
    chrtIDs = {}

    url = 'https://content-api.wildberries.ru/content/v2/get/cards/list'
    for product in products:
        product_integration = ProductIntegration.objects.order_by().filter(product=product, integration=integration).first()
        product_integrations[product.pk] = product_integration
        if product_integration.meta is None or product_integration.meta.get('chrtID', None) is None:
            if not product.gtin:
                product_integration.delete()
                for phone in SITE_WB.profile.manager_phones.split(','):
                    send_message.s(phone, 'У товара {} отключена интеграция "{}" (отсутствует штрих-код)'.format(product.code, integration.utm_source)).apply_async(priority=PRIORITY_IDLE)
                continue
            data = {'settings': {'filter': {'textSearch': product.gtin, 'withPhoto': -1}}}
            data_encoded = json.dumps(data).encode('utf-8')
            request = Request(url, data_encoded, headers, method='POST')
            logger.info('<<< ' + request.full_url)
            logger.info(data_encoded)
            try:
                sleep(10)
                response = urlopen(request)
                result = json.loads(response.read().decode('utf-8'))
                for card in result.get('cards', []):
                    for size in card.get('sizes', []):
                        if product.gtin in size.get('skus', []):
                            product_integration.meta = {'chrtID': size.get('chrtID')}
                            product_integration.save()
                if product_integration.meta is None or product_integration.meta.get('chrtID', None) is None:
                    product_integration.delete()
                    for phone in SITE_WB.profile.manager_phones.split(','):
                        send_message.s(phone, 'У товара {} отключена интеграция "{}" (не найден штрих-код)'.format(product.code, integration.utm_source)).apply_async(priority=PRIORITY_IDLE)
                    continue
            except HTTPError as e:
                content = e.read()
                error = json.loads(content.decode('utf-8'))
                logger.error(error)
                if error.get('status', 0) == 429:
                    return False
                else:
                    continue
        chrtIDs[product.gtin] = product_integration.meta.get('chrtID')

    warehouseId = integration.settings.get('warehouse_id', '')
    url = 'https://marketplace-api.wildberries.ru/api/v3/stocks/{warehouseId}'.format(warehouseId=warehouseId)

    stocks = []
    notified_products = []

    for product in products:
        if product.gtin not in chrtIDs:
            continue
        if zero_out:
            amount = 0
        else:
            amount = max(0, min(20, int(product.get_stock(integration=integration))))
        stocks.append({
            'chrtId': chrtIDs[product.gtin],
            'amount': amount
        })
        notified_products.append(product)

    if len(stocks) == 0:
        return False

    data = {'stocks': stocks}
    data_encoded = json.dumps(data).encode('utf-8')
    request = Request(url, data_encoded, headers, method='PUT')
    logger.info('<<< ' + request.full_url)
    logger.info(data_encoded)
    try:
        response = urlopen(request)
        for product in notified_products:
            product_integration = product_integrations[product.pk]
            product_integration.notify_stock = False
            product_integration.save()
        return True
    except HTTPError as e:
        content = e.read()
        error = json.loads(content.decode('utf-8'))
        logger.error(error)
        if isinstance(error, list):
            first_error = error[0]
            if 'data' in first_error:
                for item in first_error['data']:
                    if item.get('code') == 'NotFound' and 'sku' in item:
                        sku = item.get('sku')
                        ProductIntegration.objects.filter(product__gtin=sku, integration=integration).delete()
                        # {'data': [{'sku': '374318830018', 'chrtId': 0, 'amount': 4}], 'code': 'NotFound', 'message': 'Not found'}
                        for phone in SITE_WB.profile.manager_phones.split(','):
                            send_message.s(phone, 'У товара с штрих-кодом {} отключена интеграция WB'.format(sku)).apply_async(priority=PRIORITY_IDLE)
            return True
        else:
            try:
                message = error.get('detail', 'Неизвестная ошибка взаимодействия с Wildberries!')
            except:  # noqa E722
                message = error
            raise TaskFailure(message) from e


@shared_task(bind=True, autoretry_for=(OSError, django.db.Error, json.decoder.JSONDecodeError), retry_backoff=300, retry_jitter=False)
def notify_marked_stocks(self):
    total = 0
    for integration in Integration.objects.filter(site=SITE_WB, enabled=True):
        if integration.settings.get('warehouse_id', 0) == 0:
            continue

        products = ProductIntegration.objects.order_by().filter(integration=integration, notify_stock=True)
        products = list(products.values_list('product_id', flat=True).distinct())
        if products:
            countdown = 0
            for chunk in batched(products, 20):
                notify_product_stocks.s(chunk, integration.utm_source).apply_async(countdown=countdown, priority=PRIORITY_IDLE)
                countdown += 20
        total += len(products)
    return total


@shared_task(bind=True, autoretry_for=(OSError, django.db.Error, json.decoder.JSONDecodeError), retry_backoff=300, retry_jitter=False)
def notify_integration_stocks(self):
    total = 0
    for integration in Integration.objects.filter(site=SITE_WB, enabled=True):
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
            notify_product_stocks.s(chunk, integration.utm_source).apply_async(countdown=countdown, priority=PRIORITY_IDLE)
            countdown += 60

        total += len(products)

    return total
