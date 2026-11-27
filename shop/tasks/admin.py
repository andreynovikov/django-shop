from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string

from celery import shared_task

from constance import config

import reviews

from sewingworld.sms import send_sms
from sewingworld.telegram import TelegramError, send_message

from shop import integration_health
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


def post_to_staff(task, text):
    """ Posts to the staff channel, retrying as late as Telegram asks when it limits the rate """
    try:
        return send_message(text)
    except TelegramError as e:
        if e.retry_after:
            raise task.retry(exc=e, countdown=e.retry_after)
        raise


@shared_task(name='shop.tasks.notify_staff', bind=True, queue='priority', autoretry_for=(TelegramError,),
             max_retries=8, retry_backoff=True)
def notify_staff(self, text):
    """ Posts the text to the staff channel in Telegram """
    return post_to_staff(self, text)


@shared_task(name='shop.tasks.notify_integration_health', queue='priority', autoretry_for=(Exception,),
             default_retry_delay=60, retry_backoff=True)
def notify_integration_health(notices, raised):
    """
    Tells the managers about integration problems that shop/integration_health.py raised, or about their end: by
    mail to the managers of the channels, and in the staff channel through notify_staff, so that a Telegram failure
    never repeats the mail
    """
    notice = integration_health.render_notice(notices, raised)
    if notice.recipients:
        send_mail(notice.subject, notice.mail, config.sw_email_from, notice.recipients)
    notify_staff.delay(notice.telegram)


@shared_task(name='shop.tasks.notify_manager_telegram', bind=True, queue='priority', autoretry_for=(TelegramError,),
             max_retries=8, retry_backoff=True)
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
