"""
Posts to the staff channel in Telegram: the client, the new-order notice and the 1C import's notices. Nothing reaches
Telegram, requests.post is mocked. See settings.py on how to run.
"""
import os
import tempfile
from datetime import timedelta
from decimal import Decimal
from unittest import mock

import requests

from django.contrib.sites.models import Site
from django.db.backends.utils import CursorWrapper
from django.test import SimpleTestCase, TestCase, TransactionTestCase, override_settings
from django.utils import timezone

from sewingworld.telegram import MAX_LENGTH, TelegramError, send_message
from shop import health
from shop.models import HealthCheck, ImportRun, Order, ShopUser, Stock, Supplier
from shop.tasks import stocks
from shop.tasks.admin import notify_manager_telegram, notify_staff

from .fixtures import add_marketplace_sites, add_product, mock_constance

TOKEN = '123456:secret-token'


def answer(status=200, **json):
    response = mock.Mock(status_code=status)
    response.json.return_value = json
    return response


@override_settings(TELEGRAM_BOT_TOKEN=TOKEN, TELEGRAM_STAFF_CHAT='-1001')
class SendMessageTests(SimpleTestCase):
    def test_posts_the_text_to_the_staff_channel(self):
        with mock.patch('requests.post', return_value=answer(ok=True, result={'message_id': 7})) as post:
            self.assertEqual(send_message('Новый заказ'), {'message_id': 7})
        post.assert_called_once_with(
            f'https://api.telegram.org/bot{TOKEN}/sendMessage',
            json={'chat_id': '-1001', 'text': 'Новый заказ', 'link_preview_options': {'is_disabled': True}},
            timeout=30,
        )

    def test_long_text_is_cut_to_telegrams_length(self):
        with mock.patch('requests.post', return_value=answer(ok=True, result={})) as post:
            send_message('я' * (MAX_LENGTH + 10))
        text = post.call_args.kwargs['json']['text']
        self.assertEqual(len(text), MAX_LENGTH)
        self.assertTrue(text.endswith('…'))

    @override_settings(TELEGRAM_BOT_TOKEN='')
    def test_nothing_is_posted_without_a_token(self):
        with mock.patch('requests.post') as post:
            self.assertIsNone(send_message('Новый заказ'))
        post.assert_not_called()

    def test_refusal_raises_with_telegrams_description(self):
        with mock.patch('requests.post', return_value=answer(400, ok=False, description='Bad Request: chat not found')):
            with self.assertRaisesMessage(TelegramError, 'Bad Request: chat not found') as raised:
                send_message('Новый заказ')
        self.assertIsNone(raised.exception.retry_after)

    def test_rate_limit_tells_when_to_retry(self):
        limited = answer(429, ok=False, description='Too Many Requests', parameters={'retry_after': 15})
        with mock.patch('requests.post', return_value=limited):
            with self.assertRaises(TelegramError) as raised:
                send_message('Новый заказ')
        self.assertEqual(raised.exception.retry_after, 15)

    def test_connection_error_does_not_reveal_the_token(self):
        error = requests.ConnectionError(f'Max retries exceeded with url: /bot{TOKEN}/sendMessage')
        with mock.patch('requests.post', side_effect=error):
            with self.assertRaises(TelegramError) as raised:
                send_message('Новый заказ')
        self.assertNotIn(TOKEN, str(raised.exception))
        self.assertIsNone(raised.exception.__cause__)
        self.assertTrue(raised.exception.__suppress_context__)


class NotifyStaffTests(SimpleTestCase):
    def post(self, error, retries=0, expires=None):
        """ Runs notify_staff as its retries'th retry with the post failing, returns the countdown of the retry """
        notify_staff.push_request(retries=retries, expires=expires)
        self.addCleanup(notify_staff.pop_request)
        with mock.patch('shop.tasks.admin.send_message', side_effect=error), \
                mock.patch.object(notify_staff, 'retry', side_effect=RuntimeError) as retry:
            with self.assertRaises(RuntimeError):
                notify_staff.run('Импорт')
        return retry.call_args.kwargs

    def test_rate_limit_retries_as_late_as_telegram_asks(self):
        self.assertEqual(self.post(TelegramError('Too Many Requests', 15))['countdown'], 15)

    def test_failures_are_retried_with_growing_intervals_up_to_half_an_hour(self):
        error = TelegramError('Telegram: ConnectionError')
        self.assertEqual([self.post(error, retries)['countdown'] for retries in (0, 1, 2, 3, 4, 5, 6, 100)],
                         [60, 120, 240, 480, 960, 1800, 1800, 1800])

    def test_notices_expire_in_two_days_and_are_retried_without_a_count(self):
        for task in (notify_staff, notify_manager_telegram):
            with self.subTest(task.name), mock.patch.object(task.app, 'send_task') as send_task:
                task.delay(1)
                self.assertEqual(send_task.call_args.kwargs['expires'], 2 * 24 * 3600)
                self.assertIsNone(task.max_retries)

    def test_retry_keeps_the_expiry_of_the_notice(self):
        expires = timezone.now() + timedelta(hours=5)
        self.assertEqual(self.post(TelegramError('Bad Gateway'), 3, expires.isoformat())['expires'], expires)

    def test_notice_queued_without_an_expiry_gets_one_on_its_retry(self):
        expires = self.post(TelegramError('Bad Gateway'))['expires']
        self.assertAlmostEqual(expires, timezone.now() + timedelta(days=2), delta=timedelta(minutes=1))

    def test_outdated_notice_fails_instead_of_a_retry_after_its_expiry(self):
        expires = (timezone.now() + timedelta(minutes=10)).isoformat()
        for error in (TelegramError('Bad Gateway'), TelegramError('Too Many Requests', 900)):
            with self.subTest(error.retry_after):
                notify_staff.push_request(retries=5, expires=expires)
                self.addCleanup(notify_staff.pop_request)
                with mock.patch('shop.tasks.admin.send_message', side_effect=error), \
                        mock.patch.object(notify_staff, 'retry') as retry:
                    with self.assertRaises(TelegramError):
                        notify_staff.run('Импорт')
                retry.assert_not_called()
        self.assertEqual(self.post(TelegramError('Too Many Requests', 60), 5, expires)['countdown'], 60)


class OrderNoticeTests(TestCase):
    def setUp(self):
        add_marketplace_sites()  # saving a product put in an order looks them up
        patcher = mock.patch('shop.signals.logger')  # logs every product put in an order
        patcher.start()
        self.addCleanup(patcher.stop)
        self.user = ShopUser.objects.create(phone='+79161234567', email='buyer@shop.test')
        self.main_site = Site.objects.get_current()

    def order(self, site):
        order = Order.objects.create(user=self.user, site=site, name='Покупатель', phone='+79161234567',
                                     email='buyer@shop.test', delivery_price=300)
        order.items.create(product=add_product(1), product_price=1000, quantity=2)
        return order

    def text(self, order):
        with mock.patch('shop.tasks.admin.get_default_site', return_value=self.main_site), \
                mock.patch('shop.tasks.admin.send_message') as send:
            notify_manager_telegram.run(order.id)
        return send.call_args.args[0]

    def test_new_order_is_posted_after_the_commit_at_once(self):
        with mock.patch.object(notify_manager_telegram, 'apply_async') as apply_async, \
                mock.patch('shop.signals.notify_manager.apply_async'):
            with self.captureOnCommitCallbacks(execute=True):
                order = Order.objects.create(user=self.user, site=self.main_site)
                apply_async.assert_not_called()
        apply_async.assert_called_once()
        self.assertEqual(apply_async.call_args.args[0], (order.id,))
        self.assertIsNone(apply_async.call_args.kwargs.get('countdown'))  # unlike the mail, it waits for no details

    def test_notice_is_short_without_the_customer(self):
        order = self.order(self.main_site)
        self.assertEqual(order.total, Decimal('2300'))
        self.assertEqual(self.text(order), f'Новый заказ №{order.id}\nСумма: 2300.00 руб.\n'
                                           f'https://admin.sewing-world.ru/admin/shop/order/{order.id}/change/')

    def test_other_site_is_named(self):
        site = Site.objects.create(domain='janome.club', name='Janome')
        text = self.text(self.order(site))
        self.assertIn('(janome.club)', text.splitlines()[0])
        for customer in ('Покупатель', '+79161234567', 'buyer@shop.test'):
            self.assertNotIn(customer, text)


class ImportNoticeTests(TestCase):
    def setUp(self):
        mock_constance(self)
        patcher = mock.patch.object(notify_staff, 'delay')
        self.delay = patcher.start()
        self.addCleanup(patcher.stop)
        self.announced = self.enterContext(mock.patch('shop.tasks.stocks.publish_status'))

    def posts(self):
        return [call.args[0] for call in self.delay.call_args_list]

    def test_start_is_posted(self):
        with mock.patch('shop.tasks.stocks._import1c', return_value='27.11.2026 10:00:00') as import1c:
            self.assertEqual(stocks.import1c.run('stock.csv'), '27.11.2026 10:00:00')
        self.assertEqual(self.posts(), ['Импорт 1С из stock.csv начат'])
        self.assertEqual(import1c.call_args.args[1], ImportRun.objects.get())

    def test_failure_is_posted_and_fails_the_run(self):
        with mock.patch('shop.tasks.stocks._import1c', side_effect=ValueError('bad line')):
            with self.assertRaisesMessage(ValueError, 'bad line'):
                stocks.import1c.run('stock.csv')
        self.assertEqual(self.posts(), ['Импорт 1С из stock.csv начат',
                                        'Импорт 1С из stock.csv прерван: ValueError: bad line'])
        run = ImportRun.objects.get()
        self.assertEqual((run.stage, run.active, run.error), (ImportRun.FAILED, None, 'ValueError: bad line'))
        self.assertIsNone(ImportRun.running())
        self.assertEqual(HealthCheck.objects.get(operation=health.IMPORT).error, 'ValueError: bad line')
        self.assertEqual(self.announced.call_args.kwargs['stage'], ImportRun.FAILED)

    def test_nothing_runs_while_another_import_runs(self):
        ImportRun.objects.create(file='other.csv', active=True)
        with mock.patch('shop.tasks.stocks._import1c') as import1c:
            self.assertIsNone(stocks.import1c.run('stock.csv'))
        import1c.assert_not_called()
        self.assertEqual(self.posts(), [])

    def test_a_run_whose_worker_died_is_taken_over(self):
        dead = ImportRun.objects.create(file='stock.csv', active=True,
                                        started_at=timezone.now() - ImportRun.STALE - timedelta(minutes=1))
        self.assertIsNone(ImportRun.running())  # products can be saved again
        self.assertEqual(ImportRun.status()['stage'], ImportRun.FAILED)
        with mock.patch('shop.tasks.stocks._import1c', return_value=None):
            stocks.import1c.run('stock.csv')
        dead.refresh_from_db()
        self.assertEqual((dead.stage, dead.active), (ImportRun.FAILED, None))
        self.assertIn('обработчик Celery остановлен', dead.error)


class ImportFileTests(TransactionTestCase):
    """ Imports of a small file: the stock table is replaced in a transaction of its own, which a failure rolls back """

    def setUp(self):
        mock_constance(self)
        self.supplier = Supplier.objects.create(code='S', code1c='001', name='Склад', order=1)
        self.stock = Stock.objects.create(product=add_product(1), supplier=self.supplier, quantity=3)
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.enterContext(override_settings(SHOP_IMPORT_DIRECTORY=self.directory.name))
        self.enterContext(mock.patch.object(notify_staff, 'delay'))
        self.enterContext(mock.patch.object(stocks.count_stocks, 'delay'))
        self.enterContext(mock.patch('shop.tasks.stocks.send_mail'))
        # Constance's cache, which CI doesn't have; given, so that mock doesn't look into the lazy original
        self.enterContext(mock.patch('shop.tasks.stocks.config', new=mock.Mock(sw_email_from='robot@shop.test')))
        self.enterContext(mock.patch('shop.tasks.stocks.get_default_site'))
        self.announced = self.enterContext(mock.patch('shop.tasks.stocks.publish_status'))

    def write(self, text):
        with open(os.path.join(self.directory.name, 'stock.csv'), 'w') as f:
            f.write(text)

    def stages(self):
        return [call.kwargs['stage'] for call in self.announced.call_args_list]

    def test_done(self):
        self.write('27.11.2026 10:00:00\n\n//Список складов\nСклад;001\n//Остатки\n')
        self.assertEqual(stocks.import1c.run('stock.csv'), '27.11.2026 10:00:00')
        run = ImportRun.objects.get()
        self.assertEqual((run.stage, run.active, run.errors), (ImportRun.DONE, None, 0))
        self.assertEqual(timezone.localtime(run.file_date).strftime('%d.%m.%Y %H:%M'), '27.11.2026 10:00')
        self.assertEqual(self.stages(), [ImportRun.RUNNING, ImportRun.COPYING, ImportRun.RUNNING, ImportRun.DONE])
        self.assertEqual(ImportRun.status()['last'], '27.11.2026 10:00')
        self.assertEqual(HealthCheck.objects.get(operation=health.IMPORT).failures, 0)

    def test_a_file_that_leaves_the_stock_fails_the_run(self):
        self.write('27.11.2026 10:00:00\n\nсломанный файл\n')
        stocks.import1c.run('stock.csv')
        run = ImportRun.objects.get()
        self.assertEqual(run.stage, ImportRun.FAILED)
        self.assertIn('Неправильный формат файла импорта', run.error)
        self.assertEqual(HealthCheck.objects.get(operation=health.IMPORT).failures, 1)
        self.assertEqual(list(Stock.objects.values_list('pk', 'quantity')), [(self.stock.pk, 3)])

    def test_stock_survives_a_failed_copy(self):
        self.write('27.11.2026 10:00:00\n\n//Список складов\nСклад;001\n//Остатки\n')
        # the cursor wrapper hands copy_from() to psycopg2's cursor, whose C type can't be patched
        with mock.patch.object(CursorWrapper, 'copy_from', create=True, side_effect=OSError('disk full')) as copy_from:
            with self.assertRaisesMessage(OSError, 'disk full'):
                stocks.import1c.run('stock.csv')
        copy_from.assert_called_once()
        self.assertEqual(list(Stock.objects.values_list('pk', 'quantity')), [(self.stock.pk, 3)])
        run = ImportRun.objects.get()
        self.assertEqual((run.stage, run.active, run.error), (ImportRun.FAILED, None, 'OSError: disk full'))
        # The admin pages heard of each step at once
        self.assertEqual(self.stages(), [ImportRun.RUNNING, ImportRun.COPYING, ImportRun.FAILED])
