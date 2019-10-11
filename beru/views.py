import sys
from datetime import datetime
import decimal
import json
from functools import wraps

from django.conf import settings
from django.contrib.auth import SESSION_KEY
from django.http import HttpResponse, JsonResponse, HttpResponseForbidden, HttpResponseBadRequest
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt

from shop.models import Product, Basket, Order, ShopUser


BERU_TOKEN = getattr(settings, 'BERU_TOKEN', '')


def token_required(func):
    @wraps(func)
    def _wrapped_view(request, *args, **kwargs):
        if request.META.get('HTTP_AUTHORIZATION', None) != BERU_TOKEN:
            return HttpResponseForbidden()
        return func(request, *args, **kwargs)
    return _wrapped_view


@require_POST
@csrf_exempt
@token_required
def stocks(request):
    if request.body:
        data = json.loads(request.body.decode('utf-8'))
    else:
        data = json.loads("""
        { "warehouseId": 1234, "skus": [ "01057", "00159" ] }
        """)
    skus = []
    warehouseId = data.get('warehouseId', '')
    updatedAt = datetime.utcnow().replace(microsecond=0).isoformat() + '+00:00'
    for sku in data.get('skus', []):
        try:
            product = Product.objects.get(article=sku)
            count = int(product.instock)
            if count < 0:
                count = 0
            skus.append({
                'sku': sku,
                'warehouseId': str(warehouseId),
                'items': [
                    {
                        'type': 'FIT',
                        'count': str(count),
                        'updatedAt': updatedAt
                    }
                ]
            })
        except Exception:
            pass
    return JsonResponse({'skus': skus})


@require_POST
@csrf_exempt
@token_required
def cart(request):
    if request.body:
        data = json.loads(request.body.decode('utf-8'))
    else:
        data = json.loads("""
        {"cart": {"currency": "RUR", "delivery": {"region": {"parent": {"parent": {"parent": {"name": "Россия", "id": 225, "type": "COUNTRY"}, "name": "Центральный федеральный округ", "id": 3, "type": "COUNTRY_DISTRICT"}, "name": "Москва и Московская область", "id": 1, "type": "SUBJECT_FEDERATION"}, "name": "Москва", "id": 213, "type": "CITY"}}, "items": [{"sku": "1808809720", "shopSku": "ЦБ-0200637", "params": "Цвет товара: белый/серый", "offerName": "Швейная машина Singer Confidence 7640 Q, белый/серый", "offerId": "ЦБ-0200637", "count": 1, "feedId": 614439, "fulfilmentShopId": 575686}]}}
        """)
    print(data, file=sys.stderr)
    response = {'cart': {'items': []}}
    for item in data.get('cart', {}).get('items', []):
        try:
            sku = item.get('offerId', '#NO_SKU#')
            product = Product.objects.get(article=sku)
            response['cart']['items'].append({
                'feedId': item.get('feedId', 0),
                'offerId': sku,
                'count': min(item.get('count', 0), product.instock),
                'price': int(product.beru_price.to_integral_value(rounding=decimal.ROUND_UP)),
                'delivery': True
            })
        except Exception as e:
            print(str(e), file=sys.stderr)
            item['delivery'] = False
    return JsonResponse(response)


@require_POST
@csrf_exempt
@token_required
def accept_order(request):
    if request.body:
        data = json.loads(request.body.decode('utf-8'))
    else:
        data = json.loads("""
        {"order":{"id":8920689,"fake":true,"currency":"RUR","paymentType":"POSTPAID","paymentMethod":"CASH_ON_DELIVERY","taxSystem":"USN","delivery":{"type":"DELIVERY","price":249,"vat":"VAT_20","serviceName":"Доставка","id":"vujQrQNMAdM1cYADVSGnQEsID4jiUVQLGGXCp2U/4KBoJORjzponBenm38cqEfeS6ebfxyoR95LZPDROqLDWylb8Jw+EOb6MmQh4GTRzKtU=","hash":"vujQrQNMAdM1cYADVSGnQEsID4jiUVQLGGXCp2U/4KBoJORjzponBenm38cqEfeS6ebfxyoR95LZPDROqLDWylb8Jw+EOb6MmQh4GTRzKtU=","deliveryServiceId":1003937,"deliveryPartnerType":"YANDEX_MARKET","dates":{"fromDate":"29-09-2019","toDate":"29-09-2019"},"region":{"id":213,"name":"Москва","type":"CITY","parent":{"id":1,"name":"Москва и Московская область","type":"SUBJECT_FEDERATION","parent":{"id":3,"name":"Центральный федеральный округ","type":"COUNTRY_DISTRICT","parent":{"id":225,"name":"Россия","type":"COUNTRY"}}}}},"items":[{"id":15296429,"feedId":614439,"offerId":"ЦБ-0200642","offerName":"Швейная машина Singer Studio 12, белый","price":11990,"buyer-price":11990,"count":1,"delivery":true,"params":"Цвет товара: белый","vat":"NO_VAT","fulfilmentShopId":575686,"sku":"1808809549","shopSku":"ЦБ-0200642"}]}}
        """)
    print(data, file=sys.stderr)
    beru_order = data.get('order', {})

    user = ShopUser.objects.get(phone='0000')

    if not request.session.session_key:
        request.session.save()
        request.session.modified = True
    request.session[SESSION_KEY] = user._meta.pk.value_to_string(user)
    request.session.save()
    basket = Basket.objects.create(session_id=request.session.session_key, utm_source='beru', secondary=True)

    for beru_item in beru_order.get('items', []):
        try:
            sku = beru_item.get('offerId', '#NO_SKU#')
            product = Product.objects.get(article=sku)
            price = beru_item.get('buyer-price', beru_item.get('price', 0))
            count = beru_item.get('count', 0)
            item, _ = basket.items.get_or_create(product=product)
            item.quantity = count
            if product.price > price:
                item.discount = product.price - price
            item.save()
        except Exception as e:
            print(str(e), file=sys.stderr)
            return JsonResponse({"order": {"accepted": False, "reason": "OUT_OF_DATE"}})

    basket.save()
    order = Order.register(basket)

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

    order.delivery_tracking_number = beru_order.get('id', None)
    order.comment = beru_order.get('notes', '')
    order.save()

    return JsonResponse({"order": {"accepted": True, "id": str(order.id)}})


BERU_ORDER_SUBSTATUS = {
    'PROCESSING_EXPIRED': 'магазин не обработал заказ в течение семи дней',
    'REPLACING_ORDER': 'покупатель решил заменить товар другим по собственной инициативе',
    'RESERVATION_EXPIRED': 'покупатель не завершил оформление зарезервированного заказа в течение 10 минут',
    'SHOP_FAILED': 'магазин не может выполнить заказ',
    'USER_CHANGED_MIND': 'покупатель отменил заказ по собственным причинам',
    'USER_NOT_PAID': 'покупатель не оплатил заказ (для типа оплаты PREPAID) в течение двух часов',
    'USER_REFUSED_DELIVERY': 'покупателя не устраивают условия доставки',
    'USER_REFUSED_PRODUCT': 'покупателю не подошел товар',
    'USER_REFUSED_QUALITY': 'покупателя не устраивает качество товара',
    'USER_UNREACHABLE': 'не удалось связаться с покупателем'
}


BERU_PAYMENT_METHODS = {
    'CASH_ON_DELIVERY': Order.PAYMENT_CASH,
    'CARD_ON_DELIVERY': Order.PAYMENT_POS,
    'YANDEX': Order.PAYMENT_CARD
}


@require_POST
@csrf_exempt
@token_required
def order_status(request):
    if request.body:
        data = json.loads(request.body.decode('utf-8'))
    else:
        data = json.loads("""
        {'order': {'substatus': 'STARTED', 'delivery': {'serviceName': 'Доставка', 'deliveryPartnerType': 'YANDEX_MARKET', 'price': 249, 'type': 'DELIVERY', 'shipments': [{'height': 52, 'width': 21, 'depth': 67, 'status': 'NEW', 'weight': 1001}], 'region': {'id': 2, 'parent': {'id': 10174, 'parent': {'id': 17, 'parent': {'id': 225, 'name': 'Россия', 'type': 'COUNTRY'}, 'name': 'Северо-Западный федеральный округ', 'type': 'COUNTRY_DISTRICT'}, 'name': 'Санкт-Петербург и Ленинградская область', 'type': 'SUBJECT_FEDERATION'}, 'name': 'Санкт-Петербург', 'type': 'CITY'}, 'deliveryServiceId': 1003937, 'vat': 'VAT_20', 'dates': {'fromDate': '30-09-2019', 'toDate': '30-09-2019'}}, 'total': 20049, 'paymentMethod': 'CASH_ON_DELIVERY', 'currency': 'RUR', 'status': 'PROCESSING', 'itemsTotal': 19800, 'creationDate': '26-09-2019 17:50:21', 'taxSystem': 'USN', 'paymentType': 'POSTPAID', 'fake': True, 'items': [{'count': 1, 'offerName': 'Швейная машина Singer Confidence 7640 Q, белый/серый', 'feedId': 614439, 'buyer-price': 19800, 'offerId': 'ЦБ-0200637', 'sku': '1808809720', 'price': 19800, 'shopSku': 'ЦБ-0200637', 'params': 'Цвет товара: белый/серый', 'id': 15350984, 'fulfilmentShopId': 575686, 'vat': 'NO_VAT'}], 'id': 8943125}}
        """)
    print(data, file=sys.stderr)
    beru_order = data.get('order', {})
    order_id = str(beru_order.get('id', 0))
    try:
        order = Order.objects.get(delivery_tracking_number=order_id)
        status = beru_order.get('status', 'PROCESSING')
        if status == 'DELIVERY':  # заказ передан в службу доставки
            order.status = Order.STATUS_SENT
        elif status == 'PICKUP':  # заказ доставлен в пункт самовывоза
            order.status = Order.STATUS_DELIVERED
        elif status == 'DELIVERED':  # заказ получен покупателем
            order.status = Order.STATUS_DONE
        elif status == 'CANCELLED':  # заказ отменен
            substatus = beru_order.get('substatus', '')
            if substatus in ('REPLACING_ORDER', 'RESERVATION_EXPIRED', 'USER_CHANGED_MIND', 'USER_NOT_PAID', 'USER_REFUSED_DELIVERY', 'USER_UNREACHABLE'):
                order.status = Order.STATUS_CANCELED
            elif substatus in ('PROCESSING_EXPIRED', 'SHOP_FAILED', 'USER_REFUSED_PRODUCT', 'USER_REFUSED_QUALITY'):
                order.status = Order.STATUS_PROBLEM
            else:
                order.status = Order.STATUS_PROBLEM
            info = BERU_ORDER_SUBSTATUS.get(substatus, "Неизвестная причина отмены заказа")
            if order.delivery_info:
                order.delivery_info = '\n'.join([order.delivery_info, info])
            else:
                order.delivery_info = info
        payment = beru_order.get('paymentMethod', 'CASH_ON_DELIVERY')
        order.payment = BERU_PAYMENT_METHODS.get(payment, Order.PAYMENT_UNKNOWN)
        order.save()
    except Order.DoesNotExist:
        return HttpResponseBadRequest("Не существует внутреннего заказа с заказом Беру №{}".format(order_id))

    return HttpResponse('')
