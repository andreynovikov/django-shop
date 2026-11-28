from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone

from celery import shared_task
from celery.utils.time import get_exponential_backoff_interval, maybe_iso8601, maybe_make_aware

from constance import config

import reviews

from sewingworld.sms import send_sms
from sewingworld.telegram import TelegramError, send_message

from shop import health
from shop.models import Order

from .common import get_default_site


@shared_task(name='shop.tasks.notify_manager', queue="priority", autoretry_for=(Exception,), default_retry_delay=60, retry_backoff=True)
def notify_manager(order_id):
    """ Mails the new order to the managers of its site, or of the main site when it has none """
    order = Order.objects.get(id=order_id)

    msg_plain = render_to_string('mail/shop/order_manager.txt', {'order': order})
    msg_html = render_to_string('mail/shop/order_manager.html', {'order': order})

    default_site = get_default_site()
    site_text = ''
    if order.site != default_site:
        site_text = ' (%s)' % order.site.domain

    if hasattr(order.site, 'profile') and order.site.profile.manager_emails:
        managers = order.site.profile.manager_emails
    else:
        managers = default_site.profile.manager_emails
    send_mail(
        'Новый заказ №%s%s' % (order_id, site_text),
        msg_plain,
        config.sw_email_from,
        managers.split(','),
        html_message=msg_html,
    )


# Telegram is not always reachable from the server: staff notices are retried until they are two days old, then they
# are outdated. A notice that waited in the queue as long expires unsent.
TELEGRAM_RETRY_FOR = timedelta(days=2)
TELEGRAM_BACKOFF = 60  # seconds before the first retry, doubled for each next one
TELEGRAM_BACKOFF_MAX = 1800  # seconds between retries at most
TELEGRAM_TASK = {'bind': True, 'queue': 'priority', 'max_retries': None,
                 'expires': int(TELEGRAM_RETRY_FOR.total_seconds())}


def post_to_staff(task, text):
    """
    Posts to the staff channel. A failed post is retried with backoff, or as late as Telegram asks when it limits the
    rate, while the retry comes before the task expires; after that the TelegramError fails the task.
    """
    try:
        return send_message(text)
    except TelegramError as e:
        countdown = e.retry_after or get_exponential_backoff_interval(TELEGRAM_BACKOFF, task.request.retries,
                                                                      TELEGRAM_BACKOFF_MAX)
        if task.request.expires:
            expires = maybe_make_aware(maybe_iso8601(task.request.expires))
        else:  # queued before the tasks expired, or run without a worker
            expires = timezone.now() + TELEGRAM_RETRY_FOR
        if timezone.now() + timedelta(seconds=countdown) >= expires:
            raise
        raise task.retry(exc=e, countdown=countdown, expires=expires)


@shared_task(name='shop.tasks.notify_staff', **TELEGRAM_TASK)
def notify_staff(self, text):
    """ Posts the text to the staff channel in Telegram """
    return post_to_staff(self, text)


@shared_task(name='shop.tasks.notify_health', queue='priority', autoretry_for=(Exception,),
             default_retry_delay=60, retry_backoff=True)
def notify_health(notices, raised):
    """
    Tells the managers about problems that shop/health.py raised, or about their end: by mail to the managers of the
    channels (of the main site for checks without an integration), and in the staff channel through notify_staff, so
    that a Telegram failure never repeats the mail
    """
    notice = health.render_notice(notices, raised)
    if notice.recipients:
        send_mail(notice.subject, notice.mail, config.sw_email_from, notice.recipients)
    notify_staff.delay(notice.telegram)


@shared_task(name='shop.tasks.notify_manager_telegram', **TELEGRAM_TASK)
def notify_manager_telegram(self, order_id):
    """ Posts a new order to the staff channel: its number, site (unless the main one), total and admin link """
    order = Order.objects.select_related('site').get(id=order_id)
    site_text = ''
    if order.site_id != get_default_site().id:
        site_text = f' ({order.site.domain})'
    text = (f'Новый заказ №{order.id}{site_text}\n'
            f'Сумма: {order.total} руб.\n'
            f'https://admin.sewing-world.ru/admin/shop/order/{order.id}/change/')
    return post_to_staff(self, text)


@shared_task(name='shop.tasks.notify_manager_sms', queue="priority", autoretry_for=(Exception,), default_retry_delay=60, retry_backoff=True)
def notify_manager_sms(order_id, phone):
    return send_sms(phone, "Новый заказ №%s" % order_id)


@shared_task(name='shop.tasks.notify_review_posted', autoretry_for=(Exception,), default_retry_delay=60, retry_backoff=True)
def notify_review_posted(review_id):
    review = reviews.get_review_model().objects.get(id=review_id)

    msg_plain = render_to_string('mail/reviews/review_posted.txt', {'review': review})

    return send_mail(
        'Новый обзор для %s' % review.content_object,
        msg_plain,
        config.sw_email_from,
        [manager_tuple[1] for manager_tuple in settings.MANAGERS]
    )
