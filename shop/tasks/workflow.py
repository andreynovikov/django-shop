import json
import logging

import requests

from datetime import timedelta
from importlib import import_module

from django.contrib.admin.models import LogEntry, CHANGE
from django.conf import settings
from django.core.mail import mail_admins
from django.db import Error as DatabaseError, transaction
from django.db.models.fields.json import JSONField
from django.db.models.fields.related import RelatedField
from django.db.models.fields.reverse_related import ForeignObjectRel
from django.utils import timezone

from celery import shared_task
from celery.exceptions import Retry

from sewingworld.notifications import notify_user
from shop import order_lock
from shop.models import ShopUser, Product, Basket, Order
from shop.revalidation import revalidate_products


log = logging.getLogger('shop')


@shared_task(name='shop.tasks.update_order', bind=True, queue="priority", autoretry_for=(DatabaseError,), max_retries=12, retry_backoff=300, retry_jitter=False)
def update_order(self, order_id, data, append=None):
    """
    Sets order fields from data, {field: value}, for integrations and other tasks, and adds the lines of append,
    {field: text}, to text fields as they are when it saves. The pk and relations are skipped, a JSON field takes the
    keys given over those it has. It records the change in the order's admin history under the system user.

    While a staff member's page holds the lock on the order (shop/order_lock.py) it waits, retrying every 10 minutes,
    and the last attempt takes the lock: the page learns at once that it can't save. When it fails for good, the
    admins get the data by mail.
    """
    try:
        return save_order_update(self, order_id, data, append or {})
    except Retry:
        raise
    except Exception as e:
        if not isinstance(e, DatabaseError) or self.request.retries >= self.max_retries:
            mail_admins(
                f'Order update failed: {order_id}',
                f'Order: {order_id}\n'
                f'Attempt: {self.request.retries + 1}\n'
                f'Error: {e!r}\n\n'
                f'Data:\n{json.dumps(data, ensure_ascii=False, indent=2, default=str)}\n\n'
                f'Append:\n{json.dumps(append, ensure_ascii=False, indent=2, default=str)}\n',
                fail_silently=True)
        raise


def describe_change(field, value, appended=False):
    """ A change of the field for the order's history: its name and the value, a choice's label, the keys of JSON """
    if appended:
        return f'{field.verbose_name}: +{value}'
    if isinstance(field, JSONField) and isinstance(value, dict):
        return f'{field.verbose_name}: {", ".join(map(str, value))}'
    if field.choices:
        value = dict(field.flatchoices).get(value, value)
    return f'{field.verbose_name}: {value}'


def save_order_update(task, order_id, data, append):
    with transaction.atomic():
        order = order_lock.locked_order(order_id)
        if order is None:
            raise Order.DoesNotExist(f'Order {order_id} does not exist')
        holder = order.lock_holder
        if holder is not None and task.request.retries < task.max_retries - 1:
            log.info('Locked by %s, retrying', holder)
            raise task.retry(countdown=600)  # 10 minutes
        changed = {}
        changes = []
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
                changes.append(describe_change(field, data[attr]))
        for attr, text in append.items():
            if not text:
                continue
            field = order._meta.get_field(attr)
            order_value = getattr(order, attr)
            setattr(order, attr, '\n'.join(filter(None, [order_value, text])))
            changed[attr] = getattr(order, attr)
            changes.append(describe_change(field, text, appended=True))
        if not changed:
            return 'unchanged'
        # Whoever's page holds the lock, even one whose lease has ended, has the order as it was and can't save it
        if order.owner_id is not None or order.lock_token is not None:
            if holder is not None:
                log.warning('Locked by %s, force unlocking', holder)
                changes.append(f'блокировка {holder} снята')
            message = f'Заказ изменён автоматически ({"; ".join(changes)}).'
            order_lock.tell_lost(order, message)
            if order.owner_id is not None and order.owner.is_staff:
                # the workers don't route the admin's URLs (settings.IS_ADMIN_SITE)
                notify_user(order.owner_id, f'Заказ {order.pk}: {message}', 'warning', f'/admin/shop/order/{order.pk}/change/')
            for attr, value in order_lock.UNLOCKED.items():
                setattr(order, attr, value)
            changed.update(order_lock.UNLOCKED)
        try:
            order.save(update_fields=changed.keys())
        except Exception as e:
            e.add_note("Failed to save info {}".format(str(data)))
            raise
        change_message = '; '.join(changes)
        LogEntry.objects.log_actions(
            user_id=ShopUser.objects.system_user().pk,
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
    """ Deletes baskets older than a session lives, whose sessions have expired, and the expired sessions """
    threshold = timezone.now() - timedelta(seconds=settings.SESSION_COOKIE_AGE)
    baskets = Basket.objects.filter(created__lt=threshold)
    num = len(baskets)
    for basket in baskets.all():
        basket.delete()
    log.info('Deleted %d baskets' % num)
    SessionStore = import_module(settings.SESSION_ENGINE).SessionStore
    SessionStore.clear_expired()
    log.info('Cleared expired sessions')
