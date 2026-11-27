"""
Ozon FBS postings (orders) and stocks.

get_unfulfilled_orders polls the postings of the last week of every enabled Ozon integration and registers the new ones.
An integration with a push_token in its settings also takes Ozon's push notifications (views.notifications), each
of which syncs one posting. For such an integration polling and pushes also "reconcile": they apply cancellations,
delivery statuses and the shipment date to the orders already registered.

Stocks go to Ozon for the products whose ProductIntegration.notify_stock is set, see notify_marked_stocks.
"""
import json
import logging
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
from importlib import import_module
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from django.conf import settings
from django.contrib import auth
from django.db import Error as DatabaseError, transaction
from django.utils import timezone
from django.utils.functional import SimpleLazyObject
from django.views.decorators.debug import sensitive_variables

from celery import shared_task

from sewingworld.tasks import PRIORITY_IDLE

from shop.integration_health import IntegrationFailure, monitor, read_body
from shop.models import Integration, Basket, Order, Product, ProductIntegration, ShopUser

logger = logging.getLogger('ozon')


class TaskFailure(IntegrationFailure):
    pass


OZON_API = 'https://api-seller.ozon.ru'


FBS_IMPORT_STATUSES = (
    'awaiting_registration', 'awaiting_approve', 'awaiting_packaging',
    'awaiting_deliver', 'delivering', 'delivered',
)
FBS_CANCELLATIONS = {'cancelled', 'cancelled_from_split_pending'}
FBS_CANCELLATION_ALERT = 'Ozon: отправление отменено'
FBS_DELIVERY_STATUSES = {
    'delivering': Order.STATUS_SENT,
    'sent_by_seller': Order.STATUS_SENT,
    'delivered': Order.STATUS_DELIVERED,
}
FULFILLMENT_STATUSES = (
    Order.STATUS_NEW, Order.STATUS_ACCEPTED, Order.STATUS_WAITING, Order.STATUS_COLLECTING,
    Order.STATUS_COLLECTED, Order.STATUS_DELIVERED_STORE, Order.STATUS_SENT,
)
RETRYABLE_ERRORS = (OSError, DatabaseError, json.JSONDecodeError)


@sensitive_variables()
def _ozon_request(integration, endpoint, data):
    headers = {
        'Client-Id': integration.settings.get('client_id', ''),
        'Api-Key': integration.settings.get('api_key', ''),
        'Content-Type': 'application/json',
    }
    request = Request(f'{OZON_API}{endpoint}', json.dumps(data).encode(), headers, method='POST')
    try:
        with urlopen(request, timeout=15) as response:
            return json.load(response)
    except HTTPError as error:
        # An HTTPError is an OSError, which the tasks retry; the 404 of a single posting is left to the caller.
        # Other errors fail the task with Ozon's message, and the integration's health keeps the whole reply.
        if error.code == 429 or error.code >= 500 or (error.code == 404 and endpoint == '/v3/posting/fbs/get'):
            raise
        body = read_body(error)
        logger.error('Ozon request to %s failed with HTTP %s for integration %s: %s', endpoint, error.code, integration.pk, body)
        try:
            message = json.loads(body).get('message')
        except (ValueError, AttributeError):
            message = None
        raise TaskFailure(message or f'Ошибка взаимодействия с Ozon (HTTP {error.code})', status=error.code, body=body) from error


def _order_session():
    """ A session of the service user of Ozon orders: Order.register() takes the buyer from the basket's session """
    user = ShopUser.objects.get(phone='0002')
    session = import_module(settings.SESSION_ENGINE).SessionStore()
    session[auth.SESSION_KEY] = user._meta.pk.value_to_string(user)
    session[auth.BACKEND_SESSION_KEY] = settings.AUTHENTICATION_BACKENDS[0]
    session[auth.HASH_SESSION_KEY] = user.get_session_auth_hash()
    session.save()
    return session


@sensitive_variables()
def _register_posting(integration, posting, session):
    basket = Basket.objects.create(
        site=integration.source_site, session_id=session.session_key, utm_source=integration.utm_source, secondary=True,
    )
    for ozon_item in posting.get('products') or []:
        article = ozon_item.get('offer_id', '#NO_OFFER_ID#')
        try:
            product = Product.objects.get(article=article)
            price = ozon_item.get('price')
            # The list returns an amount object, while the detail endpoint returns a string.
            if isinstance(price, dict):
                price = price.get('amount')
            price = Decimal(price or '0')
            discount = max(Decimal(0), product.price - price)
        except (Product.DoesNotExist, Product.MultipleObjectsReturned, InvalidOperation, TypeError):
            logger.warning('Could not add Ozon product %s to posting %s', article, posting['posting_number'])
            continue
        item, _ = basket.items.get_or_create(product=product)
        item.quantity = ozon_item.get('quantity', 0)
        item.ext_discount = discount
        item.save()

    basket.save()

    fields = {'integration': integration, 'delivery_tracking_number': posting['posting_number']}
    if posting.get('is_express'):
        fields['delivery'] = Order.DELIVERY_EXPRESS
    if posting.get('shipment_date'):
        fields['delivery_dispatch_date'] = date.fromisoformat(posting['shipment_date'].split('T')[0])
    return Order.register(basket, **fields)


def _status_fields(order, status):
    # A cancelled posting cancels a new order, while an order already in work gets an alert for the managers, once.
    # Delivery statuses only move an order forward (statuses are numbered in the order of the workflow), and never
    # one that has the cancellation alert.
    if status in FBS_CANCELLATIONS:
        if order.status == Order.STATUS_NEW:
            return {'status': Order.STATUS_CANCELED}
        if order.status in (*FULFILLMENT_STATUSES, Order.STATUS_PROBLEM):
            if FBS_CANCELLATION_ALERT not in order.alert.splitlines():
                alert = '\n'.join(filter(None, (FBS_CANCELLATION_ALERT, order.alert)))
                return {'alert': alert[:Order._meta.get_field('alert').max_length]}
    else:
        next_status = FBS_DELIVERY_STATUSES.get(status)
        if (next_status and order.status in FULFILLMENT_STATUSES and order.status < next_status
                and FBS_CANCELLATION_ALERT not in order.alert.splitlines()):
            return {'status': next_status}
    return {}


def _warehouse_ids(integration):
    # Several integrations can share one seller account (ozon and ozon_rfbs do), whose posting list holds the
    # postings of all its warehouses. Each integration takes only the postings of its own warehouses.
    return list(dict.fromkeys(str(warehouse['id']) for warehouse in integration.settings.get('warehouses', []) if warehouse.get('id')))


@sensitive_variables()
def _sync_posting(integration, posting, session, *, reconcile):
    posting_number = posting.get('posting_number')
    if not posting_number:
        return False
    warehouses = _warehouse_ids(integration)
    warehouse_id = (posting.get('delivery_method') or {}).get('warehouse_id')
    if warehouses and warehouse_id and str(warehouse_id) not in warehouses:
        return False

    status = posting.get('status')
    with transaction.atomic():
        # Serialize poll and push imports of all Ozon integrations before an Order row exists: they may share an account.
        ozon_integrations = Integration.objects.filter(source_site_id=integration.source_site_id)
        list(ozon_integrations.select_for_update(no_key=True).order_by('pk').values_list('pk', flat=True))
        # Posting numbers are unique on Ozon, so the posting may already be the order of another integration.
        order = (Order.objects.select_for_update().order_by('pk')
                 .filter(integration__in=ozon_integrations, delivery_tracking_number=posting_number).first())
        if order is not None and order.integration_id != integration.pk:
            logger.warning('Ozon posting %s of integration %s is already order %s of integration %s',
                           posting_number, integration.pk, order.pk, order.integration_id)
            return False
        if order is None:
            if reconcile and status not in FBS_IMPORT_STATUSES:
                return False
            order = _register_posting(integration, posting, session)

        fields = {}
        scanit = posting.get('scanit')
        if scanit:
            fields['meta'] = {**(order.meta or {}), 'barcode': scanit}

        analytics_data = posting.get('analytics_data') or {}
        region = analytics_data.get('region')
        city = analytics_data.get('city')
        if city:
            fields['city'] = city
        if region or city:
            fields['address'] = ', '.join(dict.fromkeys(filter(None, (region, city))))
        delivery_date = analytics_data.get('delivery_date_end')
        if delivery_date:
            fields['delivery_handing_date'] = date.fromisoformat(delivery_date.split('T')[0])

        if reconcile:
            if posting.get('shipment_date'):
                fields['delivery_dispatch_date'] = date.fromisoformat(posting['shipment_date'].split('T')[0])
            fields.update(_status_fields(order, status))

        changed = {field: value for field, value in fields.items() if getattr(order, field) != value}
        for field, value in changed.items():
            setattr(order, field, value)
        if changed:
            order.save(update_fields=changed)
    return True


@shared_task(bind=True, autoretry_for=RETRYABLE_ERRORS, retry_backoff=300, retry_jitter=False)
@sensitive_variables()
def get_integration_unfulfilled_orders(self, account, target_site_id=None):
    integration = Integration.get_for_utm_source(account, target_site_id)
    session = SimpleLazyObject(_order_session)
    reconcile = bool(integration.settings.get('push_token'))
    statuses = list(FBS_IMPORT_STATUSES)
    if reconcile:
        # The list doesn't filter by sent_by_seller, an rFBS status (Ozon rejects the request); pushes bring it
        statuses.append('cancelled')
    now = timezone.now().replace(microsecond=0)
    week_ago = now - timedelta(days=7)
    data = {
        'sort_dir': 'DESC',
        'filter': {'since': week_ago.isoformat(), 'to': now.isoformat(), 'statuses': statuses},
        'limit': 100,
        'with': {'analytics_data': True, 'financial_data': True, 'barcodes': True},
    }
    warehouses = _warehouse_ids(integration)
    if warehouses:
        data['filter']['warehouse_ids'] = warehouses

    num = 0
    with monitor(integration, self.name):
        while True:
            result = _ozon_request(integration, '/v4/posting/fbs/list', data)
            for posting in result.get('postings', []):
                num += _sync_posting(integration, posting, session, reconcile=reconcile)
            if not result.get('has_next'):
                return num
            cursor = result.get('cursor')
            if not cursor or cursor == data.get('cursor'):
                raise TaskFailure('Ozon omitted the next posting cursor')
            data['cursor'] = cursor


@shared_task(bind=True, queue='integrations', autoretry_for=RETRYABLE_ERRORS, retry_backoff=30, retry_backoff_max=300)
@sensitive_variables()
def sync_integration_posting(self, integration_id, posting_number):
    integration = Integration.objects.filter(pk=integration_id, source_site__domain='ozon.ru', enabled=True).first()
    if integration is None or not (integration.settings or {}).get('push_token'):
        return False

    data = {'posting_number': posting_number, 'with': {'analytics_data': True, 'barcodes': True}}
    with monitor(integration, self.name):
        try:
            result = _ozon_request(integration, '/v3/posting/fbs/get', data)
        except HTTPError as error:
            if error.code == 404:
                logger.info('Ozon FBS posting %s is unavailable for integration %s', posting_number, integration_id)
                return False
            raise
        posting = result.get('result') or {}
        if posting.get('posting_number') != posting_number:
            raise TaskFailure('Ozon returned an unexpected posting number')
        return _sync_posting(integration, posting, SimpleLazyObject(_order_session), reconcile=True)


@shared_task
def get_unfulfilled_orders():
    total = 0
    for integration in Integration.objects.filter(source_site__domain='ozon.ru', enabled=True):
        get_integration_unfulfilled_orders.s(integration.utm_source, target_site_id=integration.target_site_id).apply_async(priority=PRIORITY_IDLE)
        total += 1
    return total


@shared_task(bind=True, autoretry_for=RETRYABLE_ERRORS, rate_limit='1/s', retry_backoff=300, retry_jitter=False)
def notify_product_stocks(self, products, account, target_site_id=None):
    integration = Integration.get_for_utm_source(account, target_site_id)

    stocks = []
    sent = []

    products = list(Product.objects.filter(pk__in=products))
    counted = Product.get_stocks([product.pk for product in products], integration=integration)
    counted_express = Product.get_stocks([product.pk for product in products], integration=integration, express=True)
    # At most 20 of a product; express warehouses get the stock of the integration's express suppliers
    for product in products:
        stock = max(0, min(20, int(counted[product.pk])))
        express_stock = max(0, min(20, int(counted_express[product.pk])))
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
        sent.append(product)
        if len(stocks) > 99:
            break

    data = {'stocks': stocks}
    logger.debug(data)
    with monitor(integration, self.name) as outcome:
        result = _ozon_request(integration, '/v2/products/stocks', data)
        logger.debug(result)
        # A row per product and warehouse, such as
        # {'warehouse_id': 22936068942000, 'product_id': 0, 'offer_id': 'в92086', 'updated': False,
        #  'errors': [{'code': 'TOO_MANY_REQUESTS', 'message': 'too many requests'}]}
        # A product limited by the rate keeps notify_stock for the next run. Other errors are the integration's
        # failure, and the product waits for its stock to change again.
        pending = set()
        errors = []
        for row in result.get('result', []):
            if row.get('updated', True):
                continue
            row_errors = row.get('errors') or []
            codes = {error.get('code') for error in row_errors}
            if codes and codes <= {'TOO_MANY_REQUESTS'}:
                pending.add(row.get('offer_id'))
            else:
                described = '; '.join(f"{error.get('code')}: {error.get('message')}" for error in row_errors) or 'не обновлён'
                errors.append(f"{row.get('offer_id')}, склад {row.get('warehouse_id')}: {described}")

        for product in sent:
            if product.article not in pending:
                ProductIntegration.objects.filter(product=product, integration=integration).update(notify_stock=False)

        if errors:
            logger.error('Ozon rejected stocks of integration %s: %s', integration.pk, errors)
            outcome.fail('Ozon не принял остатки:\n' + '\n'.join(errors))
    return None


@shared_task(bind=True, autoretry_for=(OSError, DatabaseError, json.decoder.JSONDecodeError), retry_backoff=300, retry_jitter=False)
def notify_marked_stocks(self):
    total = 0
    for integration in Integration.objects.filter(source_site__domain='ozon.ru', enabled=True):
        products = ProductIntegration.objects.order_by().filter(integration=integration, notify_stock=True)
        products = list(products.values_list('product_id', flat=True).distinct())
        if products:
            notify_product_stocks.s(products, integration.utm_source, target_site_id=integration.target_site_id).apply_async(priority=PRIORITY_IDLE)
            total += len(products)
    return total
