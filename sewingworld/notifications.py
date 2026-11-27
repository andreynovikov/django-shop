"""
Instant notices to the admin pages open in browsers, see sewingworld/admin_events.py for how they get there.

Each notice is an entry of a Redis stream: one stream per staff member, which every admin page of theirs reads, one
per order, which the order's page reads, and one of the top bar's indicators (STATUS_STREAM), which the pages of those
who may see them read. A page that reconnects gets what it missed from the stream. A stream
keeps its latest entries and expires a day after the last one.

Notices are a convenience: they are lost when Redis is down, and nothing may depend on them. The order lock, for one,
also tells a page that it has lost the lock in answer to the page's heartbeat (shop/order_lock.py).
"""
import json
import logging

import redis

from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.db import transaction

log = logging.getLogger(__name__)

STREAM_PREFIX = 'sw:admin:'
STREAM_LENGTH = 200
STREAM_EXPIRY = 86400  # seconds

LEVELS = ('info', 'success', 'warning', 'error')  # the classes of Django's admin messages

_client = None


def redis_url():
    """ The URL of the Redis that keeps the streams, or None when notices are off """
    url = getattr(settings, 'ADMIN_EVENTS_REDIS_URL', '')
    if url and url.startswith(('redis://', 'rediss://', 'unix://')):
        return url
    return None


def client():
    global _client
    url = redis_url()
    if url is None:
        return None
    if _client is None:
        _client = redis.Redis.from_url(url, socket_timeout=2, socket_connect_timeout=2)
    return _client


def user_stream(user_id):
    return f'{STREAM_PREFIX}user:{user_id}'


def order_stream(order_id):
    return f'{STREAM_PREFIX}order:{order_id}'


STATUS_STREAM = f'{STREAM_PREFIX}status'
# Who may see the indicators of the status stream: the 1C import's and the health's
STATUS_PERMISSIONS = ('shop.view_product', 'shop.view_healthcheck')


def publish(stream, data):
    """ Adds the data, a dict with its 'type', to the stream at once. Returns the entry's ID, None when it failed. """
    connection = client()
    if connection is None:
        return None
    try:
        pipeline = connection.pipeline()
        pipeline.xadd(stream, {'data': json.dumps(data, ensure_ascii=False, cls=DjangoJSONEncoder)},
                      maxlen=STREAM_LENGTH, approximate=True)
        pipeline.expire(stream, STREAM_EXPIRY)
        entry_id, _ = pipeline.execute()
        return entry_id
    except redis.RedisError as e:
        log.warning('Admin notice to %s not sent: %s', stream, e)
        return None


def publish_on_commit(stream, data):
    """ Publishes once the transaction commits, so that a page never hears of a change that was rolled back """
    transaction.on_commit(lambda: publish(stream, data))


def notify_user(user_id, message, level='info', link=None):
    """ A notice that every admin page of the staff member shows, with a link to follow when given """
    if level not in LEVELS:
        raise ValueError(f'Unknown level {level}')
    publish_on_commit(user_stream(user_id), {'type': 'notice', 'level': level, 'message': message, 'link': link})


def notify_order(order_id, event_type, **data):
    """ An event for the pages of the order, such as 'lock-lost', see shop/order_lock.py """
    publish_on_commit(order_stream(order_id), {'type': event_type, **data})


def publish_status(event_type, **data):
    """
    A change of an indicator of the top bar at once, such as {type: 'import'} (shop/tasks/stocks.py) or
    {type: 'health'} (shop/health.py), see staticfiles/js/admin-indicators.js
    """
    publish(STATUS_STREAM, {'type': event_type, **data})
