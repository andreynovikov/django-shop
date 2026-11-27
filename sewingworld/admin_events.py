"""
The admin's instant notices (sewingworld/notifications.py) streamed to an admin page as server-sent events, see
staticfiles/js/admin-events.js.

An open page keeps its connection, which would hold one of the few uWSGI workers of the admin. So nginx passes
/admin/events/ to a process of its own that runs Django under ASGI (sewingworld/asgi.py, server_asgi_apps in
deploy/ansible). Under WSGI the view answers 204, which tells EventSource to stop, and the pages rely on what they
poll, such as the heartbeat of the order lock.

The ID of each event holds the positions in the page's streams, which EventSource sends back as Last-Event-ID when
it reconnects, so the page gets what it missed. The stream ends every DURATION seconds, and the reconnection checks
the user again.
"""
import logging
import re
import time

import redis
import redis.asyncio

from asgiref.sync import sync_to_async
from django.contrib import admin
from django.core.handlers.asgi import ASGIRequest
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden, StreamingHttpResponse

from . import notifications

log = logging.getLogger(__name__)

BLOCK = 15000  # milliseconds a read waits for an entry, after which the stream sends a comment to keep the connection
DURATION = 600  # seconds
RETRY = 3000  # milliseconds EventSource waits before reconnecting
ENTRY_ID = re.compile(r'^\d+-\d+$')

_client = None


def client():
    global _client
    if _client is None:
        _client = redis.asyncio.Redis.from_url(notifications.redis_url(), decode_responses=True)
    return _client


def permitted_user(request, order_id):
    """ The ID of the staff member who may have the notices, of the order when given, or None """
    if not admin.site.has_permission(request):
        return None
    if order_id is not None:
        from shop.models import Order  # the admin's apps are loaded by now
        order_admin = admin.site._registry.get(Order)
        if order_admin is None or not order_admin.has_view_permission(request):
            return None
        if not order_admin.get_queryset(request).filter(pk=order_id).exists():
            return None
    return request.user.pk


def positions(last_event_id, count):
    """ Where each stream continues: from Last-Event-ID, or None for its end """
    ids = (last_event_id or '').split()
    if len(ids) == count and all(ENTRY_ID.match(entry_id) for entry_id in ids):
        return ids
    return [None] * count


async def stream(streams, ids, duration=DURATION):
    """ The events of the streams after the IDs, as text/event-stream """
    connection = client()
    deadline = time.monotonic() + duration
    yield f'retry: {RETRY}\n\n'
    try:
        for index, key in enumerate(streams):
            if ids[index] is None:
                last = await connection.xrevrange(key, count=1)
                ids[index] = last[0][0] if last else '0-0'
        while time.monotonic() < deadline:
            result = await connection.xread(dict(zip(streams, ids)), block=BLOCK, count=100)
            if not result:
                yield ': ping\n\n'
                continue
            for key, entries in result:
                index = streams.index(key)
                for entry_id, fields in entries:
                    ids[index] = entry_id
                    yield f"id: {' '.join(ids)}\ndata: {fields.get('data', '{}')}\n\n"
    except redis.RedisError as e:
        log.warning('Admin events stopped: %s', e)  # EventSource reconnects


async def events(request):
    if not isinstance(request, ASGIRequest) or notifications.redis_url() is None:
        return HttpResponse(status=204)
    order_id = request.GET.get('order')
    if order_id is not None:
        if not (order_id.isascii() and order_id.isdigit()):
            return HttpResponseBadRequest()
        order_id = int(order_id)
    user_id = await sync_to_async(permitted_user)(request, order_id)
    if user_id is None:
        return HttpResponseForbidden()
    streams = [notifications.user_stream(user_id)]
    if order_id is not None:
        streams.append(notifications.order_stream(order_id))
    response = StreamingHttpResponse(stream(streams, positions(request.headers.get('Last-Event-ID'), len(streams))),
                                     content_type='text/event-stream')
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'
    return response
