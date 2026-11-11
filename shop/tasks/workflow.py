import logging

import requests

from collections import defaultdict
from datetime import timedelta
from importlib import import_module

from django.contrib.admin.models import LogEntry, CHANGE
from django.conf import settings
from django.db import Error as DatabaseError
from django.db.models.fields.json import JSONField
from django.db.models.fields.related import RelatedField
from django.db.models.fields.reverse_related import ForeignObjectRel
from django.utils import timezone

from celery import shared_task

from sewingworld.tasks import PRIORITY_IDLE

from shop.models import ShopUser, Product, Basket, Order


log = logging.getLogger('shop')


@shared_task(name='shop.tasks.update_order', bind=True, queue="priority", autoretry_for=(DatabaseError,), max_retries=12, retry_backoff=300, retry_jitter=False)
def update_order(self, order_id, data):
    order = Order.objects.get(id=order_id)
    if order.owner:
        if self.request.retries < self.max_retries - 1:
            log.info('Locked by %s, retrying' % order.owner)
            raise self.retry(countdown=600)  # 10 minutes
        else:
            log.warning('Locked by %s, force unlocking' % order.owner)
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
        try:
            order.save(update_fields=changed.keys())
        except Exception as e:
            e.add_note("Failed to save info {}".format(str(data)))
            raise
        change_message = ', '.join(map(lambda item: '{}: {}'.format(item[0], item[1]), changed.items()))
    order.owner = None
    order.save()
    if change_message:
        LogEntry.objects.log_actions(
            user_id=order.user.id,
            queryset=Order.objects.filter(id=order.id),
            action_flag=CHANGE,
            change_message=change_message
        )
    return change_message


@shared_task(name='shop.tasks.revalidate_nextjs', queue="revalidation")  # , rate_limit='2/s')
def revalidate_nextjs(domain, token, payload):
    url = 'https://{}/api/revalidate'.format(domain)
    request_data = {
        'secret': token,
        **payload
    }
    response = requests.post(url, json=request_data)
    try:
        response_data = response.json()
        return response_data
    except:  # noqa E722
        return False


@shared_task(name='shop.tasks.post_update_product', queue="revalidation")
def post_update_product(product_id, origin):
    product = Product.objects.get(pk=product_id)

    if origin == 'admin':
        product.update_fts_vector()

    payload = {
        'model': 'product',
        'pk': product.pk,
        'code': product.code
    }
    for site in product.sites.exclude(profile__revalidation_token__exact=''):
        revalidate_nextjs.s(site.domain, site.profile.revalidation_token, payload).apply_async(priority=PRIORITY_IDLE)

    return None


@shared_task(name='shop.tasks.post_update_products', queue="priority")
def post_update_products(product_ids):
    nextjs_sites = defaultdict(list)

    for product_id in product_ids:
        product = Product.objects.get(pk=product_id)
        for site in product.sites.exclude(profile__revalidation_token__exact=''):
            nextjs_sites[site].append({'pk': product.pk, 'code': product.code})

    num = 0
    for site in nextjs_sites:
        num += len(nextjs_sites[site])
        for i in range(0, len(nextjs_sites[site]), 1000):
            payload = {
                'model': 'product',
                'items': nextjs_sites[site][i:i + 1000]
            }
            revalidate_nextjs.s(site.domain, site.profile.revalidation_token, payload).apply_async(priority=PRIORITY_IDLE)

    return num


@shared_task(name='shop.tasks.remove_outdated_baskets', autoretry_for=(EnvironmentError, DatabaseError), retry_backoff=60, retry_jitter=False)
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
