from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string

from celery import shared_task

from constance import config

import reviews

from sewingworld.sms import send_sms

from shop.models import Order

from .common import get_default_site


@shared_task(name='shop.tasks.notify_manager', queue="priority", autoretry_for=(Exception,), default_retry_delay=60, retry_backoff=True)
def notify_manager(order_id):
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
