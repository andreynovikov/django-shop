from __future__ import absolute_import

import logging

from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.core.validators import EmailValidator
from django.conf import settings
from django.template.loader import render_to_string
from django.urls import reverse
from django.contrib.sites.models import Site

from celery import shared_task

from djconfig import config, reload_maybe

from sewingworld.models import SiteProfile
from sewingworld.sms import send_sms

from shop.models import Order


log = logging.getLogger('shop')

sw_default_site = Site.objects.get_current()


def validate_email(email):
    validator = EmailValidator()
    try:
        validator(email)
        return True
    except ValidationError:
        return False


def get_site_for_order(order):
    if order.is_beru or order.is_from_market:
        return sw_default_site
    else:
        return order.site


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

        send_mail(
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
        reload_maybe()
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


@shared_task(autoretry_for=(Exception,), default_retry_delay=120, retry_backoff=True)
def notify_user_order_done(order_id):
    order = Order.objects.get(id=order_id)

    if order.email:
        if not validate_email(order.email):
            return
        reload_maybe()
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


@shared_task(autoretry_for=(Exception,), default_retry_delay=60, retry_backoff=True)
def notify_manager(order_id):
    order = Order.objects.get(id=order_id)
    site = get_site_for_order(order)
    site_profile = SiteProfile.objects.get(site=site)

    reload_maybe()
    msg_plain = render_to_string('mail/shop/order_manager.txt', {'order': order})
    msg_html = render_to_string('mail/shop/order_manager.html', {'order': order})

    site_text = ''
    if site != sw_default_site:
        site_text = ' (%s)' % site.domain
    managers = site_profile.managers or config.sw_email_managers
    send_mail(
        'Новый заказ №%s%s' % (order_id, site_text),
        msg_plain,
        config.sw_email_from,
        managers.split(','),
        html_message=msg_html,
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
