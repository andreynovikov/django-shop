from __future__ import absolute_import

import sys
import csv

from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string

from celery import shared_task

from sewingworld import sms_uslugi

from shop.models import Supplier, Currency, Product, Stock, Order


@shared_task
def send_password(phone, password):
    #smsru_key = getattr(settings, 'SMSRU_KEY', None)
    sms_login = getattr(settings, 'SMS_USLUGI_LOGIN', None)
    sms_password = getattr(settings, 'SMS_USLUGI_PASSWORD', None)
    client = sms_uslugi.Client(sms_login, sms_password)
    client.send(phone, "%s" % password)


@shared_task
def notify_user_order_new_sms(order_id, password):
    order = Order.objects.get(id=order_id)
    sms_login = getattr(settings, 'SMS_USLUGI_LOGIN', None)
    sms_password = getattr(settings, 'SMS_USLUGI_PASSWORD', None)
    client = sms_uslugi.Client(sms_login, sms_password)
    password_text = ""
    if password:
        password_text = " Пароль %s" % password
    client.send(order.phone, "Состояние заказа №%s можно узнать в личном кабинете.%s" % (order_id, password_text))


@shared_task
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
            shop_settings['email_from'],
            [order.email,],
            html_message=msg_html,
        )


@shared_task
def notify_user_order_collected(order_id):
    order = Order.objects.get(id=order_id)
    sms_login = getattr(settings, 'SMS_USLUGI_LOGIN', None)
    sms_password = getattr(settings, 'SMS_USLUGI_PASSWORD', None)
    client = sms_uslugi.Client(sms_login, sms_password)
    client.send(order.phone, "Заказ №%s собран и ожидает оплаты. Нажмите ссылку \"Что с моим заказом?\"" \
                             " на сайте магазина \"Швейный Мир\", чтобы оплатить заказ." % order_id)

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
            shop_settings['email_from'],
            [order.email,],
            html_message=msg_html,
        )


@shared_task
def notify_user_order_delivered_shop(order_id):
    order = Order.objects.get(id=order_id)
    sms_login = getattr(settings, 'SMS_USLUGI_LOGIN', None)
    sms_password = getattr(settings, 'SMS_USLUGI_PASSWORD', None)
    client = sms_uslugi.Client(sms_login, sms_password)
    client.send(order.phone, "Ваш заказ доставлен в магазин Швейный Мир по адресу Волгоградский пр-т," \
                             " д.10 стр.2. Для получения заказа обратитесь в кассу и назовите номер" \
                             " заказа %s." % order_id)


@shared_task
def notify_user_order_delivered(order_id):
    order = Order.objects.get(id=order_id)
    if order.delivery == Order.DELIVERY_PICKPOINT:
        title = 'PickPoint'
    else:
        title = 'ТК'
    sms_login = getattr(settings, 'SMS_USLUGI_LOGIN', None)
    sms_password = getattr(settings, 'SMS_USLUGI_PASSWORD', None)
    client = sms_uslugi.Client(sms_login, sms_password)
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
            shop_settings['email_from'],
            [order.email,],
            html_message=msg_html,
        )


@shared_task
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
            shop_settings['email_from'],
            [order.email,],
            html_message=msg_html,
        )


@shared_task
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


@shared_task(time_limit=1200)
def import1c(file):
    import_dir = getattr(settings, 'SHOP_IMPORT_DIRECTORY', 'import')
    filepath = import_dir + '/' + file

    imported = 0
    updated = 0
    errors = []

    suppliers = Supplier.objects.all().order_by('order')
    currencies = Currency.objects.all()
    with open(filepath) as csvfile:
        next(csvfile)
        next(csvfile)
        all_products = Product.objects.all()
        csv_fields = ('article', 'sp_cur_price', 'sp_cur_code', 'ws_cur_price', 'ws_cur_code', 'cur_price', 'cur_code')
        records = csv.DictReader(csvfile, delimiter=';', fieldnames=csv_fields, restkey='suppliers')
        #products = {x.pk:x for x in all_products}
        for line in records:
            imported = imported + 1
            try:
                product = Product.objects.get(article=line['article'])
                if line['sp_cur_code'] is not '0':
                    try:
                        sp_cur_price = float(line['sp_cur_price'].replace('\xA0',''))
                        product.sp_cur_price = int(round(sp_cur_price))
                        product.sp_cur_code = currencies.get(pk=line['sp_cur_code'])
                    except ValueError:
                        errors.append("%s: цена СП" % line['article'])
                if line['ws_cur_code'] is not '0':
                    try:
                        ws_cur_price = float(line['ws_cur_price'].replace('\xA0',''))
                        if ws_cur_price > 0:
                            product.ws_cur_price = int(round(ws_cur_price))
                        product.ws_cur_code = currencies.get(pk=line['ws_cur_code'])
                    except ValueError:
                        errors.append("%s: оптовая цена" % line['article'])
                if line['cur_code'] is not '0' and not product.forbid_price_import:
                    try:
                        price = float(line['cur_price'].replace('\xA0',''))
                        if price > 0 and product.cur_code.code == 643:
                            product.cur_price = int(round(price))
                    except ValueError:
                        errors.append("%s: розничная цена" % line['article'])
                product.stock.clear()
                product.num = -1
                product.save()
                for idx, quantity in enumerate(line['suppliers']):
                    try:
                        quantity = float(quantity.replace('\xA0','').replace(',','.'))
                        s = Stock(product=product, supplier=suppliers[idx], quantity=quantity)
                        s.save()
                    except ValueError:
                        errors.append("%s: состояние складa" % line['article'])
                    except IndexError:
                        errors.append("%s: неправильное количество складов" % line['article'])
                #products[product.id].imported = True
                updated = updated + 1
            except MultipleObjectsReturned:
                errors.append("%s: артикль не уникален" % line['article'])
                next
            except ObjectDoesNotExist:
                #errors.append("%s: товар отсутсвует" % line['article'])
                next

        #for pk, product in products.items():
        #    if not hasattr(product, 'imported'):
                #product.number_inet = -1000
                #product.save()
                #reset = reset + 1

    shop_settings = getattr(settings, 'SHOP_SETTINGS', {})
    msg_plain = render_to_string('mail/shop/import1c_result.txt',
                                 {'file': file, 'imported': imported, 'updated': updated, 'errors': errors})

    send_mail(
        'Импорт 1С из %s' % file,
        msg_plain,
        shop_settings['email_from'],
        shop_settings['email_managers'],
    )
