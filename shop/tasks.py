from __future__ import absolute_import

import csv
import datetime
import logging
from collections import defaultdict
from importlib import import_module
from decimal import Decimal, ROUND_HALF_EVEN

import django.db
from django.core import signing
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.urls import reverse
from django.contrib.sites.models import Site

from celery import shared_task

from sewingworld import sms_uslugi, smsru

from shop.models import Supplier, Currency, Product, Stock, Basket, Order


log = logging.getLogger('shop')


@shared_task(autoretry_for=(Exception,), default_retry_delay=60, retry_backoff=True)
def send_message(phone, message):
    smsru_key = getattr(settings, 'SMSRU_KEY', None)
    sms_login = getattr(settings, 'SMS_USLUGI_LOGIN', None)
    sms_password = getattr(settings, 'SMS_USLUGI_PASSWORD', None)
    client = sms_uslugi.Client(sms_login, sms_password)
    #client = smsru.Client(smsru_key)
    client.send(phone, message)


@shared_task(autoretry_for=(Exception,), default_retry_delay=15, retry_backoff=True)
def send_password(phone, password):
    smsru_key = getattr(settings, 'SMSRU_KEY', None)
    sms_login = getattr(settings, 'SMS_USLUGI_LOGIN', None)
    sms_password = getattr(settings, 'SMS_USLUGI_PASSWORD', None)
    client = sms_uslugi.Client(sms_login, sms_password)
    #client = smsru.Client(smsru_key)
    client.send(phone, "Пароль для доступа на сайт: %s" % password)


@shared_task(autoretry_for=(Exception,), default_retry_delay=60, retry_backoff=True)
def notify_user_order_new_sms(order_id, password):
    order = Order.objects.get(id=order_id)
    smsru_key = getattr(settings, 'SMSRU_KEY', None)
    sms_login = getattr(settings, 'SMS_USLUGI_LOGIN', None)
    sms_password = getattr(settings, 'SMS_USLUGI_PASSWORD', None)
    client = sms_uslugi.Client(sms_login, sms_password)
    #client = smsru.Client(smsru_key)
    password_text = ""
    if password:
        password_text = " Пароль: %s" % password
    client.send(order.phone, "Состояние заказа №%s можно узнать в личном кабинете: https://%s%s %s" \
                    % (order_id, Site.objects.get_current().domain, reverse('shop:user_orders'), password_text))


@shared_task(autoretry_for=(Exception,), default_retry_delay=120, retry_backoff=True)
def notify_user_order_new_mail(order_id):
    order = Order.objects.get(id=order_id)
    if order.email:
        shop_settings = getattr(settings, 'SHOP_SETTINGS', {})
        context = {
            'owner_info': getattr(settings, 'SHOP_OWNER_INFO', {}),
            'order': order
        }
        msg_plain = render_to_string('mail/shop/order_new.txt', context)
        msg_html = render_to_string('mail/shop/order_new.html', context)

        send_mail(
            'Ваш заказ №%s принят' % order_id,
            msg_plain,
            config.sw_email_from,
            [order.email],
            html_message=msg_html,
        )


@shared_task(autoretry_for=(Exception,), retry_backoff=True)
def notify_user_order_collected(order_id):
    order = Order.objects.get(id=order_id)
    smsru_key = getattr(settings, 'SMSRU_KEY', None)
    sms_login = getattr(settings, 'SMS_USLUGI_LOGIN', None)
    sms_password = getattr(settings, 'SMS_USLUGI_PASSWORD', None)
    client = sms_uslugi.Client(sms_login, sms_password)
    #client = smsru.Client(smsru_key)
    client.send(order.phone, "Заказ №%s собран и ожидает оплаты. Перейдите по ссылке, чтобы оплатить заказ: https://%s%s" \
                    % (order_id, Site.objects.get_current().domain, reverse('shop:order', args=[order_id])))

    if order.email:
        shop_settings = getattr(settings, 'SHOP_SETTINGS', {})
        context = {
            'owner_info': getattr(settings, 'SHOP_OWNER_INFO', {}),
            'order': order
        }
        msg_plain = render_to_string('mail/shop/order_collected.txt', context)
        msg_html = render_to_string('mail/shop/order_collected.html', context)

        send_mail(
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
    smsru_key = getattr(settings, 'SMSRU_KEY', None)
    sms_login = getattr(settings, 'SMS_USLUGI_LOGIN', None)
    sms_password = getattr(settings, 'SMS_USLUGI_PASSWORD', None)
    client = sms_uslugi.Client(sms_login, sms_password)
    #client = smsru.Client(smsru_key)
    client.send(order.phone, "Ваш заказ доставлен в магазин \"%s\" по адресу %s, %s." \
                             " Для получения заказа обратитесь в кассу и назовите номер" \
                             " заказа %s." % (name, city, address, order_id))


@shared_task(autoretry_for=(Exception,), retry_backoff=True)
def notify_user_order_delivered(order_id):
    order = Order.objects.get(id=order_id)
    if order.delivery == Order.DELIVERY_PICKPOINT:
        title = 'PickPoint'
    else:
        title = 'ТК'
    smsru_key = getattr(settings, 'SMSRU_KEY', None)
    sms_login = getattr(settings, 'SMS_USLUGI_LOGIN', None)
    sms_password = getattr(settings, 'SMS_USLUGI_PASSWORD', None)
    client = sms_uslugi.Client(sms_login, sms_password)
    #client = smsru.Client(smsru_key)
    client.send(order.phone, "Заказ №%s доставлен в %s: %s" % (order_id, title, order.delivery_info))

    if order.email:
        shop_settings = getattr(settings, 'SHOP_SETTINGS', {})
        context = {
            'owner_info': getattr(settings, 'SHOP_OWNER_INFO', {}),
            'order': order
        }
        msg_plain = render_to_string('mail/shop/order_delivered.txt', context)
        msg_html = render_to_string('mail/shop/order_delivered.html', context)

        send_mail(
            'Получение заказа №%s' % order_id,
            msg_plain,
            config.sw_email_from,
            [order.email],
            html_message=msg_html,
        )


@shared_task(autoretry_for=(Exception,), retry_backoff=True)
def notify_user_order_done(order_id):
    order = Order.objects.get(id=order_id)

    if order.email:
        shop_settings = getattr(settings, 'SHOP_SETTINGS', {})
        context = {
            'owner_info': getattr(settings, 'SHOP_OWNER_INFO', {}),
            'order': order
        }
        msg_plain = render_to_string('mail/shop/order_done.txt', context)
        msg_html = render_to_string('mail/shop/order_done.html', context)

        send_mail(
            'Заказ №%s выполнен' % order_id,
            msg_plain,
            config.sw_email_from,
            [order.email],
            html_message=msg_html,
        )


@shared_task(bind=True, autoretry_for=(EnvironmentError, django.db.Error), retry_backoff=300, retry_jitter=False)
def notify_user_review_products(self, order_id):
    order = Order.objects.get(id=order_id)

    if order.email:
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
                raise self.retry(countdown=60*60*2, max_retries=5, exc=Exception(unisender.errorMessage))  # 2 hours
            if unisender.errorCode == 'not_enough_money':
                raise self.retry(countdown=60*60*24, max_retries=5, exc=Exception(unisender.errorMessage))  # 24 hours
            return unisender.errorMessage

        # recipient errors
        for r in result['result']:
            if 'index' in r and r['index'] == 0:
                if 'errors' in r:
                    try:
                        return r['errors'][0]['message']
                    except:
                        return str(r['errors'])
                else:
                    return r['id']


@shared_task(autoretry_for=(Exception,), default_retry_delay=60, retry_backoff=True)
def notify_manager(order_id):
    order = Order.objects.get(id=order_id)

    shop_settings = getattr(settings, 'SHOP_SETTINGS', {})
    msg_plain = render_to_string('mail/shop/order_manager.txt', {'order': order})
    msg_html = render_to_string('mail/shop/order_manager.html', {'order': order})

    send_mail(
        'Новый заказ №%s' % order_id,
        msg_plain,
        shop_settings['email_from'],
        shop_settings['email_managers'],
        html_message=msg_html,
    )


@shared_task(autoretry_for=(Exception,), default_retry_delay=60, retry_backoff=True)
def notify_review_posted(review_id):
    review = reviews.get_model().objects.get(id=review_id)

    shop_settings = getattr(settings, 'SHOP_SETTINGS', {})
    msg_plain = render_to_string('mail/reviews/review_posted.txt', {'review': review})

    send_mail(
        'Новый обзор для %s' % review.content_object,
        msg_plain,
        shop_settings['email_from'],
        [manager_tuple[1] for manager_tuple in settings.MANAGERS]
    )


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


@shared_task(time_limit=2400, autoretry_for=(Exception,), retry_backoff=True)
def import1c(file):
    frozen_orders = Order.objects.filter(status=Order.STATUS_FROZEN)
    frozen_products = defaultdict(list)
    if frozen_orders.exists():
        for order in frozen_orders:
            for item in order.items.all():
                quantity = 0
                stock = Stock.objects.filter(product=item.product)
                if stock.exists():
                    for s in stock:
                        quantity = quantity + s.quantity + s.correction
                if quantity <= 0:
                    frozen_products[item.product].append(order)

    import_dir = getattr(settings, 'SHOP_IMPORT_DIRECTORY', 'import')
    filepath = import_dir + '/' + file

    imported = 0
    updated = 0
    errors = []
    orders = set()
    suppliers = []
    currencies = Currency.objects.all()
    with fragile(open(filepath)) as csvfile:
        next(csvfile)
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
                product = Product.objects.get(article=line['article'])
                if line['sp_cur_code'] != '0':
                    try:
                        sp_cur_price = float(line['sp_cur_price'].replace('\xA0', ''))
                        product.sp_cur_price = int(round(sp_cur_price))
                        product.sp_cur_code = currencies.get(pk=line['sp_cur_code'])
                    except ValueError:
                        errors.append("%s: цена СП" % line['article'])
                if line['ws_cur_code'] is not '0' and not product.forbid_ws_price_import:
                    try:
                        ws_cur_price = float(line['ws_cur_price'].replace('\xA0', ''))
                        if ws_cur_price > 0:
                            product.ws_cur_price = Decimal(ws_cur_price).quantize(Decimal('0.01'), rounding=ROUND_HALF_EVEN)
                        product.ws_cur_code = currencies.get(pk=line['ws_cur_code'])
                    except ValueError:
                        errors.append("%s: оптовая цена" % line['article'])
                if line['cur_code'] is not '0' and not product.forbid_price_import:
                    try:
                        price = float(line['cur_price'].replace('\xA0', ''))
                        if price > 0 and product.cur_code.code == 643:
                            product.cur_price = int(round(price))
                    except ValueError:
                        errors.append("%s: розничная цена" % line['article'])
                #product.stock.clear()
                product.save()
                for idx, quantity in enumerate(line['suppliers']):
                    if suppliers[idx] is None:
                        continue
                    try:
                        quantity = float(quantity.replace('\xA0', '').replace(',', '.'))
                        count = Stock.objects.filter(product=product, supplier=suppliers[idx]).update(quantity=quantity)
                        if count and quantity == 0.0:
                            s = Stock.objects.get(product=product, supplier=suppliers[idx])
                            if s.correction == 0.0:
                                s.delete()
                    except ValueError:
                        errors.append("%s: состояние складa" % line['article'])
                    except IndexError:
                        errors.append("%s: неправильное количество складов" % line['article'])
                product.num = -1
                product.spb_num = -1
                product.save()
                if product in frozen_products.keys() and product.instock > 0:
                    orders.update(frozen_products[product])
                updated = updated + 1
            except MultipleObjectsReturned:
                errors.append("%s: артикль не уникален" % line['article'])
                next
            except ObjectDoesNotExist:
                # errors.append("%s: товар отсутсвует" % line['article'])
                pass

    shop_settings = getattr(settings, 'SHOP_SETTINGS', {})
    msg_plain = render_to_string('mail/shop/import1c_result.txt',
                                 {'file': file, 'imported': imported, 'updated': updated, 'errors': errors,
                                  'orders': orders, 'opts': Order._meta})
    send_mail(
        'Импорт 1С из %s' % file,
        msg_plain,
        shop_settings['email_from'],
        shop_settings['email_managers'],
    )


@shared_task(autoretry_for=(Exception,), retry_backoff=True)
def remove_outdated_baskets():
    threshold = datetime.datetime.now() - datetime.timedelta(days=90)
    baskets = Basket.objects.filter(created__lt=threshold)
    num = len(baskets)
    for basket in baskets.all():
        basket.delete()
    log.info('Deleted %d baskets' % num)
    SessionStore = import_module(settings.SESSION_ENGINE).SessionStore
    SessionStore.clear_expired()
    log.info('Cleared expired sessions')


@shared_task(bind=True, autoretry_for=(EnvironmentError, django.db.Error), retry_backoff=3, retry_jitter=False)
def notify_abandoned_basket(self, basket_id, email, phone):
    basket = Basket.objects.get(id=basket_id)

    reload_maybe()
    owner_info = getattr(settings, 'SHOP_OWNER_INFO', {})

    signer = signing.Signer()

    restore_url = 'https://{}{}'.format(
        Site.objects.get_current().domain,
        reverse('shop:restore', args=[','.join(map(lambda i: '%s*%s' % (i.product.id, i.quantity), basket.items.all()))])
    )
    clear_url = 'https://{}{}'.format(
        Site.objects.get_current().domain,
        reverse('shop:clear', args=[signer.sign(basket.id)])
    )
    import sys
    print(restore_url, file=sys.stderr)
    print(clear_url, file=sys.stderr)

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
                raise self.retry(countdown=60*60*2, max_retries=5, exc=Exception(unisender.errorMessage))  # 2 hours
            if unisender.errorCode == 'not_enough_money':
                raise self.retry(countdown=60*60*24, max_retries=5, exc=Exception(unisender.errorMessage))  # 24 hours
            return unisender.errorMessage
        # recipient errors
        for r in result['result']:
            if 'index' in r and r['index'] == 0:
                if 'errors' in r:
                    try:
                        return r['errors'][0]['message']
                    except:
                        return str(r['errors'])
                else:
                    return r['id']
    elif phone:
        result = send_sms(phone, "Вы забыли оформить заказ: %s" % restore_url)
        try:
            return result['descr']
        except:
            return result


@shared_task(autoretry_for=(EnvironmentError, django.db.Error), retry_backoff=3, retry_jitter=False)
def notify_abandoned_baskets(first_try=True):
    SessionStore = import_module(settings.SESSION_ENGINE).SessionStore

    if first_try:
        lt = timezone.now() - datetime.timedelta(hours=3)
        gt = lt - datetime.timedelta(hours=1)
    else:
        lt = timezone.now() - datetime.timedelta(days=3)
        gt = lt - datetime.timedelta(days=1)
    baskets = Basket.objects.filter(secondary=False, created__lt=lt, created__gte=gt)
    num = 0
    for basket in baskets.all():
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
        log.info('email: %s phone: %s' % (email, phone))

        if email or phone:
            notify_abandoned_basket.delay(basket.id, email, phone)
            num = num + 1
    log.info('Sent notifications for %d abandoned baskets' % num)
    return num
