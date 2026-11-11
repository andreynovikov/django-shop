import logging

from datetime import datetime, timedelta
from importlib import import_module

from django.core import signing
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.core.validators import EmailValidator
from django.views.decorators.debug import sensitive_variables
from django.conf import settings
from django.db import Error as DatabaseError
from django.template.loader import render_to_string
from django.utils import dateparse, timezone
from django.utils.formats import date_format
from django.contrib.sites.models import Site

from celery import shared_task

from constance import config

from unisender import Unisender

from sewingworld.models import SiteProfile
from sewingworld.sms import send_sms
from sewingworld.templatetags.rupluralize import rupluralize

from shop import email_confirmation
from shop.models import ShopUser, Basket, Order

from .common import SINGLE_DATE_FORMAT, SINGLE_DATE_FORMAT_WITH_YEAR, get_default_site


log = logging.getLogger('shop')


def validate_email(email):
    validator = EmailValidator()
    try:
        validator(email)
        return True
    except ValidationError:
        return False


def get_site_for_order(order):
    if order.integration:
        return get_default_site()
    else:
        return order.site


# A postponed mail is checked again after the time it has already waited: 10 minutes, 20, 40 and so on up to 6 hours
MAIL_POSTPONE_FIRST = timedelta(minutes=10)
MAIL_POSTPONE_MAX = timedelta(hours=6)


def confirmed_email(order):
    """ The order's address if it is its buyer's confirmed one: mail goes to confirmed addresses only """
    user = order.user
    if order.email and user.email_verified and user.email.lower() == order.email.lower() and validate_email(order.email):
        return order.email
    return None


def postpone_mail(task, order, since):
    """
    Runs the task again later, while the order's address can still be confirmed: until a confirmation link
    sent when the task first ran would expire. Returns False when there is nothing to wait for.
    """
    if not order.email or not validate_email(order.email):
        return False
    now = timezone.now()
    since = dateparse.parse_datetime(since) if since else now
    if now >= since + email_confirmation.LIFETIME:
        log.info('Order %s: %s is not confirmed, mail %s dropped' % (order.id, order.email, task.name))
        return False
    delay = min(MAIL_POSTPONE_MAX, max(MAIL_POSTPONE_FIRST, now - since))
    # Celery keeps tasks with a countdown in Redis, whose visibility_timeout (8 days) is longer than any delay here
    task.apply_async((order.id,), {'since': since.isoformat()}, countdown=delay.total_seconds())
    return True


@shared_task(name='shop.tasks.send_message', queue="priority", autoretry_for=(Exception,), default_retry_delay=60, retry_backoff=True)
def send_message(phone, message):
    return send_sms(phone, message)


@shared_task(name='shop.tasks.send_password', queue="priority", autoretry_for=(Exception,), default_retry_delay=15, retry_backoff=True)
@sensitive_variables()  # the code is in the SMS text down the stack
def send_password(phone, password):
    return send_sms(phone, "Код для доступа на сайт: %s" % password)


@shared_task(name='shop.tasks.send_phone_code', queue="priority", autoretry_for=(Exception,), default_retry_delay=15, retry_backoff=True)
@sensitive_variables()  # the code is in the SMS text down the stack
def send_phone_code(phone, code):
    return send_sms(phone, "Код подтверждения телефона: %s" % code)


@shared_task(name='shop.tasks.send_email_confirmation', queue="priority", autoretry_for=(Exception,), default_retry_delay=60, retry_backoff=True)
def send_email_confirmation(user_id, email, site_id):
    """ The only mail to an address that is not confirmed yet: it carries just the link that confirms it """
    user = ShopUser.objects.filter(id=user_id).first()
    if user is None or user.email != email or user.email_verified or not validate_email(email):
        return None  # changed or confirmed since
    site = Site.objects.get(id=site_id)
    context = {
        'site': site,
        'site_profile': SiteProfile.objects.filter(site=site).first(),
        'link': email_confirmation.make_link(site, user),
        'lifetime_days': email_confirmation.LIFETIME.days,
    }
    return send_mail(
        'Подтверждение адреса эл.почты',
        render_to_string('mail/shop/email_confirmation.txt', context),
        config.sw_email_from,
        [email],
        html_message=render_to_string('mail/shop/email_confirmation.html', context),
    )


@shared_task(name='shop.tasks.notify_user_order_new_sms', queue="priority", autoretry_for=(Exception,), default_retry_delay=60, retry_backoff=True)
def notify_user_order_new_sms(order_id, password=None):
    order = Order.objects.get(id=order_id)
    site = get_site_for_order(order)
    password_text = ""
    if password:
        password_text = " Пароль: %s" % password
    return send_sms(order.phone, "Состояние заказа №%s можно узнать в личном кабинете: https://%s/user/orders/ %s"
                                 % (order_id, site.domain, password_text))


@shared_task(name='shop.tasks.notify_user_order_new_mail', autoretry_for=(Exception,), default_retry_delay=120, retry_backoff=True)
def notify_user_order_new_mail(order_id, since=None):
    order = Order.objects.get(id=order_id)
    email = confirmed_email(order)
    if email is None:
        return 'postponed' if postpone_mail(notify_user_order_new_mail, order, since) else None
    site = get_site_for_order(order)
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
        [email],
        html_message=msg_html,
    )


@shared_task(name='shop.tasks.notify_user_order_collected', autoretry_for=(Exception,), default_retry_delay=120, retry_backoff=True)
def notify_user_order_collected(order_id, since=None):
    order = Order.objects.get(id=order_id)
    site = get_site_for_order(order)
    if since is None:  # not again when the mail was postponed
        send_sms(order.phone, "Заказ №%s собран и ожидает оплаты. Перейдите по ссылке, чтобы оплатить заказ: https://%s/user/orders/%s/"
                              % (order_id, site.domain, order_id))

    email = confirmed_email(order)
    if email is None:
        return 'postponed' if postpone_mail(notify_user_order_collected, order, since) else None
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
        [email],
        html_message=msg_html,
    )


@shared_task(name='shop.tasks.notify_user_order_delivered_shop', autoretry_for=(Exception,), retry_backoff=True)
def notify_user_order_delivered_shop(order_id):
    order = Order.objects.get(id=order_id)
    city = order.store.city.name
    address = order.store.address
    name = order.store.name
    send_sms(order.phone, "Ваш заказ доставлен в магазин \"%s\" по адресу %s, %s."
                          " Для получения заказа обратитесь в кассу и назовите номер"
                          " заказа %s." % (name, city, address, order_id))


@shared_task(name='shop.tasks.notify_user_order_delivered', autoretry_for=(Exception,), retry_backoff=True)
def notify_user_order_delivered(order_id, since=None):
    order = Order.objects.get(id=order_id)
    if since is None:  # not again when the mail was postponed
        if order.delivery == Order.DELIVERY_PICKPOINT:
            title = 'PickPoint'
        else:
            title = 'ТК'
        send_sms(order.phone, "Заказ №%s доставлен в %s: %s" % (order_id, title, order.delivery_info))

    email = confirmed_email(order)
    if email is None:
        return 'postponed' if postpone_mail(notify_user_order_delivered, order, since) else None
    site = get_site_for_order(order)
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
        [email],
        html_message=msg_html,
    )


@shared_task(name='shop.tasks.notify_user_review_products', bind=True, autoretry_for=(EnvironmentError, DatabaseError), retry_backoff=300, retry_jitter=False)
def notify_user_review_products(self, order_id, since=None):
    order = Order.objects.get(id=order_id)

    email = confirmed_email(order)
    if email is None:
        return 'postponed' if postpone_mail(notify_user_review_products, order, since) else None
    owner_info = getattr(settings, 'SHOP_OWNER_INFO', {})
    context = {
        'owner_info': owner_info,
        'order': order
    }
    msg_html = render_to_string('mail/shop/order_review_products.html', context)

    unisender = Unisender(api_key=settings.UNISENDER_KEY)
    result = unisender.sendEmail(email, owner_info.get('short_name', ''), config.sw_email_unisender,
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


@shared_task(name='shop.tasks.notify_abandoned_basket', bind=True, autoretry_for=(EnvironmentError, DatabaseError), retry_backoff=3, retry_jitter=False)
def notify_abandoned_basket(self, basket_id, email, phone):
    basket = Basket.objects.get(id=basket_id)

    owner_info = getattr(settings, 'SHOP_OWNER_INFO', {})

    signer = signing.Signer()
    default_site = get_default_site()

    # TODO: basket should be linked to site (or session?)
    # Pages of the storefront, which send the link's data to BasketViewSet.restore and clear
    restore_url = 'https://{}/shop/basket/restore/{}/'.format(default_site.domain, basket.link_contents())
    clear_url = 'https://{}/shop/basket/clear/{}/'.format(default_site.domain, signer.sign(basket.id))

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


@shared_task(name='shop.tasks.notify_abandoned_baskets', autoretry_for=(EnvironmentError, DatabaseError), retry_backoff=3, retry_jitter=False)
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
            if user.email and user.email_verified:  # not postponed: the second pass, 3 days later, sees it confirmed
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


@shared_task(name='shop.tasks.notify_expiring_bonus', autoretry_for=(EnvironmentError, DatabaseError), retry_backoff=3, retry_jitter=False)
def notify_expiring_bonus(phone):
    user = ShopUser.objects.get(phone=phone)
    today = datetime.today()
    base_format = SINGLE_DATE_FORMAT if today.year == user.expiration_date.year else SINGLE_DATE_FORMAT_WITH_YEAR
    text = "Ваши %d %s сгорят %s www.thsm.ru" % (
        user.expiring_bonuses,
        rupluralize(user.expiring_bonuses, "бонус,бонуса,бонусов"),
        date_format(user.expiration_date, format=base_format)
    )
    result = send_sms(user.phone, text, True)
    try:
        return {
            'result': result['descr'],
            'bonuses': user.expiring_bonuses,
            'expiration': date_format(user.expiration_date, format=base_format)
        }
    except Exception:
        return result


@shared_task(name='shop.tasks.notify_expiring_bonuses', autoretry_for=(EnvironmentError, DatabaseError), retry_backoff=3, retry_jitter=False)
def notify_expiring_bonuses():
    """ 2 weeks and > 500 bonuses """
    lt = timezone.now() + timedelta(days=14)
    gt = lt - timedelta(days=1)
    users = ShopUser.objects.filter(expiring_bonuses__gt=500, expiration_date__lt=lt, expiration_date__gte=gt)
    num = 0
    for user in users.all():
        if user.phone:
            notify_expiring_bonus.delay(user.phone)
            num = num + 1
    log.info('Sent notifications for %d expiring bonuses' % num)
    return num
