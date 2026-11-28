"""
Yandex.Market FBS orders and stocks.

get_orders polls every Market integration that uses the API: it syncs the open orders and registers the orders
that wait for packing (PROCESSING/STARTED). An integration with a push_token also takes Market's notifications
(views.notification), each of which syncs one order. Both hold the integration's ORDER_SYNC_LOCK.
When the admin marks an order collected, notify_order_status sends its boxes and READY_TO_SHIP; a failure
that a retry can't mend puts the order into the problem status with the reason in delivery_info.
"""
import json
import logging
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal, ROUND_UP
from importlib import import_module
from itertools import batched
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError

import django.db
from django.conf import settings
from django.contrib import auth
from django.db import transaction
from django.db.models import Sum, F, Q
from django.utils.dateparse import parse_date, parse_time
from django.views.decorators.debug import sensitive_variables

from celery import shared_task

from sewingworld.lock import Lock
from sewingworld.tasks import PRIORITY_IDLE

from shop.models import Basket, Integration, Order, Product, ProductIntegration, ShopUser

logger = logging.getLogger('ym')


class TaskFailure(Exception):
    pass


class MarketUnavailable(OSError):
    pass


MARKET_URL = 'https://api.partner.market.yandex.ru'
ORDER_SYNC_LOCK = 'ym.get_integration_orders'
READY_TO_SHIP = ('PROCESSING', 'READY_TO_SHIP')
AWAITING_PACKING = ('PROCESSING', 'STARTED')
CLOSED_STATUSES = (Order.STATUS_CANCELED, Order.STATUS_DONE, Order.STATUS_FINISHED)
DELIVERY_STATUSES = {
    ('PROCESSING', 'SHIPPED'): Order.STATUS_SENT,
    ('DELIVERY', None): Order.STATUS_SENT,
    ('PICKUP', None): Order.STATUS_DELIVERED,
    ('DELIVERED', None): Order.STATUS_DONE,
}
FULFILLMENT_STATUSES = (
    Order.STATUS_NEW, Order.STATUS_ACCEPTED, Order.STATUS_WAITING, Order.STATUS_COLLECTING,
    Order.STATUS_COLLECTED, Order.STATUS_DELIVERED_STORE, Order.STATUS_SENT, Order.STATUS_DELIVERED,
)
EARLY_CANCELLATIONS = {
    'REPLACING_ORDER', 'RESERVATION_EXPIRED', 'USER_CHANGED_MIND', 'USER_NOT_PAID', 'USER_REFUSED_DELIVERY',
    'USER_UNREACHABLE', 'USER_BOUGHT_CHEAPER', 'BANK_REJECT_CREDIT_OFFER', 'USER_PLACED_OTHER_ORDER',
}

ORDER_SUBSTATUS = {
    'PROCESSING_EXPIRED': 'Магазин не обработал заказ в течение семи дней',
    'REPLACING_ORDER': 'Покупатель решил заменить товар другим по собственной инициативе',
    'RESERVATION_EXPIRED': 'Покупатель не завершил оформление зарезервированного заказа в течение 10 минут',
    'SHOP_FAILED': 'Магазин не может выполнить заказ',
    'USER_CHANGED_MIND': 'Покупатель отменил заказ по собственным причинам',
    'USER_NOT_PAID': 'Покупатель не оплатил заказ (для типа оплаты PREPAID) в течение двух часов',
    'USER_BOUGHT_CHEAPER': 'Покупатель нашёл товар дешевле',
    'USER_REFUSED_DELIVERY': 'Покупателя не устраивают условия доставки',
    'USER_REFUSED_PRODUCT': 'Покупателю не подошел товар',
    'USER_REFUSED_QUALITY': 'Покупателя не устраивает качество товара',
    'USER_UNREACHABLE': 'Не удалось связаться с покупателем',
    'BANK_REJECT_CREDIT_OFFER': 'Банк отклонил заявку на кредит',
    'USER_PLACED_OTHER_ORDER': 'Покупатель оформил другой заказ'
}


def _positive_id(value):
    if type(value) is int:
        return value if value > 0 else None
    if isinstance(value, str) and value.isascii() and value.isdecimal():
        return int(value) or None
    return None


@sensitive_variables()
def _market_request(integration, method, path, data=None, params=None):
    api_key = (integration.settings or {}).get('api_key')
    if not api_key:
        raise TaskFailure(f'У интеграции Яндекс Маркета {integration.pk} не указан API-ключ')

    url = MARKET_URL + path
    if params:
        url += '?' + urlencode(params)
    headers = {'Api-Key': api_key}
    body = None
    if data is not None:
        headers['Content-Type'] = 'application/json'
        body = json.dumps(data).encode('utf-8')

    request = Request(url, body, headers, method=method)
    try:
        with urlopen(request, timeout=15) as response:
            result = json.loads(response.read(), parse_float=Decimal)
    except HTTPError as error:
        status = error.code
        error.close()
        message = f'Яндекс Маркет вернул HTTP {status} для {method} {path}'
        # MarketUnavailable is an OSError, which the tasks retry; TaskFailure fails them
        if status in (408, 420, 429) or status >= 500:
            raise MarketUnavailable(message) from None
        raise TaskFailure(message) from None
    except (json.JSONDecodeError, UnicodeDecodeError):
        raise MarketUnavailable(f'Yandex.Market {method} {path} returned invalid JSON') from None

    if not isinstance(result, dict):
        raise MarketUnavailable(f'Yandex.Market {method} {path} returned an invalid response')
    if result.get('status') == 'ERROR':
        raise TaskFailure(f'Яндекс Маркет отклонил запрос {method} {path}')
    return result


def _campaign_ids(integration):
    campaign_id = _positive_id(integration.settings.get('ym_campaign'))
    if campaign_id is None:
        raise TaskFailure(f'У интеграции Яндекс Маркета {integration.pk} неверный идентификатор кампании')

    response = _market_request(integration, 'GET', f'/v2/campaigns/{campaign_id}')
    campaign = response.get('campaign')
    if isinstance(campaign, dict) and campaign.get('id') == campaign_id:
        business = campaign.get('business')
        if isinstance(business, dict) and (business_id := _positive_id(business.get('id'))) is not None:
            return campaign_id, business_id
    raise MarketUnavailable(f'Yandex.Market returned invalid campaign details for {campaign_id}')


def _market_orders(integration, campaign_id, business_id, filters):
    path = f'/v1/businesses/{business_id}/orders'
    data = {'campaignIds': [campaign_id], 'programTypes': ['FBS'], 'fake': False, **filters}
    params = {'limit': 50}
    seen_tokens = set()
    while True:
        result = _market_request(integration, 'POST', path, data, params)
        orders = result.get('orders')
        paging = result.get('paging') or {}
        if not isinstance(orders, list) or not isinstance(paging, dict):
            raise MarketUnavailable(f'Yandex.Market returned an invalid order page for campaign {campaign_id}')
        for order in orders:
            if (
                isinstance(order, dict) and order.get('campaignId') == campaign_id
                and order.get('programType', 'FBS') == 'FBS' and not order.get('fake', False)
                and _positive_id(order.get('orderId')) is not None
            ):
                yield order

        token = paging.get('nextPageToken')
        if not token:
            return
        if not isinstance(token, str) or token in seen_tokens:
            raise MarketUnavailable(f'Yandex.Market returned an invalid page token for campaign {campaign_id}')
        seen_tokens.add(token)
        params['pageToken'] = token


def _market_order_status(data):
    return data.get('status'), data.get('substatus')


def _market_order_by_id(integration, campaign_id, business_id, order_id):
    return next(
        (order for order in _market_orders(integration, campaign_id, business_id, {'orderIds': [order_id]})
         if order['orderId'] == order_id),
        None,
    )


def _delivery_fields(data):
    delivery = data.get('delivery') or {}
    dates = delivery.get('dates') or {}
    shipment = delivery.get('shipment') or {}
    fields = {}
    for name, value, parse in (
        ('delivery_dispatch_date', shipment.get('shipmentDate'), parse_date),
        ('delivery_handing_date', dates.get('fromDate'), parse_date),
        ('delivery_time_from', dates.get('fromTime'), parse_time),
        ('delivery_time_till', dates.get('toTime'), parse_time),
    ):
        if value:
            try:
                parsed = parse(value)
            except (TypeError, ValueError):
                parsed = None
            if parsed is not None:
                fields[name] = parsed

    destination = delivery.get('pickup' if delivery.get('type') == 'PICKUP' else 'courier') or {}
    address_fields = destination.get('address') or {}
    region = destination.get('region')
    region_names = []
    while region:
        name = region.get('name')
        if name and name not in region_names:
            region_names.append(name)
            if region.get('type') == 'CITY':
                fields.setdefault('city', name[:255])
        region = region.get('parent')

    if address_fields.get('city'):
        fields['city'] = address_fields['city'][:255]
    if not region_names and fields.get('city'):
        region_names.append(fields['city'])
    if region_names:
        fields['address'] = ', '.join(region_names)[:255]
    return fields


def _is_prepaid(data):
    return data.get('paymentType') == 'PREPAID' and data.get('status') in ('PROCESSING', 'DELIVERY', 'PICKUP', 'DELIVERED')


def _item_discount(product, site, data):
    prices = data.get('prices')
    if not prices:
        return Decimal(0)
    amounts = [(prices.get(name) or {}).get('value') for name in ('payment', 'cashback', 'subsidy')]
    if all(amount is None for amount in amounts):
        return Decimal(0)
    unit_price = sum(Decimal(str(amount)) for amount in amounts if amount is not None) / data['count']
    precision = Decimal('0.01') if site.profile.wholesale else Decimal('1')
    list_price = product.site_price(site).quantize(precision, rounding=ROUND_UP)
    return max(Decimal(0), list_price - unit_price).quantize(Decimal('0.01'))


@sensitive_variables()
def _import_order(integration, data):
    order_number = str(data['orderId'])
    with transaction.atomic():
        if Order.objects.filter(integration=integration, delivery_tracking_number=order_number).exists():
            return False

        # Order.register() takes the buyer from the basket's session: the service user of Market orders
        user = ShopUser.objects.get(phone='0000')
        session = import_module(settings.SESSION_ENGINE).SessionStore()
        session[auth.SESSION_KEY] = user._meta.pk.value_to_string(user)
        session[auth.BACKEND_SESSION_KEY] = settings.AUTHENTICATION_BACKENDS[0]
        session[auth.HASH_SESSION_KEY] = user.get_session_auth_hash()
        session.save()
        site = integration.source_site
        basket = Basket.objects.create(site=site, session_id=session.session_key, utm_source=integration.utm_source, secondary=True)

        lines = data.get('items') or []
        sku_counts = Counter(line.get('offerId') for line in lines)
        unresolved = []
        for line in lines:
            sku = line.get('offerId')
            quantity = line.get('count')
            if not sku or sku_counts[sku] != 1 or type(quantity) is not int or not 0 < quantity <= 32767:
                unresolved.append(sku or 'без артикула')
                continue
            products = Product.objects.filter(article=sku)
            try:
                product = products.get()
            except Product.MultipleObjectsReturned:
                products = products.filter(integration=integration)
                try:
                    product = products.get()
                except (Product.DoesNotExist, Product.MultipleObjectsReturned):
                    unresolved.append(sku)
                    continue
            except Product.DoesNotExist:
                unresolved.append(sku)
                continue
            basket.items.create(product=product, quantity=quantity, ext_discount=_item_discount(product, site, line))

        alert = ''
        if unresolved or not lines:
            missing = ', '.join(dict.fromkeys(unresolved)) if lines else 'заказ без товаров'
            alert = f'Яндекс Маркет: не удалось добавить товары: {missing}'
            logger.warning('Yandex.Market order %s has unresolved order items: %s', order_number, missing)
        order = Order.register(
            basket, integration=integration, delivery_tracking_number=order_number, paid=_is_prepaid(data),
            comment=data.get('notes') or '', alert=alert[:255],
        )
        fields = _delivery_fields(data)
        for field, value in fields.items():
            setattr(order, field, value)
        if fields:
            order.save(update_fields=fields)
    return True


def _cancellation_fields(order, substatus):
    # A new order is cancelled for a reason in EARLY_CANCELLATIONS and becomes a problem for any other, such as
    # SHOP_FAILED. An order already in work gets an alert for the managers instead.
    reason = ORDER_SUBSTATUS.get(substatus, 'Неизвестная причина отмены заказа')
    if order.status == Order.STATUS_NEW:
        status = Order.STATUS_CANCELED if substatus in EARLY_CANCELLATIONS else Order.STATUS_PROBLEM
        info = '\n'.join(filter(None, (order.delivery_info, reason)))
        return {'status': status, 'delivery_info': info}
    if reason in order.delivery_info.splitlines():
        return {}
    return {'alert': reason}


def _sync_order(integration, data):
    with transaction.atomic():
        try:
            order = Order.objects.select_for_update().get(integration=integration, delivery_tracking_number=str(data['orderId']))
        except Order.DoesNotExist:
            return False
        except Order.MultipleObjectsReturned:
            logger.error('Multiple local orders match Yandex.Market order %s in integration %s', data['orderId'], integration.pk)
            return False

        # an order that a manager is editing (the admin sets its owner meanwhile) is left to the next sync
        if order.owner_id or order.status in CLOSED_STATUSES:
            return False

        fields = _delivery_fields(data)
        if _is_prepaid(data):
            fields['paid'] = True

        status, substatus = _market_order_status(data)
        if status == 'CANCELLED':
            fields.update(_cancellation_fields(order, substatus))
        else:
            next_status = DELIVERY_STATUSES.get((status, substatus)) or DELIVERY_STATUSES.get((status, None))
            # statuses are numbered in the order of the workflow, so an order only moves forward
            if next_status and order.status in FULFILLMENT_STATUSES and next_status > order.status:
                fields['status'] = next_status

        changed = {field: value for field, value in fields.items() if getattr(order, field) != value}
        for field, value in changed.items():
            setattr(order, field, value)
        if changed:
            order.save(update_fields=changed)
        return bool(changed)


@shared_task(bind=True, autoretry_for=(OSError, django.db.Error), retry_backoff=30, retry_backoff_max=300)
@sensitive_variables()
def get_integration_orders(self, account, target_site_id=None):
    integration = Integration.get_for_utm_source(account, target_site_id)
    if not integration.enabled or not integration.uses_api or 'ym_campaign' not in (integration.settings or {}):
        return 0
    lock = Lock(ORDER_SYNC_LOCK, integration.pk)
    if not lock.locked:
        return 0
    try:
        campaign_id, business_id = _campaign_ids(integration)
        open_numbers = Order.objects.filter(integration=integration).exclude(status__in=CLOSED_STATUSES).order_by()
        open_ids = sorted({order_id for number in open_numbers.values_list('delivery_tracking_number', flat=True)
                           if (order_id := _positive_id(number)) is not None})
        changed = 0
        for order_ids in batched(open_ids, 50):
            requested = set(order_ids)
            for order in _market_orders(integration, campaign_id, business_id, {'orderIds': list(order_ids)}):
                if order['orderId'] in requested:
                    changed += _sync_order(integration, order)

        status, substatus = AWAITING_PACKING
        filters = {'statuses': [status], 'substatuses': [substatus]}
        for order in _market_orders(integration, campaign_id, business_id, filters):
            if _market_order_status(order) == AWAITING_PACKING:
                changed += _import_order(integration, order)
        return changed
    finally:
        lock.release()


@shared_task(bind=True, queue='integrations', autoretry_for=(OSError, django.db.Error), retry_backoff=30, retry_backoff_max=300)
@sensitive_variables()
def sync_integration_order(self, integration_id, campaign_id, order_id):
    integration = Integration.objects.filter(pk=integration_id, enabled=True, uses_api=True).first()
    market_settings = (integration.settings or {}) if integration else {}
    if not market_settings.get('push_token') or _positive_id(market_settings.get('ym_campaign')) != campaign_id:
        return False

    # Polling and notifications must serialize imports and apply snapshots in fetch order.
    lock = Lock(ORDER_SYNC_LOCK, integration_id)
    if not lock.locked:
        raise MarketUnavailable(f'Yandex.Market order sync is already running for integration {integration_id}')
    try:
        _, business_id = _campaign_ids(integration)
        order = _market_order_by_id(integration, campaign_id, business_id, order_id)
        if order is None:
            return False
        if _market_order_status(order) == AWAITING_PACKING and _import_order(integration, order):
            return True
        return _sync_order(integration, order)
    finally:
        lock.release()


@shared_task
def get_orders():
    total = 0
    for integration in Integration.objects.filter(enabled=True, uses_api=True, settings__has_key='ym_campaign'):
        get_integration_orders.s(integration.utm_source, target_site_id=integration.target_site_id).apply_async(priority=PRIORITY_IDLE)
        total += 1
    return total


def _box_layout(order, market_order):
    market_items = market_order.get('items') or []
    expected = {item['offerId']: item for item in market_items}
    if not expected or len(expected) != len(market_items):
        raise TaskFailure('Не удалось однозначно определить товары заказа Яндекс Маркета')

    boxes = {box_id: Counter() for box_id in order.boxes.values_list('id', flat=True)}
    packed = Counter()
    for item in order.items.select_related('product'):
        sku = item.product.article
        if item.box_id not in boxes or sku not in expected or item.quantity <= 0:
            raise TaskFailure('Комплектация коробок не совпадает с составом заказа Яндекс Маркета')
        boxes[item.box_id][sku] += item.quantity
        packed[sku] += item.quantity

    if packed != {sku: item['count'] for sku, item in expected.items()} or not all(boxes.values()):
        raise TaskFailure('Комплектация коробок не совпадает с количеством товаров заказа Яндекс Маркета')

    return [{'items': [{'id': expected[sku]['id'], 'fullCount': count} for sku, count in items.items()]}
            for items in boxes.values()]


def _box_contents(boxes):
    return [
        sorted((item['id'], item.get('fullCount', 0)) for item in box['items'])
        for box in boxes
    ]


def _report_packing_failure(order_id, message):
    with transaction.atomic():
        order = Order.objects.select_for_update().get(pk=order_id)
        if order.status not in (Order.STATUS_COLLECTED, Order.STATUS_SENT):
            return
        fields = []
        if order.status == Order.STATUS_COLLECTED:
            order.status = Order.STATUS_PROBLEM
            fields.append('status')
        if message not in order.delivery_info.splitlines():
            order.delivery_info = '\n'.join(filter(None, (order.delivery_info, message)))
            fields.append('delivery_info')
        if fields:
            order.save(update_fields=fields)


@shared_task(bind=True, autoretry_for=(OSError, django.db.Error), retry_backoff=30, retry_backoff_max=300)
@sensitive_variables()
def notify_order_status(self, order_id, status, substatus):
    if (status, substatus) != READY_TO_SHIP:
        return None

    lock = Lock('ym.notify_order_status', order_id, wait=True)
    try:
        order = Order.objects.select_related('integration').get(pk=order_id)
        integration = order.integration
        if (order.status not in (Order.STATUS_COLLECTED, Order.STATUS_SENT)
                or not integration or not integration.enabled or not integration.uses_api
                or 'ym_campaign' not in (integration.settings or {})):
            return None

        try:
            market_id = _positive_id(order.delivery_tracking_number)
            if market_id is None:
                raise TaskFailure('В заказе не указан номер заказа Яндекс Маркета')

            campaign_id, business_id = _campaign_ids(integration)
            market_order = _market_order_by_id(integration, campaign_id, business_id, market_id)
            if market_order is None or _market_order_status(market_order) != AWAITING_PACKING:
                return None

            boxes = _box_layout(order, market_order)
            path = f'/v2/campaigns/{campaign_id}/orders/{market_id}'
            existing_boxes = (market_order.get('delivery') or {}).get('boxesLayout') or []
            # A retry after sending the boxes can reuse their labels and any markings already on Market.
            if _box_contents(existing_boxes) != _box_contents(boxes):
                if any(item.get('instances') for box in existing_boxes for item in box['items']):
                    raise TaskFailure('Измените комплектацию заказа с кодами маркировки в Яндекс Маркете')
                result = _market_request(integration, 'PUT', path + '/boxes', {'boxes': boxes, 'allowRemove': False})
                if result.get('status') != 'OK':
                    raise MarketUnavailable(f'Yandex.Market returned an invalid box layout response for order {market_id}')
            result = _market_request(integration, 'PUT', path + '/status', {'order': {'status': status, 'substatus': substatus}})
            if _market_order_status(result.get('order') or {}) != READY_TO_SHIP:
                raise MarketUnavailable(f'Yandex.Market did not confirm ready-for-shipment status for order {market_id}')
            return f'{market_id}: {status} {substatus}'
        except TaskFailure as error:
            _report_packing_failure(order_id, str(error))
            raise
    finally:
        lock.release()


def get_order_details(order_id):
    order = Order.objects.get(id=order_id)
    market_order = order.delivery_tracking_number
    if not market_order:
        raise TaskFailure('Order {} does not have a Yandex.Market order number'.format(order_id))

    campaign_id = order.integration.settings.get('ym_campaign', '')
    api_key = order.integration.settings.get('api_key', '')

    url = 'https://api.partner.market.yandex.ru/v2/campaigns/{campaignId}/orders/{orderId}.json'.format(campaignId=campaign_id, orderId=market_order)
    headers = {
        'Api-Key': api_key,
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
        message = error.get('errors', [{}])[0].get('message', 'Неизвестная ошибка взаимодействия с Яндекс Маркетом')
        raise TaskFailure(message) from e


def get_labels_data(order_id):
    order = Order.objects.get(id=order_id)
    market_order = order.delivery_tracking_number
    if not market_order:
        raise TaskFailure('Order {} does not have a Yandex.Market order number'.format(order_id))

    campaign_id = order.integration.settings.get('ym_campaign', '')
    api_key = order.integration.settings.get('api_key', '')

    url = 'https://api.partner.market.yandex.ru/v2/campaigns/{campaignId}/orders/{orderId}/delivery/labels/data.json'.format(campaignId=campaign_id, orderId=market_order)
    headers = {
        'Api-Key': api_key,
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
        message = error.get('errors', [{}])[0].get('message', 'Неизвестная ошибка взаимодействия с Яндекс Маркетом')
        raise TaskFailure(message) from e


@shared_task(bind=True, autoretry_for=(OSError, django.db.Error), rate_limit='1/s', retry_backoff=300, retry_jitter=False)
def notify_product_stocks(self, products, account, target_site_id=None):
    integration = Integration.get_for_utm_source(account, target_site_id)

    campaign_id = integration.settings.get('ym_campaign', '')
    api_key = integration.settings.get('api_key', '')

    url = 'https://api.partner.market.yandex.ru/campaigns/{campaignId}/offers/stocks'.format(campaignId=campaign_id)
    headers = {
        'Api-Key': api_key,
        'Content-Type': 'application/json'
    }

    updatedAt = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    skus = []

    products = list(Product.objects.filter(pk__in=products))
    counted = Product.get_stocks([product.pk for product in products], integration=integration)
    for product in products:
        skus.append({
            'sku': product.article,
            'items': [
                {
                    'count': max(0, min(20, int(counted[product.pk]))),
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

        for product in products:
            product_integration = ProductIntegration.objects.order_by().filter(product=product, integration=integration).first()
            if product_integration is not None:
                product_integration.notify_stock = False
                product_integration.save()

        return result
    except HTTPError as e:
        content = e.read()
        error = json.loads(content.decode('utf-8'))
        logger.error(error)
        message = error.get('errors', [{}])[0].get('message', 'Неизвестная ошибка взаимодействия с Яндекс Маркетом')
        raise TaskFailure(message) from e


@shared_task(bind=True, autoretry_for=(OSError, django.db.Error, json.decoder.JSONDecodeError), retry_backoff=300, retry_jitter=False)
def notify_marked_stocks(self):
    total = 0
    for integration in Integration.objects.filter(settings__has_key='ym_campaign', enabled=True):
        products = ProductIntegration.objects.order_by().filter(integration=integration, notify_stock=True)
        products = list(products.values_list('product_id', flat=True).distinct())
        if products:
            notify_product_stocks.s(products, integration.utm_source, target_site_id=integration.target_site_id).apply_async(priority=PRIORITY_IDLE)
            total += len(products)
    return total


@shared_task(bind=True, autoretry_for=(OSError, django.db.Error, json.decoder.JSONDecodeError), retry_backoff=300, retry_jitter=False)
def notify_integration_stocks(self):
    """ Sends the stock of every product of the Market integrations, in chunks of 20 a minute apart """
    total = 0
    for integration in Integration.objects.filter(settings__has_key='ym_campaign', enabled=True):
        products = Product.objects.order_by().filter(integration=integration)

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


# The tasks' names from before the beru package became ym. Messages queued under them before the deploy (retries,
# stock chunks with a countdown, a beat that has not restarted yet) are passed on to the tasks under their new names.
# TODO: remove after 2027-01-31, when nothing can be left in the queues
LEGACY_TASKS = {
    'beru.tasks.get_orders': get_orders,
    'beru.tasks.get_integration_orders': get_integration_orders,
    'beru.tasks.sync_integration_order': sync_integration_order,
    'beru.tasks.notify_beru_order_status': notify_order_status,
    'beru.tasks.notify_beru_product_stocks': notify_product_stocks,
    'beru.tasks.notify_beru_marked_stocks': notify_marked_stocks,
    'beru.tasks.notify_beru_integration_stocks': notify_integration_stocks,
}


def _forward(task):
    def forward(*args, **kwargs):
        return task.apply_async(args, kwargs).id
    forward.__name__ = f'forward_{task.__name__}'
    return forward


for _name, _task in LEGACY_TASKS.items():
    shared_task(name=_name, ignore_result=True)(_forward(_task))
