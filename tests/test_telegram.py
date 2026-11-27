"""
Posts to the staff channel in Telegram: the client, the new-order notice and the 1C import's notices. Nothing reaches
Telegram, requests.post is mocked. See settings.py on how to run.
"""
import os
import tempfile
from decimal import Decimal
from unittest import mock

import requests

from django.contrib.sites.models import Site
from django.core.cache import cache
from django.db.backends.utils import CursorWrapper
from django.test import SimpleTestCase, TestCase, TransactionTestCase, override_settings

from flags.state import enable_flag, flag_state

from sewingworld.telegram import MAX_LENGTH, TelegramError, send_message
from shop.models import Order, ShopUser, Stock, Supplier
from shop.tasks import stocks
from shop.tasks.admin import notify_manager_telegram, notify_staff

from .fixtures import add_marketplace_sites, add_product

TOKEN = '123456:secret-token'
# the import's lock is in the cache, which .env may point at a memcached that isn't running
LOCAL_CACHE = override_settings(CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}})


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
    def test_rate_limit_retries_as_late_as_telegram_asks(self):
        with mock.patch('shop.tasks.admin.send_message', side_effect=TelegramError('Too Many Requests', 15)), \
                mock.patch.object(notify_staff, 'retry', side_effect=RuntimeError) as retry:
            with self.assertRaises(RuntimeError):
                notify_staff.run('Импорт')
        self.assertEqual(retry.call_args.kwargs['countdown'], 15)


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
        self.assertEqual(self.text(order), f'Новый заказ №{order.id}\nИтого: 2300.00 руб.\n'
                                           f'https://admin.sewing-world.ru/admin/shop/order/{order.id}/change/')

    def test_other_site_is_named(self):
        site = Site.objects.create(domain='janome.club', name='Janome')
        text = self.text(self.order(site))
        self.assertIn('(janome.club)', text.splitlines()[0])
        for customer in ('Покупатель', '+79161234567', 'buyer@shop.test'):
            self.assertNotIn(customer, text)


@LOCAL_CACHE
class ImportNoticeTests(SimpleTestCase):
    def setUp(self):
        cache.delete('celery-single-instance-import1c')
        patcher = mock.patch.object(notify_staff, 'delay')
        self.delay = patcher.start()
        self.addCleanup(patcher.stop)

    def posts(self):
        return [call.args[0] for call in self.delay.call_args_list]

    def test_start_is_posted(self):
        with mock.patch('shop.tasks.stocks._import1c', return_value='27.11.2026 10:00:00'):
            self.assertEqual(stocks.import1c.run('stock.csv'), '27.11.2026 10:00:00')
        self.assertEqual(self.posts(), ['Импорт 1С из stock.csv начат'])

    def test_failure_is_posted_and_switches_the_flags_off(self):
        with mock.patch('shop.tasks.stocks._import1c', side_effect=ValueError('bad line')), \
                mock.patch('shop.tasks.stocks.disable_flag') as disable_flag:
            with self.assertRaisesMessage(ValueError, 'bad line'):
                stocks.import1c.run('stock.csv')
        self.assertEqual(self.posts(), ['Импорт 1С из stock.csv начат',
                                        'Импорт 1С из stock.csv прерван: ValueError: bad line'])
        self.assertEqual(sorted(call.args[0] for call in disable_flag.call_args_list),
                         ['1C_IMPORT_COPYING', '1C_IMPORT_RUNNING'])

    def test_nothing_is_posted_while_another_import_runs(self):
        cache.add('celery-single-instance-import1c', 'true', 60)
        self.addCleanup(cache.delete, 'celery-single-instance-import1c')
        with mock.patch('shop.tasks.stocks._import1c') as import1c:
            stocks.import1c.run('stock.csv')
        import1c.assert_not_called()
        self.assertEqual(self.posts(), [])


@LOCAL_CACHE
class ImportCopyFailureTests(TransactionTestCase):
    """ The stock table is replaced in a transaction of its own, which a failure must roll back """

    def setUp(self):
        cache.delete('celery-single-instance-import1c')
        self.supplier = Supplier.objects.create(code='S', code1c='001', name='Склад', order=1)
        self.stock = Stock.objects.create(product=add_product(1), supplier=self.supplier, quantity=3)
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        with open(os.path.join(directory.name, 'stock.csv'), 'w') as f:
            f.write('27.11.2026 10:00:00\n\n//Список складов\nСклад;001\n//Остатки\n')
        self.enterContext(override_settings(SHOP_IMPORT_DIRECTORY=directory.name))
        self.enterContext(mock.patch.object(notify_staff, 'delay'))
        self.enterContext(mock.patch.object(stocks.count_stocks, 'delay'))

    def test_stock_and_flags_survive_a_failed_copy(self):
        enable_flag('1C_IMPORT_RUNNING')
        # the cursor wrapper hands copy_from() to psycopg2's cursor, whose C type can't be patched
        with mock.patch.object(CursorWrapper, 'copy_from', create=True, side_effect=OSError('disk full')) as copy_from:
            with self.assertRaisesMessage(OSError, 'disk full'):
                stocks.import1c.run('stock.csv')
        copy_from.assert_called_once()
        self.assertEqual(list(Stock.objects.values_list('pk', 'quantity')), [(self.stock.pk, 3)])
        self.assertFalse(flag_state('1C_IMPORT_RUNNING'))
        self.assertFalse(flag_state('1C_IMPORT_COPYING'))
