import logging

import requests

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

from shop.models import ShopUser, Product, Basket, Order
from shop.revalidation import revalidate_products


log = logging.getLogger('shop')


@shared_task(name='shop.tasks.update_order', bind=True, queue="priority", autoretry_for=(DatabaseError,), max_retries=12, retry_backoff=300, retry_jitter=False)
def update_order(self, order_id, data):
    order = Order.objects.get(id=order_id)
    # The admin sets the order owner while a staff member is editing.
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
            if isinstance(field, JSONField):  # Keep keys omitted by a partial marketplace update.
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


class StorefrontUnavailable(Exception):
    pass


@shared_task(name='shop.tasks.revalidate_nextjs', queue="revalidation", autoretry_for=(requests.RequestException, StorefrontUnavailable),
             max_retries=6, retry_backoff=60, retry_jitter=True)
def revalidate_nextjs(domain, token, payload):
    """
    Asks the storefront of the domain to render again the pages with the payload's tags, see shop/revalidation.py.
    It is retried while the storefront can't be reached or fails, as during its deploy.
    """
    url = 'https://{}/api/revalidate'.format(domain)
    response = requests.post(url, json={'secret': token, **payload}, timeout=30)
    if response.status_code >= 500:
        raise StorefrontUnavailable('{} answered {}'.format(url, response.status_code))
    try:
        result = response.json()
    except ValueError:
        result = {'status': response.status_code, 'text': response.text[:200]}
    if not response.ok:
        log.error('Revalidation by %s failed: %s', url, result)
    return result


@shared_task(name='shop.tasks.post_update_product', queue="revalidation")
def post_update_product(product_id, origin):
    """ Saved in the admin: the search vector. The admin revalidates the product's pages itself, see save_model() """
    if origin == 'admin':
        Product.objects.get(pk=product_id).update_fts_vector()


@shared_task(name='shop.tasks.post_update_products', queue="priority")
def post_update_products(product_ids):
    """ Products whose prices an import changed: their pages and lists show the new prices at once """
    revalidate_products(product_ids)
    return len(product_ids)


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
