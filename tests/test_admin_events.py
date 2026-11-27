"""
The admin's instant notices: publishing them (sewingworld/notifications.py) and streaming them to admin pages
(sewingworld/admin_events.py). Redis is replaced by fakes. See settings.py on how to run.
"""
import asyncio
import json
from unittest import mock

import redis

from asgiref.sync import sync_to_async
from django.contrib.auth.models import AnonymousUser, Permission
from django.contrib.sites.models import Site
from django.test import AsyncRequestFactory, RequestFactory, SimpleTestCase, TestCase, override_settings

from sewingworld import notifications
from sewingworld.admin_events import events, positions, stream
from shop.models import Order, ShopUser

REDIS = 'redis://localhost:6379/9'


class FakeRedis:
    """ Streams with the entries that reads return one batch at a time, then nothing """
    def __init__(self, batches, last=None, error=None):
        self.batches = list(batches)
        self.last = last or {}
        self.error = error
        self.reads = []

    async def xrevrange(self, key, count):
        return [(self.last[key], {})] if key in self.last else []

    async def xread(self, streams, block, count):
        if self.error is not None:
            raise self.error
        self.reads.append(dict(streams))
        if self.batches:
            return [self.batches.pop(0)]
        await asyncio.sleep(0.01)
        return []


class PublishTests(SimpleTestCase):
    def test_off_without_redis(self):
        self.assertIsNone(notifications.publish('sw:admin:user:1', {'type': 'notice'}))

    @override_settings(ADMIN_EVENTS_REDIS_URL=REDIS)
    def test_entry_expires(self):
        client = mock.Mock()
        pipeline = client.pipeline.return_value
        pipeline.execute.return_value = ['1-0', True]
        with mock.patch('sewingworld.notifications.client', return_value=client):
            self.assertEqual(notifications.publish('sw:admin:user:1', {'type': 'notice', 'message': 'Привет'}), '1-0')
        pipeline.xadd.assert_called_once_with(
            'sw:admin:user:1', {'data': '{"type": "notice", "message": "Привет"}'}, maxlen=200, approximate=True)
        pipeline.expire.assert_called_once_with('sw:admin:user:1', 86400)

    @override_settings(ADMIN_EVENTS_REDIS_URL=REDIS)
    def test_redis_errors_do_not_break_the_caller(self):
        client = mock.Mock()
        client.pipeline.return_value.execute.side_effect = redis.ConnectionError('refused')
        with mock.patch('sewingworld.notifications.client', return_value=client), \
                self.assertLogs('sewingworld.notifications', 'WARNING'):
            self.assertIsNone(notifications.publish('sw:admin:user:1', {'type': 'notice'}))

    def test_levels_of_notices(self):
        with self.assertRaises(ValueError):
            notifications.notify_user(1, 'Привет', level='debug')


class StreamTests(SimpleTestCase):
    async def collect(self, fake, streams, ids, duration=0.05):
        with mock.patch('sewingworld.admin_events.client', return_value=fake):
            return [chunk async for chunk in stream(streams, ids, duration=duration)]

    async def test_events_carry_the_positions_of_all_streams(self):
        streams = ['sw:admin:user:1', 'sw:admin:order:5']
        fake = FakeRedis([
            ('sw:admin:user:1', [('7-0', {'data': '{"type": "notice"}'})]),
            ('sw:admin:order:5', [('8-1', {'data': '{"type": "lock-lost"}'})]),
        ], last={'sw:admin:user:1': '5-0'})
        chunks = await self.collect(fake, streams, [None, None])
        self.assertEqual(chunks[:3], [
            'retry: 3000\n\n',
            'id: 7-0 0-0\ndata: {"type": "notice"}\n\n',
            'id: 7-0 8-1\ndata: {"type": "lock-lost"}\n\n',
        ])
        self.assertEqual(fake.reads[0], {'sw:admin:user:1': '5-0', 'sw:admin:order:5': '0-0'})  # only what is new
        self.assertIn(': ping\n\n', chunks[3:])

    async def test_reconnection_continues_where_the_page_was(self):
        fake = FakeRedis([])
        await self.collect(fake, ['sw:admin:user:1'], positions('6-2', 1), duration=0.02)
        self.assertEqual(fake.reads[0], {'sw:admin:user:1': '6-2'})

    def test_last_event_id(self):
        self.assertEqual(positions('7-0 8-1', 2), ['7-0', '8-1'])
        self.assertEqual(positions('7-0', 2), [None, None])
        self.assertEqual(positions('7-0 drop', 2), [None, None])
        self.assertEqual(positions(None, 1), [None])

    async def test_redis_error_ends_the_stream(self):
        fake = FakeRedis([], error=redis.ConnectionError('refused'))
        with self.assertLogs('sewingworld.admin_events', 'WARNING'):
            chunks = await self.collect(fake, ['sw:admin:user:1'], [None])
        self.assertEqual(chunks, ['retry: 3000\n\n'])


@override_settings(ADMIN_EVENTS_REDIS_URL=REDIS)
class ViewTests(TestCase):
    def setUp(self):
        self.staff = ShopUser.objects.create(phone='+79990000000', is_staff=True, is_superuser=True)
        self.order = Order.objects.create(user=ShopUser.objects.create(phone='+79161234567'), site=Site.objects.get_current())

    def staff_with(self, *permissions):
        user = ShopUser.objects.create(phone='+7999000%04d' % ShopUser.objects.count(), is_staff=True)
        user.user_permissions.set(Permission.objects.filter(content_type__app_label='shop', codename__in=permissions))
        return ShopUser.objects.get(pk=user.pk)

    def request(self, user, query=None, headers=None):
        request = AsyncRequestFactory().get('/admin/events/', query or {}, headers=headers or {})
        request.user = user
        user.is_verified = lambda: True  # passed the second factor, as OTPMiddleware tells the admin site
        return request

    async def test_no_stream_under_wsgi(self):
        request = RequestFactory().get('/admin/events/')
        request.user = self.staff
        self.assertEqual((await events(request)).status_code, 204)
        with override_settings(ADMIN_EVENTS_REDIS_URL=''):
            self.assertEqual((await events(self.request(self.staff))).status_code, 204)

    async def test_who_may_listen(self):
        viewer = await sync_to_async(self.staff_with)('view_order')
        nobody = await sync_to_async(self.staff_with)()
        customer = await ShopUser.objects.acreate(phone='+79160000000')
        for user, query, status in (
            (AnonymousUser(), {}, 403),
            (customer, {}, 403),
            (nobody, {'order': self.order.pk}, 403),
            (self.staff, {'order': 'all'}, 400),
            (self.staff, {'order': self.order.pk + 1}, 403),
            (viewer, {'order': self.order.pk}, 200),
            (self.staff, {}, 200),
        ):
            with self.subTest(user=str(user), query=query), mock.patch('sewingworld.admin_events.stream'):
                self.assertEqual((await events(self.request(user, query))).status_code, status)

    async def test_streams_of_the_page(self):
        with mock.patch('sewingworld.admin_events.stream') as fake:
            response = await events(self.request(self.staff, {'order': self.order.pk},
                                                 headers={'Last-Event-ID': '7-0 8-1'}))
        self.assertEqual(response['Content-Type'], 'text/event-stream')
        self.assertEqual((response['Cache-Control'], response['X-Accel-Buffering']), ('no-cache', 'no'))
        fake.assert_called_once_with([f'sw:admin:user:{self.staff.pk}', f'sw:admin:order:{self.order.pk}'], ['7-0', '8-1'])


class NoticeTests(TestCase):
    """ Notices go out once the transaction commits """

    def test_on_commit(self):
        with mock.patch('sewingworld.notifications.publish') as publish:
            with self.captureOnCommitCallbacks() as callbacks:
                notifications.notify_user(3, 'Заказ изменён', 'warning', '/admin/shop/order/1/change/')
                notifications.notify_order(1, 'lock-lost', token='t', message='Снята')
            publish.assert_not_called()
            for callback in callbacks:
                callback()
        self.assertEqual([call.args for call in publish.call_args_list], [
            ('sw:admin:user:3', {'type': 'notice', 'level': 'warning', 'message': 'Заказ изменён',
                                 'link': '/admin/shop/order/1/change/'}),
            ('sw:admin:order:1', {'type': 'lock-lost', 'token': 't', 'message': 'Снята'}),
        ])
        json.dumps(publish.call_args_list[0].args[1])  # what the stream carries is JSON
