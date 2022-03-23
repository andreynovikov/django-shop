import base64
import logging
import json
from datetime import datetime
from functools import wraps

from decimal import Decimal

from django.conf import settings
from django.contrib.auth import SESSION_KEY
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt

from shop.models import Product, Basket, BasketItem, Order, ShopUser


logger = logging.getLogger('sber')

SBER_MARKET = getattr(settings, 'SBER_MARKET', {})


def token_required(func):
    @wraps(func)
    def _wrapped_view(request, *args, **kwargs):
        if request.META.get('HTTP_AUTHORIZATION', None) != SBER_MARKET.get('token', ''):
            return HttpResponseForbidden()
        return func(request, *args, **kwargs)
    return _wrapped_view


def auth_required(func):
    @wraps(func)
    def _wrapped_view(request, *args, **kwargs):
        if 'HTTP_AUTHORIZATION' in request.META:
            auth = request.META['HTTP_AUTHORIZATION'].split()
            if len(auth) == 2:
                if auth[0].lower() == "basic":
                    uname, passwd = base64.b64decode(auth[1]).decode('utf8').split(':', 1)
                    if uname == SBER_MARKET.get('auth_user', '') and passwd == SBER_MARKET.get('auth_password', ''):
                        return func(request, *args, **kwargs)
        return HttpResponseForbidden()
    return _wrapped_view


@require_POST
@csrf_exempt
@auth_required
def new_order(request):
    data = json.loads(request.body.decode('utf-8'))
    logger.info('>>> ' + request.path)
    logger.debug(data)
    sber_order = data.get('data', {})

    user = ShopUser.objects.get(phone='0001')

    if not request.session.session_key:
        request.session.save()
        request.session.modified = True
    request.session[SESSION_KEY] = user._meta.pk.value_to_string(user)
    request.session.save()

    for shipment in sber_order.get('shipments', []):
        basket = Basket.objects.create(session_id=request.session.session_key, utm_source='sber', secondary=True)

        for sber_item in shipment.get('items', []):
            try:
                item_index = sber_item.get('itemIndex', '-1')
                offer_id = sber_item.get('offerId', '#NO_SKU#')
                product = Product.objects.get(pk=offer_id)
                price = sber_item.get('price', 0)
                quantity = sber_item.get('quantity', 0)
                item = BasketItem(basket=basket, product=product, quantity=quantity, meta={'itemIndex': item_index})
                if product.price > price:
                    item.ext_discount = product.price - Decimal(price)
                item.save()
            except Exception as e:
                logger.exception(e)
                return JsonResponse({"success": 0, "meta": {}, "error": {"message": str(e)}})

        basket.save()
        order = Order.register(basket)

        full_address = []
        delivery = shipment.get('label', {})
        region = delivery.get('region', None)
        if region:
            full_address.append(region)
        city = delivery.get('city', None)
        if city:
            if city != region:
                full_address.append(city)
            order.city = city
        address = delivery.get('address', None)
        if address:
            full_address.append(address)

        if full_address:
            order.address = ', '.join(full_address)

        full_name = delivery.get('fullName', None)
        if full_name:
            order.name = full_name

        date = shipment.get('shipping', {}).get('shippingDate', None)
        if date:
            order.delivery_dispatch_date = datetime.strptime(date.split('T')[0], '%Y-%m-%d')

        order.delivery_tracking_number = shipment.get('shipmentId', None)

        order.status = Order.STATUS_ACCEPTED  # автоматическое подтверждение сработает по сигналу смены статуса
        order.save()

    return JsonResponse({"data": {}, "meta": {"id": str(order.id)}, "success": 1})


@require_POST
@csrf_exempt
@auth_required
def cancel_order(request):
    data = json.loads(request.body.decode('utf-8'))
    logger.info('>>> ' + request.path)
    logger.debug(data)
    sber_order = data.get('data', {})

    for shipment in sber_order.get('shipments', []):
        shipment_id = shipment.get('shipmentId', None)
        try:
            order = Order.objects.get(delivery_tracking_number=shipment_id)
            deleted_items = []
            for sber_item in shipment.get('items', []):
                item_index = sber_item.get('itemIndex', '-1')
                offer_id = sber_item.get('offerId', '#NO_SKU#')
                item = order.items.get(meta__itemIndex=item_index)
                if str(item.product.id) != offer_id:
                    raise Exception('Wrong product SKU')
                deleted_items.append(item)  # Сбер поддерживает частичную отмену заказа
            if order.items.count() == len(deleted_items):
                order.alert = 'Заказ отменён'
            else:
                codes = ', '.join([item.product.code for item in deleted_items])
                order.alert = 'Удалены некоторые позиции заказа: {}'.format(codes)
            order.save()
        except Exception as e:
            logger.exception(e)
            return JsonResponse({"success": 0, "meta": {}, "error": {"message": str(e)}})

    return JsonResponse({"data": {}, "meta": {"id": str(order.id)}, "success": 1})
