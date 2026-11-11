import base64
import csv
import hashlib
import io
import json
import logging
import re

from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_EVEN
from urllib.parse import quote
from urllib.request import Request, urlopen
from urllib.error import HTTPError

from django.conf import settings
from django.db import Error as DatabaseError
from django.utils import timezone
from django.utils.formats import date_format

from celery import shared_task

from constance import config

from sewingworld.sms import send_sms
from sewingworld.templatetags.rupluralize import rupluralize

from shop.models import ShopUser, ShopUserManager, Currency, Order

from .common import SINGLE_DATE_FORMAT
from .workflow import update_order


log = logging.getLogger('shop')


class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return str(o)
        return super(DecimalEncoder, self).default(o)


@shared_task(name='shop.tasks.update_user_bonuses', bind=True, autoretry_for=(OSError, DatabaseError), retry_backoff=600, retry_jitter=False)
def update_user_bonuses(self):
    bonused_users = set(ShopUser.objects.filter(bonuses__gt=0).values_list('id', flat=True))
    filename = 'БонусныеБаллыИнфо.txt'  # БонусныеБаллыНаДР.txt
    url = 'https://cloud-api.yandex.net/v1/disk/resources?path={}'.format(quote('disk:/' + filename))
    headers = {
        'Authorization': 'OAuth {token}'.format(token=config.sw_bonuses_ydisk_token),
        'Content-Type': 'application/json; charset=utf-8'
    }
    request = Request(url, None, headers)
    try:
        response = urlopen(request)
        result = json.loads(response.read().decode('utf-8'))
        bonus_file = result.get('file', None)
        bonus_md5 = result.get('md5', None)
        if not bonus_file:
            log.error('No file')
            raise self.retry(countdown=3600, max_retries=4)  # 1 hour
        log.info('Getting file %s' % bonus_file)
        request = Request(bonus_file, None, headers)
        response = urlopen(request)
        result = response.read()
        md5 = hashlib.md5(result).hexdigest()
        if md5 != bonus_md5:
            log.error('MD5 checksums differ')
            raise self.retry(countdown=3600, max_retries=4)  # 1 hour
        num = 0
        records = csv.DictReader(io.StringIO(result.decode('windows-1251')), delimiter=';')
        log.info('Processing file')
        for line in records:
            try:
                if line['ШтрихКод'] and line['КоличествоБаллов']:
                    bonuses = float(line['КоличествоБаллов'].replace('\xA0', '').replace(' ', '').replace(',', '.'))
                    if bonuses < 0:
                        continue
                    user, created = ShopUser.objects.get_or_create(phone=ShopUserManager.normalize_phone(line['ШтрихКод']))
                    user.bonuses = int(bonuses)
                    if not created:
                        bonused_users.discard(user.id)
                    if line['КСписанию']:
                        expiring_bonuses = float(line['КСписанию'].replace('\xA0', '').replace(' ', '').replace(',', '.'))
                        user.expiring_bonuses = int(expiring_bonuses)
                        if line['ДатаСписания']:
                            expiration_date = datetime.strptime(line['ДатаСписания'], '%d.%m.%Y %H:%M:%S')
                            user.expiration_date = timezone.make_aware(expiration_date)
                    if not user.name:
                        name = line['ФИО']
                        if name and not name.startswith('Держатель карты'):
                            name = re.sub(r'[:,]?\s?(?:Штрихкод)?:?\s?\d+', '', name)
                            user.name = name.title()
                    user.save()
                    num = num + 1
            except ValueError:
                log.error("Wrong bonus number '%s' for '%s'" % (line['КоличествоБаллов'], line['ШтрихКод']))
        for user_id in bonused_users:
            user = ShopUser.objects.get(pk=user_id)
            user.bonuses = 0
            user.save()
            num = num + 1
        return num
    except HTTPError as e:
        content = e.read()
        error = json.loads(content.decode('utf-8'))
        message = error.get('message', 'Неизвестная ошибка взаимодействия с Яндекс.Диском')
        log.error(message)
        raise self.retry(countdown=60 * 10, max_retries=12, exc=e)  # 10 minutes
    return 0


@shared_task(name='shop.tasks.update_user_birthday_bonuses', bind=True, autoretry_for=(OSError, DatabaseError), retry_backoff=600, retry_jitter=False)
def update_user_birthday_bonuses(self):
    # bonused_users = set(ShopUser.objects.filter(bonuses__gt=0).values_list('id', flat=True))
    filename = 'БонусныеБаллыНаДР.txt'
    url = 'https://cloud-api.yandex.net/v1/disk/resources?path={}'.format(quote('disk:/' + filename))
    headers = {
        'Authorization': 'OAuth {token}'.format(token=config.sw_bonuses_ydisk_token),
        'Content-Type': 'application/json; charset=utf-8'
    }
    request = Request(url, None, headers)
    try:
        response = urlopen(request)
        result = json.loads(response.read().decode('utf-8'))
        bonus_file = result.get('file', None)
        bonus_md5 = result.get('md5', None)
        if not bonus_file:
            log.error('No file')
            raise self.retry(countdown=3600, max_retries=4)  # 1 hour
        log.info('Getting file %s' % bonus_file)
        request = Request(bonus_file, None, headers)
        response = urlopen(request)
        result = response.read()
        md5 = hashlib.md5(result).hexdigest()
        if md5 != bonus_md5:
            log.error('MD5 checksums differ')
            raise self.retry(countdown=3600, max_retries=4)  # 1 hour
        num = 0
        one_week = timezone.now() + timedelta(days=7)
        expiration_date = date_format(one_week, format=SINGLE_DATE_FORMAT)
        records = csv.DictReader(io.StringIO(result.decode('windows-1251')), delimiter=';')
        log.info('Processing file')
        for line in records:
            try:
                if line['НомерТелефона'] and line['КоличествоБонусов']:
                    bonuses = int(float(line['КоличествоБонусов'].replace('\xA0', '').replace(' ', '').replace(',', '.')))
                    if bonuses < 0:
                        continue
                    text = "%d %s ко дню рождения до %s www.thsm.ru" % (
                        bonuses,
                        rupluralize(bonuses, "бонус,бонуса,бонусов"),
                        expiration_date
                    )
                    send_sms(ShopUserManager.normalize_phone(line['НомерТелефона']), text, True)
                    num = num + 1
            except ValueError:
                log.error("Wrong bonus number '%s' for '%s'" % (line['КоличествоБаллов'], line['НомерТелефона']))
        return num
    except HTTPError as e:
        content = e.read()
        error = json.loads(content.decode('utf-8'))
        message = error.get('message', 'Неизвестная ошибка взаимодействия с Яндекс.Диском')
        log.error(message)
        raise self.retry(countdown=60 * 10, max_retries=12, exc=e)  # 10 minutes
    return 0


@shared_task(name='shop.tasks.update_cbrf_currencies', bind=True, autoretry_for=(OSError, DatabaseError), retry_backoff=300, retry_jitter=False)
def update_cbrf_currencies(self):
    url = 'https://www.cbr-xml-daily.ru/daily_json.js'
    request = Request(url)
    response = urlopen(request)
    result = json.loads(response.read().decode('utf-8'))
    rate = result.get('Valute', {}).get('USD', {}).get('Value', None)
    if rate:
        usd_cbrf = Currency.objects.get(code=998)
        usd_cbrf.rate = rate
        usd_cbrf.save()
    else:
        raise self.retry(countdown=3600, max_retries=4)  # 1 hour
    return rate


@shared_task(name='shop.tasks.create_modulpos_order', queue="integrations", bind=True, autoretry_for=(EnvironmentError, DatabaseError), retry_backoff=60, retry_jitter=False)
def create_modulpos_order(self, order_id):
    order = Order.objects.get(id=order_id)
    if not order.courier:
        return 'Отсутствует привязка курьера'
    if not order.courier.pos_terminal:
        return 'Отсутствует привязка кассы к курьеру'
    items = []
    for item in order.items.all():
        items.append({
            'name': item.product.title,
            'measure': 'pcs',
            'inventoryType': 'INVENTORY',
            'quantity': item.quantity,
            'price': item.cost
        })
    if order.delivery_price > 0:
        items.append({
            'name': "Доставка",
            'measure': 'other',
            'inventoryType': 'SERVICE',
            'quantity': 1,
            'price': str(order.delivery_price.quantize(Decimal('1'), rounding=ROUND_HALF_EVEN))
        })
    data = {
        'documentNumber': str(order.id),
        'documentType': 'SALE',
        'documentDateTime': timezone.localtime(order.created).strftime('%Y-%m-%dT%H:%M:%S%z'),
        'customerContact': str(order.user.phone),
        'clientInformation': {
            'name': order.user.get_short_name()
        },
        'prepaid': order.paid,
        'inventPositions': items
    }
    data_encoded = json.dumps(data, cls=DecimalEncoder).encode('utf-8')

    pos_terminal = order.courier.pos_terminal
    seller = pos_terminal.seller
    url = 'https://service.modulpos.ru/api/v2/retail-point/{}/order'.format(pos_terminal.id)
    headers = {
        'Authorization': 'Basic {token}'.format(token=base64.standard_b64encode('{}:{}'.format(seller.modulkassa_login, seller.modulkassa_password).encode('utf-8')).decode('utf-8')),
        'Content-Type': 'application/json; charset=utf-8'
    }
    request = Request(url, data_encoded, headers, method='POST')
    try:
        response = urlopen(request)
        result = json.loads(response.read().decode('utf-8'))
        order_id = result.get('id', '')
        update_order.delay(order.pk, {'hidden_tracking_number': order_id})
        return order_id
    except HTTPError as e:
        content = e.read()
        error = json.loads(content.decode('utf-8'))
        """
        {
            'errors': [
                {
                    'defaultMessage': 'Переданное значение не соответствует допустимому формату',
                    'rejectedValue': '+375298882111',
                    'code': 'Contact',
                    'objectName': 'orderDto',
                    'field': 'customerContact'
                }
            ],
            'status': 400,
            'error': 'Bad Request',
            'path': '/v2/retail-point/c3b58ef5-5d26-482f-8f25-b92c33302e1f/order',
            'message': "Validation failed for object='orderDto'. Error count: 1",
            'timestamp': '2022-03-04T11:25:22+00:00'
        }
        """
        log.error(error)
        message = error.get('message', 'Неизвестная ошибка взаимодействия с МодульКасса')
        update = {}
        if message != 'object-already-exists':
            update['status'] = Order.STATUS_PROBLEM
        if order.manager_comment:
            update['manager_comment'] = '\n'.join([order.manager_comment, message])
        else:
            update['manager_comment'] = message
        update_order.delay(order.pk, update)
        if message == 'object-already-exists':
            return message
        raise self.retry(countdown=60 * 10, max_retries=12, exc=e)  # 10 minutes


@shared_task(name='shop.tasks.delete_modulpos_order', queue="integrations", bind=True, autoretry_for=(EnvironmentError, DatabaseError), retry_backoff=60, retry_jitter=False)
def delete_modulpos_order(self, order_id):
    order = Order.objects.get(id=order_id)
    if not order.courier:
        return 'Отсутствует привязка курьера'
    if not order.courier.pos_terminal:
        return 'Отсутствует привязка кассы к курьеру'
    if not order.hidden_tracking_number:
        return 'Отсутствует ID документа в кассе'

    pos_terminal = order.courier.pos_terminal
    seller = pos_terminal.seller
    # get fiscal info
    url = 'https://service.modulpos.ru/api/v1/retail-point/{}/cashdocs?count=1&q=linkedDocId=={}'.format(pos_terminal.id, order.hidden_tracking_number)
    headers = {
        'Authorization': 'Basic {token}'.format(token=base64.standard_b64encode('{}:{}'.format(seller.modulkassa_login, seller.modulkassa_password).encode('utf-8')).decode('utf-8')),
        'Content-Type': 'application/json; charset=utf-8'
    }
    request = Request(url, None, headers, method='GET')
    try:
        response = urlopen(request)
        result = json.loads(response.read().decode('utf-8'))
        log.error(str(result))
        fiscalInfo = result.get('data', [{}])[0].get('fiscalInfo')
        log.error(str(fiscalInfo))
        if fiscalInfo:
            update_order.delay(order.pk, {'meta': {'fiscalInfo': fiscalInfo}})
    except HTTPError as e:
        content = e.read()
        error = json.loads(content.decode('utf-8'))
        message = error.get('message', 'Неизвестная ошибка взаимодействия с МодульКасса')
        update = {}
        update['status'] = Order.STATUS_PROBLEM
        if order.manager_comment:
            update['manager_comment'] = '\n'.join([order.manager_comment, message])
        else:
            update['manager_comment'] = message
        update_order.delay(order.pk, update)
        raise self.retry(countdown=60 * 10, max_retries=12, exc=e)  # 10 minutes

    # delete order from pos terminal
    url = 'https://service.modulpos.ru/api/v2/retail-point/{}/order/{}'.format(pos_terminal.id, order.hidden_tracking_number)
    request = Request(url, None, headers, method='DELETE')
    try:
        urlopen(request)
        update_order.delay(order.pk, {'hidden_tracking_number': ''})
        return order.hidden_tracking_number
    except HTTPError as e:
        content = e.read()
        error = json.loads(content.decode('utf-8'))
        message = error.get('message', 'Неизвестная ошибка взаимодействия с МодульКасса')
        update = {}
        update['status'] = Order.STATUS_PROBLEM
        if order.manager_comment:
            update['manager_comment'] = '\n'.join([order.manager_comment, message])
        else:
            update['manager_comment'] = message
        update_order.delay(order.pk, update)
        raise self.retry(countdown=60 * 10, max_retries=12, exc=e)  # 10 minutes


@shared_task(name='shop.tasks.ym_upload_user', autoretry_for=(OSError, DatabaseError), retry_backoff=600, retry_jitter=False)
def ym_upload_user(user_id, order_id):
    user = ShopUser.objects.get(pk=user_id)
    order = Order.objects.get(id=order_id)
    metas = Order.objects.filter(user=user, meta__has_key='clientID').values_list('meta', flat=True).exclude(id=order_id)
    client_ids = {order.meta['clientID']}
    for meta in metas:
        client_ids.add(meta['clientID'])
    data = {
        "contacts": [
            {
                "uniq_id": str(user.id),
                "name": user.name,
                "create_date_time": timezone.localtime(user.date_joined).strftime('%Y-%m-%d %H:%M:%S'),
                "update_date_time": timezone.localtime(timezone.now()).strftime('%Y-%m-%d %H:%M:%S'),
                "client_ids": list(client_ids),
                "emails": [user.email],
                "phones": [user.phone]
            }
        ]
    }
    data_encoded = json.dumps(data).encode('utf-8')
    mode = 'UPDATE'
    url = 'https://api-metrika.yandex.net/cdp/api/v1/counter/{counterId}/data/contacts?merge_mode={mode}'.format(counterId=settings.YM_COUNTER_ID, mode=mode)
    headers = {
        'Authorization': 'OAuth {oauth_token}'.format(oauth_token=settings.YM_API_TOKEN),
        'Content-Type': 'application/json; charset=utf-8'
    }
    request = Request(url, data_encoded, headers, method='POST')
    log.info('<<< ' + request.full_url)
    log.info(data_encoded)
    try:
        response = urlopen(request)
        result = json.loads(response.read().decode('utf-8'))
        log.info(str(result))
    except HTTPError as e:
        content = e.read().decode('utf-8')
        log.error(content)


@shared_task(name='shop.tasks.ym_upload_order', autoretry_for=(OSError, DatabaseError), retry_backoff=600, retry_jitter=False)
def ym_upload_order(order_id):
    order = Order.objects.get(id=order_id)
    data = {
        "orders": [
            {
                "id": str(order.id),
                "client_uniq_id": str(order.user.id),
                "client_type": "CONTACT",
                "revenue": order.total,
                "order_status": str(order.status),
                "create_date_time": timezone.localtime(order.created).strftime('%Y-%m-%d %H:%M:%S'),
                "update_date_time": timezone.localtime(timezone.now()).strftime('%Y-%m-%d %H:%M:%S')
            }
        ]
    }
    if order.status in (Order.STATUS_DONE, Order.STATUS_FINISHED, Order.STATUS_CANCELED, Order.STATUS_UNCLAIMED):
        data["orders"][0]["finish_date_time"] = timezone.localtime(timezone.now()).strftime('%Y-%m-%d %H:%M:%S')

    data_encoded = json.dumps(data, cls=DecimalEncoder).encode('utf-8')
    mode = 'APPEND' if order.status == Order.STATUS_NEW else 'UPDATE'
    url = 'https://api-metrika.yandex.net/cdp/api/v1/counter/{counterId}/data/orders?merge_mode={mode}'.format(counterId=settings.YM_COUNTER_ID, mode=mode)
    headers = {
        'Authorization': 'OAuth {oauth_token}'.format(oauth_token=settings.YM_API_TOKEN),
        'Content-Type': 'application/json; charset=utf-8'
    }
    request = Request(url, data_encoded, headers, method='POST')
    log.info('<<< ' + request.full_url)
    log.info(data_encoded)
    try:
        response = urlopen(request)
        result = json.loads(response.read().decode('utf-8'))
        log.info(str(result))
    except HTTPError as e:
        content = e.read().decode('utf-8')
        log.error(content)
