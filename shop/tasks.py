from __future__ import absolute_import

import base64
import csv
import functools
import hashlib
import io
import json
import logging
import os.path
import re
import tempfile

from collections import defaultdict
from datetime import datetime, timedelta
from importlib import import_module
from decimal import Decimal, ROUND_HALF_EVEN
from urllib.parse import quote
from urllib.request import Request, urlopen
from urllib.error import HTTPError

from django.contrib.admin.models import LogEntry, CHANGE
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.fields import JSONField
from django.core import signing
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned, ValidationError
from django.core.mail import send_mail
from django.core.validators import EmailValidator
from django.conf import settings
from django.db import connection, Error as DatabaseError
from django.db.models import Q
from django.db.models.fields.related import RelatedField
from django.db.models.fields.reverse_related import ForeignObjectRel
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import dateparse, timezone
from django.utils.encoding import force_text
from django.utils.formats import date_format
from django.contrib.sites.models import Site

from celery import shared_task

from djconfig import config, reload_maybe
from flags.state import enable_flag, disable_flag

import reviews

from unisender import Unisender

from sewingworld.models import SiteProfile
from sewingworld.sms import send_sms
from utility.templatetags.rupluralize import rupluralize

from shop.models import ShopUser, ShopUserManager, Supplier, Currency, Product, Stock, Basket, Order


SINGLE_DATE_FORMAT = 'j E'
SINGLE_DATE_FORMAT_WITH_YEAR = 'j E Y'

log = logging.getLogger('shop')

sw_default_site = Site.objects.get(domain='www.sewing-world.ru')


def single_instance_task(timeout):
    def task_exc(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            lock_id = "celery-single-instance-" + func.__name__
            if cache.add(lock_id, "true", timeout):
                try:
                    return func(*args, **kwargs)
                finally:
                    cache.delete(lock_id)
        return wrapper
    return task_exc


def validate_email(email):
    validator = EmailValidator()
    try:
        validator(email)
        return True
    except ValidationError:
        return False


def get_site_for_order(order):
    if order.integration:
        return sw_default_site
    else:
        return order.site


class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return str(o)
        return super(DecimalEncoder, self).default(o)


@shared_task(bind=True, autoretry_for=(DatabaseError,), retry_backoff=300, retry_jitter=False)
def update_order(self, order_id, data):
    order = Order.objects.get(id=order_id)
    if order.owner:
        log.info('Locked by %s, retrying' % order.owner)
        raise self.retry(countdown=600, max_retries=24)  # 10 minutes
    order.owner = ShopUser.objects.get(phone='000')
    order.save()
    changed = {}
    change_message = 'unchanged'
    for attr, new_val in data.items():
        field = order._meta.get_field(attr)
        if field.primary_key or isinstance(field, (ForeignObjectRel, RelatedField)):
            continue
        old_val = getattr(order, attr)
        if old_val != new_val:
            if isinstance(field, JSONField):  # json fields are merged for purpose
                if old_val:
                    new_val = {**old_val, **new_val}
            setattr(order, attr, new_val)
            changed[attr] = new_val
    if changed:
        order.save(update_fields=changed.keys())
        change_message = ', '.join(map(lambda item: '{}: {}'.format(item[0], item[1]), changed.items()))
        LogEntry.objects.log_action(
            user_id=order.user.id,
            content_type_id=ContentType.objects.get_for_model(order).pk,
            object_id=order.pk,
            object_repr=force_text(order),
            action_flag=CHANGE,
            change_message=change_message
        )
    order.owner = None
    order.save()
    return change_message


@shared_task(autoretry_for=(Exception,), default_retry_delay=60, retry_backoff=True)
def send_message(phone, message):
    return send_sms(phone, message)


@shared_task(autoretry_for=(Exception,), default_retry_delay=15, retry_backoff=True)
def send_password(phone, password):
    return send_sms(phone, "Пароль для доступа на сайт: %s" % password)


@shared_task(autoretry_for=(Exception,), default_retry_delay=60, retry_backoff=True)
def notify_user_order_new_sms(order_id, password=None):
    order = Order.objects.get(id=order_id)
    site = get_site_for_order(order)
    password_text = ""
    if password:
        password_text = " Пароль: %s" % password
    return send_sms(order.phone, "Состояние заказа №%s можно узнать в личном кабинете: https://%s%s %s"
                                 % (order_id, site.domain, reverse('shop:user_orders'), password_text))


@shared_task(autoretry_for=(Exception,), default_retry_delay=120, retry_backoff=True)
def notify_user_order_new_mail(order_id):
    order = Order.objects.get(id=order_id)
    if order.email:
        if not validate_email(order.email):
            return
        site = get_site_for_order(order)
        reload_maybe()
        context = {
            'site': site,
            'site_profile': SiteProfile.objects.get(site=site),
            'owner_info': getattr(settings, 'SHOP_OWNER_INFO', {}),
            'order': order
        }
        msg_plain = render_to_string('mail/shop/order_new.txt', context)
        msg_html = render_to_string('mail/shop/order_new.html', context)

        return send_mail(
            'Ваш заказ №%s принят' % order_id,
            msg_plain,
            config.sw_email_from,
            [order.email],
            html_message=msg_html,
        )


@shared_task(autoretry_for=(Exception,), default_retry_delay=120, retry_backoff=True)
def notify_user_order_collected(order_id):
    order = Order.objects.get(id=order_id)
    site = get_site_for_order(order)
    send_sms(order.phone, "Заказ №%s собран и ожидает оплаты. Перейдите по ссылке, чтобы оплатить заказ: https://%s%s"
                          % (order_id, site.domain, reverse('shop:order', args=[order_id])))

    if order.email:
        if not validate_email(order.email):
            return
        reload_maybe()
        context = {
            'site': site,
            'site_profile': SiteProfile.objects.get(site=site),
            'owner_info': getattr(settings, 'SHOP_OWNER_INFO', {}),
            'order': order
        }
        msg_plain = render_to_string('mail/shop/order_collected.txt', context)
        msg_html = render_to_string('mail/shop/order_collected.html', context)

        return send_mail(
            'Оплата заказа №%s' % order_id,
            msg_plain,
            config.sw_email_from,
            [order.email],
            html_message=msg_html,
        )


@shared_task(autoretry_for=(Exception,), retry_backoff=True)
def notify_user_order_delivered_shop(order_id):
    order = Order.objects.get(id=order_id)
    city = order.store.city.name
    address = order.store.address
    name = order.store.name
    send_sms(order.phone, "Ваш заказ доставлен в магазин \"%s\" по адресу %s, %s."
                          " Для получения заказа обратитесь в кассу и назовите номер"
                          " заказа %s." % (name, city, address, order_id))


@shared_task(autoretry_for=(Exception,), retry_backoff=True)
def notify_user_order_delivered(order_id):
    order = Order.objects.get(id=order_id)
    if order.delivery == Order.DELIVERY_PICKPOINT:
        title = 'PickPoint'
    else:
        title = 'ТК'
    send_sms(order.phone, "Заказ №%s доставлен в %s: %s" % (order_id, title, order.delivery_info))

    if order.email:
        if not validate_email(order.email):
            return
        site = get_site_for_order(order)
        reload_maybe()
        context = {
            'site': site,
            'site_profile': SiteProfile.objects.get(site=site),
            'owner_info': getattr(settings, 'SHOP_OWNER_INFO', {}),
            'order': order
        }
        msg_plain = render_to_string('mail/shop/order_delivered.txt', context)
        msg_html = render_to_string('mail/shop/order_delivered.html', context)

        return send_mail(
            'Получение заказа №%s' % order_id,
            msg_plain,
            config.sw_email_from,
            [order.email],
            html_message=msg_html,
        )


@shared_task(autoretry_for=(Exception,), default_retry_delay=120, retry_backoff=True)
def notify_user_order_done(order_id):
    order = Order.objects.get(id=order_id)

    if order.email:
        if not validate_email(order.email):
            return
        site = get_site_for_order(order)
        reload_maybe()
        context = {
            'site': site,
            'site_profile': SiteProfile.objects.get(site=site),
            'owner_info': getattr(settings, 'SHOP_OWNER_INFO', {}),
            'order': order
        }
        msg_plain = render_to_string('mail/shop/order_done.txt', context)
        msg_html = render_to_string('mail/shop/order_done.html', context)

        return send_mail(
            'Заказ №%s выполнен' % order_id,
            msg_plain,
            config.sw_email_from,
            [order.email],
            html_message=msg_html,
        )


@shared_task(bind=True, autoretry_for=(EnvironmentError, DatabaseError), retry_backoff=300, retry_jitter=False)
def notify_user_review_products(self, order_id):
    order = Order.objects.get(id=order_id)

    if order.email:
        if not validate_email(order.email):
            return
        reload_maybe()
        owner_info = getattr(settings, 'SHOP_OWNER_INFO', {})
        context = {
            'owner_info': owner_info,
            'order': order
        }
        msg_html = render_to_string('mail/shop/order_review_products.html', context)

        unisender = Unisender(api_key=settings.UNISENDER_KEY)
        result = unisender.sendEmail(order.email, owner_info.get('short_name', ''), config.sw_email_unisender,
                                     'Оцените товары из заказа №%s' % order_id,
                                     msg_html, settings.UNISENDER_PRODUCT_REVIEW_LIST)

        # https://www.unisender.com/ru/support/api/common/api-errors/
        if unisender.errorMessage:
            if unisender.errorCode in ['retry_later', 'api_call_limit_exceeded_for_api_key', 'api_call_limit_exceeded_for_ip']:
                raise self.retry(countdown=60 * 60 * 2, max_retries=5, exc=Exception(unisender.errorMessage))  # 2 hours
            if unisender.errorCode == 'not_enough_money':
                raise self.retry(countdown=60 * 60 * 24, max_retries=5, exc=Exception(unisender.errorMessage))  # 24 hours
            return unisender.errorMessage

        # recipient errors
        for r in result['result']:
            if 'index' in r and r['index'] == 0:
                if 'errors' in r:
                    try:
                        return r['errors'][0]['message']
                    except Exception:
                        return str(r['errors'])
                else:
                    return r['id']


@shared_task(autoretry_for=(Exception,), default_retry_delay=60, retry_backoff=True)
def notify_manager(order_id):
    order = Order.objects.get(id=order_id)

    reload_maybe()
    msg_plain = render_to_string('mail/shop/order_manager.txt', {'order': order})
    msg_html = render_to_string('mail/shop/order_manager.html', {'order': order})

    site_text = ''
    if order.site != sw_default_site:
        site_text = ' (%s)' % order.site.domain

    if hasattr(order.site, 'profile') and order.site.profile.manager_emails:
        managers = order.site.profile.manager_emails
    else:
        managers = sw_default_site.profile.manager_emails
    send_mail(
        'Новый заказ №%s%s' % (order_id, site_text),
        msg_plain,
        config.sw_email_from,
        managers.split(','),
        html_message=msg_html,
    )


@shared_task(autoretry_for=(Exception,), default_retry_delay=60, retry_backoff=True)
def notify_manager_sms(order_id, phone):
    return send_sms(phone, "Новый заказ №%s" % order_id)


@shared_task(autoretry_for=(Exception,), default_retry_delay=60, retry_backoff=True)
def notify_review_posted(review_id):
    review = reviews.get_review_model().objects.get(id=review_id)

    reload_maybe()
    msg_plain = render_to_string('mail/reviews/review_posted.txt', {'review': review})

    return send_mail(
        'Новый обзор для %s' % review.content_object,
        msg_plain,
        config.sw_email_from,
        [manager_tuple[1] for manager_tuple in settings.MANAGERS]
    )


@shared_task(bind=True, autoretry_for=(OSError, DatabaseError), retry_backoff=300, retry_jitter=False)
def update_1c_stocks(self):
    reload_maybe()
    filename = 'ВыгрузкаНаСайтПоВсемСкладам.csv'
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
        modified = result.get('modified', None)
        if not bonus_file:
            log.error('No file')
            raise self.retry(countdown=600, max_retries=4)  # 10 minutes

        import_dir = getattr(settings, 'SHOP_IMPORT_DIRECTORY', 'import')
        filepath = os.path.join(import_dir, filename)
        if modified and os.path.isfile(filename):
            mdate = dateparse.parse_datetime(modified)
            fdate = timezone.make_aware(datetime.fromtimestamp(os.path.getmtime(filepath)))
            if mdate < fdate:
                log.info('File is not modified since last update: {} < {}'.format(mdate, fdate))
                return None

        log.info('Getting file %s' % bonus_file)
        request = Request(bonus_file, None, headers)
        response = urlopen(request)
        result = response.read()
        md5 = hashlib.md5(result).hexdigest()
        if md5 != bonus_md5:
            log.error('MD5 checksums differ')
            raise self.retry(countdown=600, max_retries=4)  # 10 minutes

        f = open(filepath, 'wb')
        f.write(result)
        f.close()

        import1c.delay(filename)
        return modified
    except HTTPError as e:
        content = e.read()
        error = json.loads(content.decode('utf-8'))
        message = error.get('message', 'Неизвестная ошибка взаимодействия с Яндекс.Диском')
        log.error(message)
        raise self.retry(countdown=600, max_retries=12, exc=e)  # 10 minutes
    return 0


class fragile(object):
    class Break(Exception):
        """Break out of the with statement"""

    def __init__(self, value):
        self.value = value

    def __enter__(self):
        return self.value.__enter__()

    def __exit__(self, etype, value, traceback):
        error = self.value.__exit__(etype, value, traceback)
        if etype == self.Break:
            return True
        return error


@shared_task(time_limit=7200, autoretry_for=(Exception,), retry_backoff=True)
@single_instance_task(60 * 20)
def import1c(file):
    log.error('Import1C')
    enable_flag('1C_IMPORT_RUNNING')
    frozen_orders = Order.objects.filter(status=Order.STATUS_FROZEN)
    frozen_products = defaultdict(list)
    if frozen_orders.exists():
        for order in frozen_orders:
            for item in order.items.all():
                quantity = 0
                stock = Stock.objects.filter(supplier__count_in_stock=True, product=item.product)
                if stock.exists():
                    for s in stock:
                        quantity = quantity + s.quantity + s.correction
                if quantity <= 0:
                    frozen_products[item.product.id].append(order)

    log.info('Frozen products %s' % str(frozen_products.keys()))

    stocks = list(Stock.objects.filter(~Q(correction=0)).values_list('product', 'supplier', 'correction', 'reason'))
    corrected_stocks = defaultdict(dict)
    for s in stocks:
        corrected_stocks[s[0]][s[1]] = (s[2], s[3])

    import_dir = getattr(settings, 'SHOP_IMPORT_DIRECTORY', 'import')
    filepath = import_dir + '/' + file

    src_file = open(filepath, mode='rt')
    tmp_file = tempfile.TemporaryFile(mode='r+t')
    for line in src_file:
        tmp_file.write(line)
    src_file.close()
    tmp_file.seek(0)

    table_copy = tempfile.TemporaryFile(mode='r+t')

    imported = 0
    updated = 0
    errors = []
    products = set()
    orders = set()
    suppliers = []
    currencies = Currency.objects.all()
    date_reg = re.compile(r"\d{1,2}\.\d{2}\.\d{4} \d{1,2}:\d{2}:\d{2}")
    date = None
    with fragile(tmp_file) as csvfile:  # https://stackoverflow.com/a/23665658
        line = csvfile.readline().strip()
        if line[0] == '\ufeff':
            line = line[1:]  # trim the BOM away
        if date_reg.match(line):
            date = line
        next(csvfile)
        line = csvfile.readline().strip()
        if line != '//Список складов':
            errors.append("Неправильный формат файла импорта (ожидался список складов)")
            raise fragile.Break
        for line in csvfile:
            line = line.strip()
            if line == '//Остатки':
                break
            name, code = line.split(';')
            try:
                supplier = Supplier.objects.get(code1c=code)
                suppliers.append(supplier)
            except ObjectDoesNotExist:
                errors.append("Неизвестный поставщик с кодом %s: %s" % (code, name))
                suppliers.append(None)
        if not suppliers:
            errors.append("Нет ни одного известного поставщика")
            raise fragile.Break
        csv_fields = ('article', 'sp_cur_price', 'sp_cur_code', 'ws_cur_price', 'ws_cur_code', 'cur_price', 'cur_code')
        records = csv.DictReader(csvfile, delimiter=';', fieldnames=csv_fields, restkey='suppliers')
        for line in records:
            imported = imported + 1
            try:
                product = Product.objects.only(
                    'forbid_ws_price_import',
                    'forbid_price_import',
                    'cur_code'
                ).get(article=line['article'])
                if line['sp_cur_code'] != '0':
                    try:
                        sp_cur_price = float(line['sp_cur_price'].replace('\xA0', ''))
                        product.sp_cur_price = int(round(sp_cur_price))
                        product.sp_cur_code = currencies.get(pk=line['sp_cur_code'])
                    except ValueError:
                        errors.append("%s: цена СП" % line['article'])
                if line['ws_cur_code'] != '0' and not product.forbid_ws_price_import:
                    try:
                        ws_cur_price = float(line['ws_cur_price'].replace('\xA0', ''))
                        if ws_cur_price > 0:
                            product.ws_cur_price = Decimal(ws_cur_price).quantize(Decimal('0.01'), rounding=ROUND_HALF_EVEN)
                        product.ws_cur_code = currencies.get(pk=line['ws_cur_code'])
                    except ValueError:
                        errors.append("%s: оптовая цена" % line['article'])
                if line['cur_code'] != '0' and not product.forbid_price_import:
                    try:
                        price = float(line['cur_price'].replace('\xA0', ''))
                        if price > 0 and product.cur_code.code == 643:
                            product.cur_price = int(round(price))
                    except ValueError:
                        errors.append("%s: розничная цена" % line['article'])
                product.save()
                products.add(product.id)
                for idx, quantity in enumerate(line['suppliers']):
                    if suppliers[idx] is None:
                        continue
                    try:
                        quantity = float(quantity.replace('\xA0', '').replace(',', '.'))
                        correction, reason = corrected_stocks.get(product.id, {}).get(suppliers[idx].id, (0, ''))
                        if (quantity or correction) and product.article != 'г66356':
                            table_copy.write('{}\t{}\t{}\t{}\t{}\n'.format(quantity, product.id, suppliers[idx].id, correction, reason))
                        try:
                            del corrected_stocks[product.id][suppliers[idx].id]
                            if not corrected_stocks[product.id]:
                                del corrected_stocks[product.id]
                        except KeyError:
                            pass
                        """
                        count = Stock.objects.filter(product=product, supplier=suppliers[idx]).update(quantity=quantity)
                        if count and quantity == 0.0:
                            s = Stock.objects.get(product=product, supplier=suppliers[idx])
                            if s.correction == 0.0:
                                s.delete()
                        if not count and quantity > 0.0:
                            s = Stock.objects.create(product=product, supplier=suppliers[idx], quantity=quantity)
                        """
                    except ValueError:
                        errors.append("%s: состояние складa" % line['article'])
                    except IndexError:
                        errors.append("%s: неправильное количество складов" % line['article'])
                updated = updated + 1
            except MultipleObjectsReturned:
                errors.append("%s: артикль не уникален" % line['article'])
            except ObjectDoesNotExist:
                # errors.append("%s: товар отсутсвует" % line['article'])
                pass
        for product, stocks in corrected_stocks.items():
            for stock, (correction, reason) in stocks.items():
                table_copy.write('{}\t{}\t{}\t{}\t{}\n'.format(0, product, stock, correction, reason))
        table_copy.seek(0)
        with connection.cursor() as cursor:
            enable_flag('1C_IMPORT_COPYING')
            cursor.execute("BEGIN")
            cursor.execute("TRUNCATE TABLE shop_stock RESTART IDENTITY")
            cursor.copy_from(table_copy, 'shop_stock', columns=('quantity', 'product_id', 'supplier_id', 'correction', 'reason'))
            cursor.execute("COMMIT")
            disable_flag('1C_IMPORT_COPYING')
    table_copy.close()
    tmp_file.close()

    for product_id in products:
        product = Product.objects.only(
            'num',
            'spb_num',
            'ws_num'
        ).get(id=product_id)
        product.num = -1
        product.spb_num = -1
        product.ws_num = -1
        product.save()
        if product_id in frozen_products.keys() and product.instock > 0:
            orders.update(frozen_products[product_id])
        if product_id in frozen_products.keys():
            log.error('F %d %d' % (product.id, product.instock))

    log.info('Frozen orders %s' % str(orders))

    disable_flag('1C_IMPORT_RUNNING')
    reload_maybe()
    msg_plain = render_to_string('mail/shop/import1c_result.txt',
                                 {'file': file, 'date': date, 'imported': imported, 'updated': updated, 'errors': errors,
                                  'orders': orders, 'opts': Order._meta})
    send_mail(
        'Импорт 1С из %s' % file,
        msg_plain,
        config.sw_email_from,
        sw_default_site.profile.manager_emails.split(','),
    )

    return date


@shared_task(autoretry_for=(EnvironmentError, DatabaseError), retry_backoff=60, retry_jitter=False)
def remove_outdated_baskets():
    threshold = timezone.now() - timedelta(seconds=settings.SESSION_COOKIE_AGE)
    baskets = Basket.objects.filter(created__lt=threshold)
    num = len(baskets)
    for basket in baskets.all():
        basket.delete()
    log.info('Deleted %d baskets' % num)
    SessionStore = import_module(settings.SESSION_ENGINE).SessionStore
    SessionStore.clear_expired()
    log.info('Cleared expired sessions')


@shared_task(bind=True, autoretry_for=(EnvironmentError, DatabaseError), retry_backoff=3, retry_jitter=False)
def notify_abandoned_basket(self, basket_id, email, phone):
    basket = Basket.objects.get(id=basket_id)

    reload_maybe()
    owner_info = getattr(settings, 'SHOP_OWNER_INFO', {})

    signer = signing.Signer()

    restore_url = 'https://{}{}'.format(
        sw_default_site.domain,
        reverse('shop:restore', args=[','.join(map(lambda i: '%s*%s' % (i.product.id, i.quantity), basket.items.all()))])
    )
    clear_url = 'https://{}{}'.format(
        sw_default_site.domain,
        reverse('shop:clear', args=[signer.sign(basket.id)])
    )

    unisender = Unisender(api_key=settings.UNISENDER_KEY)
    if email:
        context = {
            'owner_info': owner_info,
            'basket': basket,
            'restore_url': restore_url,
            'clear_url': clear_url
        }
        result = unisender.sendEmail(email, owner_info.get('short_name', ''), config.sw_email_unisender,
                                     'Вы забыли оформить заказ',
                                     render_to_string('mail/shop/basket_abandoned.html', context),
                                     settings.UNISENDER_ABANDONED_BASKET_LIST)
        # https://www.unisender.com/ru/support/api/common/api-errors/
        if unisender.errorMessage:
            if unisender.errorCode in ['retry_later', 'api_call_limit_exceeded_for_api_key', 'api_call_limit_exceeded_for_ip']:
                raise self.retry(countdown=60 * 60 * 2, max_retries=5, exc=Exception(unisender.errorMessage))  # 2 hours
            if unisender.errorCode == 'not_enough_money':
                raise self.retry(countdown=60 * 60 * 24, max_retries=5, exc=Exception(unisender.errorMessage))  # 24 hours
            return unisender.errorMessage
        # recipient errors
        for r in result['result']:
            if 'index' in r and r['index'] == 0:
                if 'errors' in r:
                    try:
                        return r['errors'][0]['message']
                    except Exception:
                        return str(r['errors'])
                else:
                    return r['id']
    elif phone:
        result = send_sms(phone, "Вы забыли оформить заказ: %s" % restore_url)
        try:
            return result['descr']
        except Exception:
            return result


@shared_task(autoretry_for=(EnvironmentError, DatabaseError), retry_backoff=3, retry_jitter=False)
def notify_abandoned_baskets(first_try=True):
    SessionStore = import_module(settings.SESSION_ENGINE).SessionStore

    if first_try:
        lt = timezone.now() - timedelta(hours=3)
        gt = lt - timedelta(hours=1)
    else:
        lt = timezone.now() - timedelta(days=3)
        gt = lt - timedelta(days=1)
    baskets = Basket.objects.filter(secondary=False, created__lt=lt, created__gte=gt)
    num = 0
    for basket in baskets.all():
        if basket.items.count() == 0:
            continue

        email = None
        phone = None

        session = SessionStore(session_key=basket.session_id).load()
        uid = session.get('_auth_user_id')
        if uid:
            user = ShopUser.objects.get(id=uid)
            if user.email:
                email = user.email
            if user.phone:
                phone = user.phone
        if phone is None and basket.phone:
            phone = basket.phone

        if email:  # or phone: отключили отправку смс
            notify_abandoned_basket.delay(basket.id, email, phone)
            num = num + 1
    log.info('Sent notifications for %d abandoned baskets' % num)
    return num


@shared_task(bind=True, autoretry_for=(EnvironmentError, DatabaseError), retry_backoff=60, retry_jitter=False)
def create_modulpos_order(self, order_id):
    order = Order.objects.get(id=order_id)
    if not order.courier:
        return 'Отсутствует привязка курьера'
    if not order.courier.pos_id:
        return 'Отсутствует привязка кассы к курьеру'
    items = []
    for item in order.items.all():
        items.append({
            'name': item.product.title,
            'measure': 'pcs',
            'inventoryType': 'INVENTORY',
            'quantity': item.quantity,
            'vatSum': 0,
            'vatTag': '1105',
            'sumWithVat': item.price
        })
    if order.delivery_price > 0:
        items.append({
            'name': "Доставка",
            'measure': 'other',
            'inventoryType': 'SERVICE',
            'quantity': 1,
            'vatSum': 0,
            'vatTag': '1105',
            'sumWithVat': str(order.delivery_price.quantize(Decimal('1'), rounding=ROUND_HALF_EVEN))
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

    reload_maybe()

    url = 'https://service.modulpos.ru/api/v2/retail-point/{}/order'.format(order.courier.pos_id)
    headers = {
        'Authorization': 'Basic {token}'.format(token=base64.standard_b64encode('{}:{}'.format(config.sw_modulkassa_login, config.sw_modulkassa_password).encode('utf-8')).decode('utf-8')),
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


@shared_task(bind=True, autoretry_for=(EnvironmentError, DatabaseError), retry_backoff=60, retry_jitter=False)
def delete_modulpos_order(self, order_id):
    order = Order.objects.get(id=order_id)
    if not order.courier:
        return 'Отсутствует привязка курьера'
    if not order.courier.pos_id:
        return 'Отсутствует привязка кассы к курьеру'
    if not order.hidden_tracking_number:
        return 'Отсутствует ID документа в кассе'

    reload_maybe()

    # get fiscal info
    url = 'https://service.modulpos.ru/api/v1/retail-point/{}/cashdocs?count=1&q=linkedDocId=={}'.format(order.courier.pos_id, order.hidden_tracking_number)
    headers = {
        'Authorization': 'Basic {token}'.format(token=base64.standard_b64encode('{}:{}'.format(config.sw_modulkassa_login, config.sw_modulkassa_password).encode('utf-8')).decode('utf-8')),
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
    url = 'https://service.modulpos.ru/api/v2/retail-point/{}/order/{}'.format(order.courier.pos_id, order.hidden_tracking_number)
    headers = {
        'Authorization': 'Basic {token}'.format(token=base64.standard_b64encode('{}:{}'.format(config.sw_modulkassa_login, config.sw_modulkassa_password).encode('utf-8')).decode('utf-8')),
        'Content-Type': 'application/json; charset=utf-8'
    }
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


@shared_task(bind=True, autoretry_for=(OSError, DatabaseError), retry_backoff=300, retry_jitter=False)
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


@shared_task(bind=True, autoretry_for=(OSError, DatabaseError), retry_backoff=600, retry_jitter=False)
def update_user_bonuses(self):
    reload_maybe()
    bonused_users = set(ShopUser.objects.filter(bonuses__gt=0).values_list('id', flat=True))
    filename = 'БонусныеБаллыИнфо.txt'
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


@shared_task(bind=True, autoretry_for=(EnvironmentError, DatabaseError), retry_backoff=3, retry_jitter=False)
def notify_expiring_bonus(self, phone):
    user = ShopUser.objects.get(phone=phone)
    today = datetime.today()
    base_format = SINGLE_DATE_FORMAT if today.year == user.expiration_date.year else SINGLE_DATE_FORMAT_WITH_YEAR
    text = "%d ваших %s действуют до %s. В Швейном Мире вы можете оплатить бонусами до 20%% от стоимости покупки! http://thsm.ru" % (
        user.expiring_bonuses,
        rupluralize(user.expiring_bonuses, "бонус,бонуса,бонусов"),
        date_format(user.expiration_date, format=base_format)
    )
    result = send_sms(user.phone, text, True)
    try:
        return result['descr']
    except Exception:
        return result


@shared_task(autoretry_for=(EnvironmentError, DatabaseError), retry_backoff=3, retry_jitter=False)
def notify_expiring_bonuses():
    lt = timezone.now() + timedelta(days=10)
    gt = lt - timedelta(days=1)
    users = ShopUser.objects.filter(expiring_bonuses__gte=100, expiration_date__lt=lt, expiration_date__gte=gt)
    num = 0
    for user in users.all():
        if user.phone:
            notify_expiring_bonus.delay(user.phone)
            num = num + 1
    log.info('Sent notifications for %d expiring bonuses' % num)
    return num
