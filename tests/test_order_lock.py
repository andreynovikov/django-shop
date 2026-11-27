"""
The admin's lock on orders (shop/order_lock.py) and update_order(), which waits for it. See settings.py on how to run.
"""
import io
import json
import uuid
from datetime import timedelta
from types import SimpleNamespace
from unittest import mock
from urllib.error import HTTPError

from celery.exceptions import Retry

from django.contrib.admin.models import LogEntry
from django.contrib.sites.models import Site
from django.core import mail
from django.db import DatabaseError, connection
from django.test import RequestFactory, TestCase
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from shop import order_lock
from shop.models import Contractor, Courier, Order, PosTerminal, ShopUser
from shop.tasks.integrations import delete_modulpos_order
from shop.tasks.workflow import save_order_update, update_order
from yandex_kassa.views import callback


class FakeTask:
    """ What save_order_update() uses of the task, at the given attempt """
    max_retries = 12

    def __init__(self, retries=0):
        self.request = SimpleNamespace(retries=retries)

    def retry(self, countdown):
        return Retry()


class Base(TestCase):
    def setUp(self):
        for target, new in (
            ('shop.order_lock.config', SimpleNamespace(sw_order_lock_lease=180, sw_order_lock_idle=1800)),
            ('shop.signals.logger', mock.Mock()),
        ):
            patcher = mock.patch(target, new=new)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.publish = mock.patch('sewingworld.notifications.publish').start()
        self.addCleanup(mock.patch.stopall)
        self.system = ShopUser.objects.create(phone='000')
        self.anna = ShopUser.objects.create(phone='+79990000001', name='Анна', is_staff=True)
        self.boris = ShopUser.objects.create(phone='+79990000002', name='Борис', is_staff=True)
        buyer = ShopUser.objects.create(phone='+79161234567')
        self.order = Order.objects.create(user=buyer, site=Site.objects.get_current(), manager_comment='Позвонить')
        self.token = uuid.uuid4()

    def lock(self, user=None, token=None, expired=False):
        """ The user's page holds the lock on the order """
        until = timezone.now() + timedelta(seconds=-1 if expired else 180)
        Order.objects.filter(pk=self.order.pk).update(owner=user or self.anna, lock_token=token or self.token, locked_until=until)
        self.order.refresh_from_db()

    def published(self):
        """ The notices sent, (stream, data) each """
        return [call.args for call in self.publish.call_args_list]


class LockTests(Base):
    def test_free_order(self):
        with self.captureOnCommitCallbacks(execute=True):
            self.assertTrue(order_lock.acquire(self.order.pk, self.anna, self.token))
        self.order.refresh_from_db()
        self.assertEqual((self.order.lock_holder, self.order.lock_token), (self.anna, self.token))
        self.assertEqual(self.published(), [])

    def test_lock_of_another_staff_member(self):
        self.lock()
        self.assertFalse(order_lock.acquire(self.order.pk, self.boris, uuid.uuid4()))
        self.order.refresh_from_db()
        self.assertEqual((self.order.owner, self.order.lock_token), (self.anna, self.token))

    def test_ended_lease(self):
        self.lock(expired=True)
        with self.captureOnCommitCallbacks(execute=True):
            self.assertTrue(order_lock.acquire(self.order.pk, self.boris, uuid.uuid4()))
        [(stream, data)] = self.published()
        self.assertEqual(stream, f'sw:admin:order:{self.order.pk}')
        self.assertEqual((data['type'], data['token']), ('lock-lost', str(self.token)))
        self.assertIn('Борис', data['message'])

    def test_same_user_in_another_tab(self):
        self.lock()
        with self.captureOnCommitCallbacks(execute=True):
            self.assertTrue(order_lock.acquire(self.order.pk, self.anna, uuid.uuid4()))
        [(_, data)] = self.published()
        self.assertEqual(data['token'], str(self.token))
        self.assertIn('другой вкладке', data['message'])

    def test_renewal(self):
        self.lock(expired=True)  # a computer that slept, while nobody took the lock
        self.assertEqual(order_lock.renew(self.order.pk, self.anna, str(self.token)), {'held': True})
        self.order.refresh_from_db()
        self.assertEqual(self.order.lock_holder, self.anna)
        self.assertFalse(order_lock.renew(self.order.pk, self.anna, str(uuid.uuid4()))['held'])
        self.assertEqual(order_lock.renew(self.order.pk, self.boris, str(self.token)),
                         {'held': False, 'message': 'Заказ редактирует Анна.'})
        self.assertFalse(order_lock.renew(self.order.pk, self.anna, 'not a token')['held'])

    def test_release_needs_the_token(self):
        self.lock()
        order_lock.release(self.order.pk, str(uuid.uuid4()))
        order_lock.release(self.order.pk, 'not a token')
        self.order.refresh_from_db()
        self.assertEqual(self.order.owner, self.anna)
        order_lock.release(self.order.pk, str(self.token))
        self.order.refresh_from_db()
        self.assertEqual((self.order.owner, self.order.lock_token, self.order.locked_until), (None, None, None))

    def test_forced_release(self):
        self.lock()
        with self.captureOnCommitCallbacks(execute=True):
            order_lock.force_release(self.order.pk, self.boris)
        self.order.refresh_from_db()
        self.assertIsNone(self.order.owner)
        [(_, data)] = self.published()
        self.assertEqual(data['message'], 'Блокировка заказа снята пользователем Борис. Изменения на этой странице уже не сохранить.')

    def test_save_error(self):
        self.lock(expired=True)
        self.assertIsNone(order_lock.save_error(self.order.pk, self.anna, self.token))
        self.assertIn('Блокировка заказа снята', order_lock.save_error(self.order.pk, self.anna, uuid.uuid4()))
        self.lock()
        self.assertIn('Заказ редактирует Анна', order_lock.save_error(self.order.pk, self.boris, self.token))


class UpdateOrderTests(Base):
    def update(self, data, append=None, retries=0):
        with self.captureOnCommitCallbacks(execute=True):
            return save_order_update(FakeTask(retries), self.order.pk, data, append or {})

    def test_waits_while_the_lock_holds(self):
        self.lock()
        with self.assertRaises(Retry):
            self.update({'alert': 'Отменён'})
        self.order.refresh_from_db()
        self.assertEqual((self.order.alert, self.order.owner), ('', self.anna))
        self.assertEqual(self.published(), [])

    def test_last_attempt_takes_the_lock(self):
        self.lock()
        with self.assertLogs('shop', 'WARNING'):
            message = self.update({'status': Order.STATUS_PROBLEM}, {'manager_comment': 'Ошибка кассы'}, retries=11)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.STATUS_PROBLEM)
        self.assertEqual(self.order.manager_comment, 'Позвонить\nОшибка кассы')
        self.assertEqual((self.order.owner, self.order.lock_token, self.order.locked_until), (None, None, None))
        self.assertEqual(message, 'статус: проблема; комментарий менеджера: +Ошибка кассы; блокировка Анна снята')
        (order_stream, lost), (user_stream, notice) = self.published()
        self.assertEqual((order_stream, lost['type'], lost['token']), (f'sw:admin:order:{self.order.pk}', 'lock-lost', str(self.token)))
        self.assertEqual((user_stream, notice['type'], notice['level']), (f'sw:admin:user:{self.anna.pk}', 'notice', 'warning'))
        self.assertIn('Заказ изменён автоматически', lost['message'])
        self.assertEqual(notice['link'], f'/admin/shop/order/{self.order.pk}/change/')
        entry = LogEntry.objects.get()
        self.assertEqual((entry.user, entry.change_message), (self.system, message))

    def test_ended_lease_gives_way_at_once(self):
        self.lock(expired=True)
        self.update({'alert': 'Отменён'})
        self.order.refresh_from_db()
        self.assertEqual((self.order.alert, self.order.lock_token), ('Отменён', None))
        self.assertEqual([data['type'] for _, data in self.published()], ['lock-lost', 'notice'])

    def test_writes_only_its_fields(self):
        Order.objects.filter(pk=self.order.pk).update(name='Иван')  # since the page or task read it
        with CaptureQueriesContext(connection) as queries:
            self.update({'name': 'Пётр', 'alert': 'Отменён'}, {'delivery_info': 'Трек 1'})
        [update] = [query['sql'] for query in queries if query['sql'].startswith('UPDATE "shop_order"')]
        self.assertNotIn('"manager_comment"', update)
        self.order.refresh_from_db()
        self.assertEqual((self.order.name, self.order.alert, self.order.delivery_info), ('Пётр', 'Отменён', 'Трек 1'))

    def test_append_to_what_the_order_has_when_saved(self):
        Order.objects.filter(pk=self.order.pk).update(manager_comment='Позвонить\nПеренести доставку')
        self.update({}, {'manager_comment': 'Ошибка кассы'})
        self.order.refresh_from_db()
        self.assertEqual(self.order.manager_comment, 'Позвонить\nПеренести доставку\nОшибка кассы')
        self.update({}, {'alert': 'Отменён'})
        self.order.refresh_from_db()
        self.assertEqual(self.order.alert, 'Отменён')

    def test_nothing_to_change(self):
        self.lock()
        self.assertEqual(self.update({'manager_comment': 'Позвонить'}, retries=11), 'unchanged')
        self.order.refresh_from_db()
        self.assertEqual(self.order.owner, self.anna)  # the page goes on, nothing changed under it
        self.assertFalse(LogEntry.objects.exists())

    def test_failed_save_leaves_the_order_as_it_was(self):
        self.lock()
        with self.assertRaises(ValueError), self.assertLogs('shop', 'WARNING'):
            self.update({'alert': 'Отменён', 'status': 'not a number'}, retries=11)
        self.order.refresh_from_db()
        self.assertEqual((self.order.alert, self.order.owner, self.order.lock_token), ('', self.anna, self.token))
        self.assertEqual(self.published(), [])

    def run_task(self, retries, error):
        update_order.push_request(retries=retries)
        try:
            with mock.patch('shop.tasks.workflow.save_order_update', side_effect=error):
                update_order.run(self.order.pk, {'alert': 'Отменён'}, append={'manager_comment': 'Ошибка'})
        finally:
            update_order.pop_request()

    def test_mail_when_it_fails_for_good(self):
        with self.assertRaises(DatabaseError):
            self.run_task(12, DatabaseError('lock timeout'))
        [message] = mail.outbox
        self.assertIn(f'Order update failed: {self.order.pk}', message.subject)
        self.assertIn('"alert": "Отменён"', message.body)
        self.assertIn('"manager_comment": "Ошибка"', message.body)
        self.assertIn('lock timeout', message.body)

    def test_no_mail_while_it_retries(self):
        with self.assertRaises(DatabaseError):  # a task called directly raises instead of retrying
            self.run_task(3, DatabaseError('lock timeout'))
        self.assertEqual(mail.outbox, [])

    def test_mail_when_the_order_is_gone(self):
        Order.objects.filter(pk=self.order.pk).delete()
        result = update_order.apply(args=(self.order.pk, {'alert': 'Отменён'}))
        self.assertIsInstance(result.result, Order.DoesNotExist)
        self.assertEqual(len(mail.outbox), 1)


class CallerTests(Base):
    """ What other tasks and views give update_order(), and the history they write """

    def test_modulpos_error_is_added_to_the_comment_when_saved(self):
        seller = Contractor.objects.create(code='s', name='Продавец', modulkassa_login='l', modulkassa_password='p')
        courier = Courier.objects.create(name='Курьер', pos_terminal=PosTerminal.objects.create(id='t1', seller=seller))
        Order.objects.filter(pk=self.order.pk).update(courier=courier, hidden_tracking_number='doc1')
        error = HTTPError('https://service.modulpos.ru', 400, 'Bad Request', {},
                          io.BytesIO(json.dumps({'message': 'Нет документа'}).encode()))
        with mock.patch('shop.tasks.integrations.urlopen', side_effect=error), \
                mock.patch('shop.tasks.integrations.update_order') as update, self.assertRaises(HTTPError):
            delete_modulpos_order.run(self.order.pk)  # called directly, the retry raises
        update.delay.assert_called_once_with(self.order.pk, {'status': Order.STATUS_PROBLEM},
                                             append={'manager_comment': 'Нет документа'})

    def test_payment_notice_is_under_the_system_user(self):
        metadata = {'order_id': str(self.order.pk), 'user_id': str(self.order.user_id)}
        payment = SimpleNamespace(id='p1', paid=True, status='succeeded', metadata=metadata, cancellation_details=None)
        notification = SimpleNamespace(event='payment.succeeded', object=SimpleNamespace(id='p1', metadata=metadata))
        with mock.patch('yandex_kassa.views.WebhookNotification', return_value=notification), \
                mock.patch('yandex_kassa.views.Payment') as payments, mock.patch('yandex_kassa.views.configure_yookassa'), \
                mock.patch('yandex_kassa.views.update_order'), mock.patch('yandex_kassa.views.get_receipt'):
            payments.find_one.return_value = payment
            response = callback(RequestFactory().post('/kassa/callback/', '{"event": "payment.succeeded"}',
                                                      content_type='application/json'))
        self.assertEqual(response.status_code, 200)
        entry = LogEntry.objects.get()
        self.assertEqual((entry.user, entry.change_message), (self.system, 'Получено уведомление об оплате'))
