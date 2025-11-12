import logging
from datetime import datetime
import decimal
import json
from functools import wraps

from decimal import Decimal

from django.contrib.auth import SESSION_KEY
from django.http import HttpResponse, JsonResponse, HttpResponseForbidden, HttpResponseBadRequest
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.utils.formats import date_format

from shop.models import Product, Basket, Order, ShopUser, Integration, ProductIntegration


logger = logging.getLogger('beru')


def token_required(func):
    @wraps(func)
    def _wrapped_view(request, *args, **kwargs):
        integration = Integration.objects.filter(utm_source=kwargs.get('account', 'beru')).first()
        if integration is None or not integration.settings:
            return HttpResponseForbidden()
        if request.META.get('HTTP_AUTHORIZATION', None) != integration.settings.get('token', ''):
            return HttpResponseForbidden()
        return func(request, *args, **kwargs)
    return _wrapped_view


@require_POST
@csrf_exempt
@token_required
def cart(request, account='beru'):
    if request.body:
        data = json.loads(request.body.decode('utf-8'))
    else:
        data = json.loads("""
        {"cart": {"currency": "RUR", "delivery": {"region": {"parent": {"parent": {"parent": {"name": "Россия", "id": 225, "type": "COUNTRY"}, "name": "Центральный федеральный округ", "id": 3, "type": "COUNTRY_DISTRICT"}, "name": "Москва и Московская область", "id": 1, "type": "SUBJECT_FEDERATION"}, "name": "Москва", "id": 213, "type": "CITY"}}, "items": [{"sku": "1808809720", "shopSku": "ЦБ-0200637", "params": "Цвет товара: белый/серый", "offerName": "Швейная машина Singer Confidence 7640 Q, белый/серый", "offerId": "ЦБ-0200637", "count": 1, "feedId": 614439, "fulfilmentShopId": 575686}]}}
        """)
    logger.info('>>> ' + request.path)
    logger.debug(data)
    integration = Integration.objects.filter(utm_source=account).first()
    response = {'cart': {'items': []}}
    for item in data.get('cart', {}).get('items', []):
        try:
            sku = item.get('offerId', '#NO_SKU#')
            product = Product.objects.get(article=sku)
            product_integration = ProductIntegration.objects.filter(product=product, integration=integration).first()
            price = product_integration.price if product_integration.price > 0 else product.price
            response['cart']['items'].append({
                'feedId': item.get('feedId', 0),
                'offerId': sku,
                'count': min(item.get('count', 0), max(product.get_stock(integration), 0)),
                'price': int(price.to_integral_value(rounding=decimal.ROUND_UP)),
                'delivery': True
            })
        except Exception as e:
            logger.exception(e)
            response['cart']['items'].append({
                'feedId': item.get('feedId', 0),
                'offerId': sku,
                'count': 0,
                'delivery': False
            })
    return JsonResponse(response)


@require_POST
@csrf_exempt
@token_required
def accept_order(request, account='beru'):
    if request.body:
        data = json.loads(request.body.decode('utf-8'))
    else:
        data = json.loads("""
        {"order":{"id":8920689,"fake":true,"currency":"RUR","paymentType":"POSTPAID","paymentMethod":"CASH_ON_DELIVERY","taxSystem":"USN","delivery":{"type":"DELIVERY","price":249,"vat":"VAT_20","serviceName":"Доставка","id":"vujQrQNMAdM1cYADVSGnQEsID4jiUVQLGGXCp2U/4KBoJORjzponBenm38cqEfeS6ebfxyoR95LZPDROqLDWylb8Jw+EOb6MmQh4GTRzKtU=","hash":"vujQrQNMAdM1cYADVSGnQEsID4jiUVQLGGXCp2U/4KBoJORjzponBenm38cqEfeS6ebfxyoR95LZPDROqLDWylb8Jw+EOb6MmQh4GTRzKtU=","deliveryServiceId":1003937,"deliveryPartnerType":"YANDEX_MARKET","dates":{"fromDate":"29-09-2019","toDate":"29-09-2019"},"region":{"id":213,"name":"Москва","type":"CITY","parent":{"id":1,"name":"Москва и Московская область","type":"SUBJECT_FEDERATION","parent":{"id":3,"name":"Центральный федеральный округ","type":"COUNTRY_DISTRICT","parent":{"id":225,"name":"Россия","type":"COUNTRY"}}}}},"items":[{"id":15296429,"feedId":614439,"offerId":"ЦБ-0200642","offerName":"Швейная машина Singer Studio 12, белый","price":11990,"buyer-price":11990,"count":1,"delivery":true,"params":"Цвет товара: белый","vat":"NO_VAT","fulfilmentShopId":575686,"sku":"1808809549","shopSku":"ЦБ-0200642"}]}}
        """)
    logger.info('>>> ' + request.path)
    logger.debug(data)
    beru_order = data.get('order', {})

    order_id = beru_order.get('id', None)
    order = Order.objects.filter(delivery_tracking_number=order_id).first()  # Beru sometimes registers same order several times
    if order is not None:
        return JsonResponse({"order": {"accepted": True, "id": str(order.id)}})

    user = ShopUser.objects.get(phone='0000')
    integration = Integration.objects.filter(utm_source=account).first()

    if not request.session.session_key:
        request.session.save()
        request.session.modified = True
    request.session[SESSION_KEY] = user._meta.pk.value_to_string(user)
    request.session.save()
    basket = Basket.objects.create(site=integration.site, session_id=request.session.session_key, utm_source=account, secondary=True)

    for beru_item in beru_order.get('items', []):
        try:
            sku = beru_item.get('offerId', '#NO_SKU#')
            product = Product.objects.get(article=sku)
            price = beru_item.get('price', 0) + beru_item.get('subsidy', 0)
            count = beru_item.get('count', 0)
            item, _ = basket.items.get_or_create(product=product)
            item.quantity = count
            if product.price > price:
                item.ext_discount = product.price - Decimal(price)
            item.save()
        except Exception as e:
            logger.exception(e)
            return JsonResponse({"order": {"accepted": False, "reason": "OUT_OF_DATE"}})

    basket.save()

    kwargs = {
        'integration': integration,
        'delivery_tracking_number': order_id
    }
    if integration.settings.get('is_taxi', False):
        kwargs['delivery'] = Order.DELIVERY_EXPRESS

    order = Order.register(basket, **kwargs)

    address = []
    delivery = beru_order.get('delivery', {})
    region = delivery.get('region', {})
    while region:
        name = region.get('name', None)
        if name:
            address.append(name)
            if region.get('type', '') == 'CITY':
                order.city = name
        region = region.get('parent', None)
    if address:
        order.address = ', '.join(address)

    date = delivery.get('dates', {}).get('fromDate', None)
    if date:
        order.delivery_handing_date = datetime.strptime(date, '%d-%m-%Y')
        from_time = delivery.get('dates', {}).get('fromTime', None)
        till_time = delivery.get('dates', {}).get('toTime', None)
        if from_time:
            order.delivery_time_from = datetime.strptime(from_time, '%H:%M')
        if till_time:
            order.delivery_time_till = datetime.strptime(till_time, '%H:%M')

    date = delivery.get('shipments', [{}])[0].get('shipmentDate', None)
    if date:
        order.delivery_dispatch_date = datetime.strptime(date, '%d-%m-%Y')

    order.comment = beru_order.get('notes', '')
    order.save()

    return JsonResponse({"order": {"accepted": True, "id": str(order.id)}})


BERU_ORDER_SUBSTATUS = {
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


@require_POST
@csrf_exempt
@token_required
def order_status(request, account='beru'):
    if request.body:
        data = json.loads(request.body.decode('utf-8'))
    else:
        data = json.loads("""
        {'order': {'substatus': 'STARTED', 'delivery': {'serviceName': 'Доставка', 'deliveryPartnerType': 'YANDEX_MARKET', 'price': 249, 'type': 'DELIVERY', 'shipments': [{'height': 52, 'width': 21, 'depth': 67, 'status': 'NEW', 'weight': 1001}], 'region': {'id': 2, 'parent': {'id': 10174, 'parent': {'id': 17, 'parent': {'id': 225, 'name': 'Россия', 'type': 'COUNTRY'}, 'name': 'Северо-Западный федеральный округ', 'type': 'COUNTRY_DISTRICT'}, 'name': 'Санкт-Петербург и Ленинградская область', 'type': 'SUBJECT_FEDERATION'}, 'name': 'Санкт-Петербург', 'type': 'CITY'}, 'deliveryServiceId': 1003937, 'vat': 'VAT_20', 'dates': {'fromDate': '30-09-2019', 'toDate': '30-09-2019'}}, 'total': 20049, 'paymentMethod': 'CASH_ON_DELIVERY', 'currency': 'RUR', 'status': 'PROCESSING', 'itemsTotal': 19800, 'creationDate': '26-09-2019 17:50:21', 'taxSystem': 'USN', 'paymentType': 'POSTPAID', 'fake': True, 'items': [{'count': 1, 'offerName': 'Швейная машина Singer Confidence 7640 Q, белый/серый', 'feedId': 614439, 'buyer-price': 19800, 'offerId': 'ЦБ-0200637', 'sku': '1808809720', 'price': 19800, 'shopSku': 'ЦБ-0200637', 'params': 'Цвет товара: белый/серый', 'id': 15350984, 'fulfilmentShopId': 575686, 'vat': 'NO_VAT'}], 'id': 8943125}}
        """)
    logger.info('>>> ' + request.path)
    logger.debug(data)
    beru_order = data.get('order', {})
    order_id = str(beru_order.get('id', 0))
    try:
        order = Order.objects.get(delivery_tracking_number=order_id)
        if order.integration is None:  # этого не должно быть, но иногда бывает, когда заказ добавляют руками
            return HttpResponse('')
        status = beru_order.get('status', 'UNKNOWN')
        if status == 'PROCESSING':  # заказ начал обрабатываться в Беру!
            order.status = Order.STATUS_ACCEPTED
            if beru_order.get('paymentType', 'UNKNOWN') == 'PREPAID':
                order.paid = True
        elif status == 'PICKUP':  # заказ доставлен в пункт самовывоза
            order.status = Order.STATUS_DELIVERED
        elif status == 'DELIVERED':  # заказ получен покупателем
            is_taxi = order.integration.settings.get('is_taxi', False)
            if is_taxi:
                info = 'Доставлен покупателю в {}'.format(date_format(timezone.localtime(timezone.now()), "DATETIME_FORMAT"))
                if order.delivery_info:
                    order.delivery_info = '\n'.join([order.delivery_info, info])
                else:
                    order.delivery_info = info
            else:
                order.status = Order.STATUS_DONE
        elif status == 'CANCELLED':  # заказ отменен
            substatus = beru_order.get('substatus', '')
            info = BERU_ORDER_SUBSTATUS.get(substatus, "Неизвестная причина отмены заказа")
            if order.status in (Order.STATUS_NEW, Order.STATUS_CANCELED):  # меняем статус только, если заказ не обрабатывается
                if substatus in ('REPLACING_ORDER', 'RESERVATION_EXPIRED', 'USER_CHANGED_MIND', 'USER_NOT_PAID', 'USER_REFUSED_DELIVERY',
                                 'USER_UNREACHABLE', 'USER_BOUGHT_CHEAPER', 'BANK_REJECT_CREDIT_OFFER', 'USER_PLACED_OTHER_ORDER'):
                    order.status = Order.STATUS_CANCELED
                elif substatus in ('PROCESSING_EXPIRED', 'SHOP_FAILED', 'USER_REFUSED_PRODUCT', 'USER_REFUSED_QUALITY'):
                    order.status = Order.STATUS_PROBLEM
                else:
                    order.status = Order.STATUS_PROBLEM
                if order.delivery_info:
                    order.delivery_info = '\n'.join([order.delivery_info, info])
                else:
                    order.delivery_info = info
            else:  # если заказ в обработке, выставляем флаг тревоги, не меняя статус
                order.alert = info
        elif status == 'DELIVERY':  # заказ передан в службу доставки
            pass  # ничего не меняем, так как с нашей стороны статус уже установлен
        elif status == 'UNPAID':
            pass

        delivery = beru_order.get('delivery', {})
        date = delivery.get('dates', {}).get('fromDate', None)
        if date:
            order.delivery_handing_date = datetime.strptime(date, '%d-%m-%Y')
            from_time = delivery.get('dates', {}).get('fromTime', None)
            till_time = delivery.get('dates', {}).get('toTime', None)
            if from_time:
                order.delivery_time_from = datetime.strptime(from_time, '%H:%M')
            if till_time:
                order.delivery_time_till = datetime.strptime(till_time, '%H:%M')

        date = delivery.get('shipments', [{}])[0].get('shipmentDate', None)
        if date:
            order.delivery_dispatch_date = datetime.strptime(date, '%d-%m-%Y')

        order.save()
    except Order.MultipleObjectsReturned:
        logger.error("Ошибка поиска внутреннего заказа с заказом Беру №{}".format(order_id))
        return HttpResponse("Ошибка поиска внутреннего заказа с заказом Беру №{}".format(order_id))
    except Order.DoesNotExist:
        logger.error("Не существует внутреннего заказа с заказом Беру №{}".format(order_id))
        return HttpResponse("Не существует внутреннего заказа с заказом Беру №{}".format(order_id))
        # return HttpResponseBadRequest("Не существует внутреннего заказа с заказом Беру №{}".format(order_id))

    return HttpResponse('')
