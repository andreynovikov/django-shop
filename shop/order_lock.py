"""
The admin's lock on an order, which keeps staff from editing an order at the same time.

The page of the order (a browser tab) that holds the lock is known by a token it gets when the admin opens it. The
page renews its lease while it is open (HEARTBEAT, see staticfiles/js/order-lock.js) and gives the lock up when it is
left or after a while without input. A page that is closed without leaving, as when the browser crashes, stops
renewing, and its lease ends after config.sw_order_lock_lease seconds. Then anyone may take the lock.

A save checks the token, so a page that has lost its lock can't save, whatever it shows. When the lease has ended
but nobody has taken the lock or written the order, as when the computer slept, the page goes on as before.

Whoever takes the lock from a page, or writes the order without it (update_order() in shop/tasks/workflow.py),
replaces or clears the token, and the page hears of it at once through a 'lock-lost' notice
(sewingworld/notifications.py), or from its next renewal.
"""
import uuid
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from constance import config

from sewingworld.notifications import notify_order
from shop.models import Order

HEARTBEAT = 30  # seconds between the renewals of a page
IDLE_WARNING = 120  # seconds before an idle page gives the lock up, when it warns

# The fields that hold a lock, as the admin's save leaves them alone
LOCK_FIELDS = ('owner', 'lock_token', 'locked_until')
UNLOCKED = dict.fromkeys(LOCK_FIELDS)

TOKEN_FIELD = '_lock_token'  # the order form's field with the page's token


def new_token():
    return uuid.uuid4()


def parse_token(value):
    """ The token a page sent, or None when it is not one """
    try:
        return uuid.UUID(str(value))
    except (TypeError, ValueError):
        return None


def lease_end():
    return timezone.now() + timedelta(seconds=config.sw_order_lock_lease)


def page_config():
    """ What the page needs to keep its lock, in seconds """
    return {'heartbeat': HEARTBEAT, 'idle': config.sw_order_lock_idle, 'idle_warning': IDLE_WARNING}


def locked_order(order_id):
    """ The order with its row locked till the end of the transaction, or None """
    return Order.objects.select_for_update(of=('self',)).select_related('owner').filter(pk=order_id).first()


def holds(order, user, token):
    token = parse_token(token)
    return token is not None and order.owner_id == user.pk and order.lock_token == token


def lost_message(order, user):
    """ Why the user's page no longer holds the lock on the order """
    holder = order.lock_holder
    if holder is not None and holder.pk == user.pk:
        return 'Заказ открыт в другой вкладке, сохранить его можно только там.'
    if holder is not None:
        return f'Заказ редактирует {holder}.'
    return 'Блокировка заказа снята.'


def tell_lost(order, message):
    """ Tells the page that holds the lock on the order that it has lost it, once the transaction commits """
    if order.lock_token is not None:
        notify_order(order.pk, 'lock-lost', token=str(order.lock_token), message=message)


def acquire(order_id, user, token):
    """
    Gives the lock to the user's page with the token unless another staff member's lease holds it. The user's own
    page in another tab loses it. Returns whether the page got it.
    """
    with transaction.atomic():
        order = locked_order(order_id)
        if order is None:
            return False
        holder = order.lock_holder
        if holder is not None and holder.pk != user.pk:
            return False
        if order.lock_token is not None and order.lock_token != token:
            if order.owner_id == user.pk:
                tell_lost(order, 'Заказ открыт в другой вкладке, сохранить его можно только там.')
            else:
                tell_lost(order, f'Блокировка заказа истекла, пока страница была без связи, заказ редактирует {user}.')
        Order.objects.filter(pk=order.pk).update(owner=user, lock_token=token, locked_until=lease_end())
        return True


def renew(order_id, user, token):
    """ The page's heartbeat: extends its lease while it holds the lock. Returns {'held': ..., 'message': ...}. """
    with transaction.atomic():
        order = locked_order(order_id)
        if order is None:
            return {'held': False, 'message': 'Заказ удалён.'}
        if holds(order, user, token):
            Order.objects.filter(pk=order.pk).update(locked_until=lease_end())
            return {'held': True}
        return {'held': False, 'message': lost_message(order, user)}


def release(order_id, token):
    """ Releases the lock if the page with the token holds it, which a page that has lost the lock doesn't """
    token = parse_token(token)
    if token is not None:
        Order.objects.filter(pk=order_id, lock_token=token).update(**UNLOCKED)


def force_release(order_id, user):
    """ The user releases the lock whoever holds it, and the page that held it learns who did """
    with transaction.atomic():
        order = locked_order(order_id)
        if order is None:
            return
        tell_lost(order, f'Блокировка заказа снята пользователем {user}. Изменения на этой странице уже не сохранить.')
        Order.objects.filter(pk=order.pk).update(**UNLOCKED)


def save_error(order_id, user, token):
    """
    Why the user's page can't save the order, or None when it holds the lock. Call it in the transaction of the save:
    the order's row stays locked until it ends, so that nobody takes the lock in the meantime.
    """
    order = locked_order(order_id)
    if order is None or holds(order, user, token):
        return None
    return f'{lost_message(order, user)} Изменения не сохранены: скопируйте нужное и обновите страницу.'
