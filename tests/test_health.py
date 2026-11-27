"""
Health, shop/health.py: failures counted per operation and raised as problems, their notices, staleness, Wildberries
token expiry, SMS sending, Celery's queues, broker and beat, the check_health command and the admin's indicators.
"""
import base64
import json
from datetime import timedelta
from io import BytesIO, StringIO
from unittest.mock import Mock, patch
from urllib.error import HTTPError, URLError

from celery.exceptions import Retry
from django_celery_beat.models import IntervalSchedule, PeriodicTask
from django_celery_results.models import TaskResult
from kombu.exceptions import OperationalError
from django.contrib import admin
from django.contrib.auth.models import Permission
from django.contrib.sites.models import Site
from django.core import mail
from django.core.exceptions import PermissionDenied
from django.core.management import CommandError, call_command
from django.test import RequestFactory, TestCase, override_settings
from django.urls import path
from django.utils import timezone

from sewingworld import sms
from sewingworld.models import SiteProfile
from sewingworld.signals import create_task_result_on_publish
from shop import health
from shop.models import HealthCheck, Integration, ShopUser
from shop.tasks.admin import notify_health
from shop.tasks.monitoring import heartbeat

from .fixtures import add_marketplace_sites, mock_constance

POLL = 'ozon.tasks.get_integration_unfulfilled_orders'
STOCKS = 'ozon.tasks.notify_product_stocks'
WB_ORDERS = 'wb.tasks.get_integration_new_orders'

urlpatterns = [path('admin/', admin.site.urls)]


def http_error(status, body):
    return HTTPError('https://api.test/', status, 'Error', {}, BytesIO(body.encode()))


def jwt(expiry):
    """ A token that looks like Wildberries' JWT, unsigned """
    def part(data):
        return base64.urlsafe_b64encode(json.dumps(data).encode()).rstrip(b'=').decode()
    return f"{part({'alg': 'ES256'})}.{part({'exp': int(expiry.timestamp()), 'sid': 'seller'})}.signature"


class HealthTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        add_marketplace_sites()
        cls.ozon_site = Site.objects.get(domain='ozon.ru')
        SiteProfile.objects.create(site=cls.ozon_site, manager_emails='ozon@shop.test, boss@shop.test')
        cls.wb_site = Site.objects.get(domain='wildberries.ru')
        SiteProfile.objects.create(site=cls.wb_site)
        cls.ozon = Integration.objects.create(name='Ozon', utm_source='ozon', source_site=cls.ozon_site,
                                              target_site=Site.objects.get_current(), uses_api=True, enabled=True,
                                              settings={})
        cls.wb = Integration.objects.create(name='Wildberries', utm_source='wb', source_site=cls.wb_site,
                                            target_site=Site.objects.get_current(), uses_api=True, enabled=True,
                                            settings={'api_key': 'not-a-jwt'})

    def setUp(self):
        self.config = mock_constance(self)
        self.queued = self.enterContext(patch.object(notify_health, 'delay'))
        self.published = self.enterContext(patch.object(heartbeat, 'apply_async'))

    def failure(self, operation=POLL, error='HTTP 400: Invalid filter', integration=None):
        with self.captureOnCommitCallbacks(execute=True):
            return health.record_failure(integration or self.ozon, operation, error)

    def success(self, operation=POLL, integration=None):
        with self.captureOnCommitCallbacks(execute=True):
            return health.record_success(integration or self.ozon, operation)

    def check(self, operation=POLL, integration=None):
        return HealthCheck.objects.get(integration=integration or self.ozon, operation=operation)


class FailureTests(HealthTestCase):
    def test_first_failure_warns_and_the_third_raises_once(self):
        self.assertIsNone(self.failure())
        self.assertEqual(health.level(self.check(), timezone.now()), health.WARNING)
        self.assertEqual(health.summary(health.INTEGRATIONS)['level'], health.WARNING)
        self.failure()
        self.queued.assert_not_called()

        notice = self.failure(error='HTTP 401: Token expired')
        check = self.check()
        self.assertEqual((check.failures, check.error), (3, 'HTTP 401: Token expired'))
        self.assertIsNotNone(check.raised_at)
        self.assertEqual(health.level(check, timezone.now()), health.PROBLEM)
        self.queued.assert_called_once_with([notice], True)
        self.assertEqual(notice['since'], check.first_failed_at.isoformat())

        self.failure()
        self.queued.assert_called_once()
        self.assertEqual(health.summary(health.INTEGRATIONS)['level'], health.PROBLEM)

    def test_threshold_is_a_setting(self):
        self.config.sw_integration_failures = 1
        self.assertIsNotNone(self.failure())

    def test_success_clears_and_tells_only_about_a_raised_problem(self):
        self.failure()
        self.assertIsNone(self.success())
        check = self.check()
        self.assertEqual((check.failures, check.error, check.first_failed_at), (0, '', None))
        self.queued.assert_not_called()

        for _ in range(3):
            self.failure()
        self.queued.reset_mock()
        notice = self.success()
        self.queued.assert_called_once_with([notice], False)
        self.assertIsNone(self.check().raised_at)
        self.assertEqual(health.summary(health.INTEGRATIONS)['level'], health.OK)

    def test_operations_count_apart(self):
        for _ in range(2):
            self.failure()
            self.success(STOCKS)
        self.assertIsNotNone(self.failure())
        self.assertEqual(self.check(STOCKS).failures, 0)

    def test_success_while_all_is_well_writes_at_most_once_a_minute(self):
        self.success()
        first = self.check().last_success_at
        self.success()
        self.assertEqual(self.check().last_success_at, first)
        HealthCheck.objects.update(last_success_at=first - timedelta(minutes=2))
        self.success()
        self.assertGreater(self.check().last_success_at, first)

    def test_disabled_integrations_are_left_out(self):
        for _ in range(3):
            self.failure()
        Integration.objects.filter(pk=self.ozon.pk).update(enabled=False)
        self.assertEqual(health.summary(health.INTEGRATIONS), {'level': health.OK, 'color': 'limegreen',
                                                               'title': 'Обмен с маркетплейсами и SMS в порядке', 'problems': []})


class PublishTests(HealthTestCase):
    """ Open admin pages hear of a group's change of level, see sewingworld/notifications.py """

    def setUp(self):
        super().setUp()
        self.status = self.enterContext(patch('sewingworld.notifications.publish_status'))

    def statuses(self):
        return [(call.args[0], call.kwargs['group'], call.kwargs['level']) for call in self.status.call_args_list]

    def test_a_change_of_level_is_published_on_commit(self):
        with self.captureOnCommitCallbacks() as callbacks:
            health.record_failure(self.ozon, POLL, 'HTTP 400: Invalid filter')
            self.status.assert_not_called()
        for callback in callbacks:
            callback()
        self.assertEqual(self.statuses(), [('health', health.INTEGRATIONS, health.WARNING)])

        self.failure()  # still a warning
        self.assertEqual(len(self.statuses()), 1)
        self.failure()  # raised
        self.success()
        self.assertEqual(self.statuses()[1:], [('health', health.INTEGRATIONS, health.PROBLEM),
                                               ('health', health.INTEGRATIONS, health.OK)])

    def test_heartbeats_of_a_healthy_queue_publish_nothing(self):
        with self.captureOnCommitCallbacks(execute=True):
            heartbeat.run('priority')
        self.status.reset_mock()
        HealthCheck.objects.filter(operation='celery.priority').update(last_success_at=timezone.now() - timedelta(minutes=2))
        with self.captureOnCommitCallbacks(execute=True):
            heartbeat.run('priority')
        self.status.assert_not_called()

    def test_command_publishes_both_groups(self):
        with patch('sewingworld.telegram.send_message'):
            call_command('check_health', stdout=StringIO())
        self.assertEqual({group for _, group, _ in self.statuses()}, set(health.GROUPS))


class MonitorTests(HealthTestCase):
    def test_records_the_outcome_and_reraises_the_original_exception(self):
        error = health.IntegrationFailure('Token expired', status=401, body='{"detail": "Token expired", "code": 401}')
        with self.assertRaises(health.IntegrationFailure) as raised:
            with health.monitor(self.ozon, POLL):
                raise error
        self.assertIs(raised.exception, error)
        self.assertEqual(self.check().error, 'HTTP 401: Token expired\n{"detail": "Token expired", "code": 401}')

        with health.monitor(self.ozon, POLL):
            pass
        self.assertEqual(self.check().failures, 0)

    def test_fail_counts_a_failure_without_an_exception(self):
        with health.monitor(self.ozon, STOCKS) as outcome:
            outcome.fail('Ozon не принял остатки')
        self.assertEqual((self.check(STOCKS).failures, self.check(STOCKS).error), (1, 'Ozon не принял остатки'))

    def test_celery_retry_is_not_a_failure(self):
        with self.assertRaises(Retry):
            with health.monitor(self.ozon, POLL):
                raise Retry()
        self.assertFalse(HealthCheck.objects.exists())

    def test_a_failing_record_does_not_mask_the_task_outcome(self):
        with patch('shop.health.record_failure', side_effect=RuntimeError('database')), \
                self.assertLogs('shop', 'ERROR'):
            with self.assertRaises(KeyError):
                with health.monitor(self.ozon, POLL):
                    raise KeyError('postings')
        with patch('shop.health.record_success', side_effect=RuntimeError('database')), \
                self.assertLogs('shop', 'ERROR'):
            with health.monitor(self.ozon, POLL):
                pass

    def test_describe(self):
        self.assertEqual(health.describe(http_error(502, '<html>Bad gateway</html>')), 'HTTP 502 Error\n<html>Bad gateway</html>')
        self.assertEqual(health.describe(URLError('Name or service not known')), 'Нет связи: Name or service not known')
        self.assertEqual(health.describe(TimeoutError('timed out')), 'Нет ответа: истекло время ожидания')
        self.assertEqual(health.describe(KeyError('postings')), "KeyError: 'postings'")
        self.assertEqual(health.describe(health.IntegrationFailure('Same', status=400, body='Same')), 'HTTP 400: Same')
        long = health.describe(health.IntegrationFailure('x' * 5000))
        self.assertEqual(len(long), health.MAX_ERROR)
        self.assertTrue(long.endswith('…'))


class NoticeTests(HealthTestCase):
    def test_mail_goes_to_the_channel_managers_and_telegram_through_its_own_task(self):
        for _ in range(3):
            notice = self.failure(error='HTTP 400: {"message": "invalid Statuses[6]"}')
        with patch('shop.tasks.admin.notify_staff.delay') as post:
            notify_health.run([notice], True)
        message = mail.outbox[0]
        self.assertEqual(message.to, ['boss@shop.test', 'ozon@shop.test'])
        self.assertEqual(message.subject, 'Сбой: Ozon, получение заказов')
        self.assertIn('неудачных попыток подряд: 3', message.body)
        self.assertIn('"message": "invalid Statuses[6]"', message.body)  # not HTML-escaped
        text = post.call_args.args[0]
        self.assertIn('Ozon (ozon, example.com): получение заказов', text)
        self.assertIn('сбоев подряд: 3', text)
        self.assertIn('https://admin.sewing-world.ru/admin/shop/healthcheck/', text)

    def test_recovery_and_the_main_site_managers_for_a_channel_without_its_own(self):
        main = Site.objects.get_current()
        SiteProfile.objects.create(site=main, manager_emails='main@shop.test')
        for _ in range(3):
            self.failure(WB_ORDERS, integration=self.wb)
        notice = self.success(WB_ORDERS, integration=self.wb)
        with patch('shop.tasks.common.get_default_site', return_value=main), \
                patch('shop.tasks.admin.notify_staff.delay') as post:
            notify_health.run([notice], False)
        self.assertEqual(mail.outbox[0].to, ['main@shop.test'])
        self.assertEqual(mail.outbox[0].subject, 'Восстановлено: Wildberries, получение новых заказов')
        self.assertIn('Не работала с', post.call_args.args[0])


class StaleTests(HealthTestCase):
    def setUp(self):
        super().setUp()
        self.success()
        self.long_ago = timezone.now() - timedelta(hours=2)
        HealthCheck.objects.update(last_success_at=self.long_ago)

    def test_indicator_shows_stale_operations_as_problems_without_the_command(self):
        status = health.summary(health.INTEGRATIONS)
        self.assertEqual(status['level'], health.PROBLEM)
        self.assertTrue(status['problems'][0]['error'].startswith('Нет успешного обмена с'))
        # Operations that don't run on schedule never go stale
        HealthCheck.objects.update(operation=STOCKS)
        self.assertEqual(health.summary(health.INTEGRATIONS)['level'], health.OK)

    def test_command_raises_once_and_notifies_without_celery(self):
        with patch('sewingworld.telegram.send_message') as post:
            call_command('check_health', stdout=StringIO())
            call_command('check_health', stdout=StringIO())
        self.queued.assert_not_called()
        post.assert_called_once()
        self.assertIn('Нет успешного обмена с', post.call_args.args[0])
        self.assertEqual(len(mail.outbox), 1)
        self.assertIsNotNone(self.check().raised_at)

        # The poller comes back
        notice = self.success()
        self.queued.assert_called_once_with([notice], False)

    def test_command_leaves_problems_unraised_when_nothing_takes_the_notice(self):
        with patch('sewingworld.telegram.send_message', side_effect=OSError('down')), \
                patch('shop.health.send_mail', side_effect=OSError('down')), \
                self.assertLogs('shop', 'ERROR'):
            with self.assertRaises(CommandError):
                call_command('check_health', stdout=StringIO())
        self.assertIsNone(self.check().raised_at)

    def test_dry_run_changes_and_sends_nothing(self):
        out = StringIO()
        with patch('sewingworld.telegram.send_message') as post:
            call_command('check_health', '--dry-run', stdout=out)
        post.assert_not_called()
        self.assertIsNone(self.check().raised_at)
        self.assertIn('Интеграции: problem', out.getvalue())


class TokenTests(HealthTestCase):
    def token_level(self, days):
        Integration.objects.filter(pk=self.wb.pk).update(settings={'api_key': jwt(timezone.now() + timedelta(days=days))})
        with patch('sewingworld.telegram.send_message'):
            call_command('check_health', stdout=StringIO())
        check = self.check(health.TOKEN, self.wb)
        return health.level(check, timezone.now())

    def test_warns_two_weeks_ahead_and_raises_three_days_ahead(self):
        self.assertEqual(self.token_level(30), health.OK)
        self.assertEqual(self.token_level(10), health.WARNING)
        self.assertEqual(len(mail.outbox), 0)
        self.assertEqual(self.token_level(2), health.PROBLEM)
        self.assertIn('Токен API истекает', self.check(health.TOKEN, self.wb).error)
        self.assertEqual(self.token_level(-1), health.PROBLEM)
        self.assertIn('Токен API истёк', self.check(health.TOKEN, self.wb).error)
        # A new token
        self.assertEqual(self.token_level(180), health.OK)

    def test_keys_that_are_not_jwts_are_skipped(self):
        self.assertIsNone(health.token_expiry('not-a-jwt'))
        self.assertIsNone(health.token_expiry('a.b.c'))
        with patch('sewingworld.telegram.send_message'):
            call_command('check_health', stdout=StringIO())
        self.assertFalse(HealthCheck.objects.filter(operation=health.TOKEN).exists())


class QueueTests(HealthTestCase):
    def setUp(self):
        super().setUp()
        # Notices without an integration go to the managers of the main site
        main = Site.objects.get_current()
        SiteProfile.objects.create(site=main, manager_emails='main@shop.test')
        self.enterContext(patch('shop.tasks.common.get_default_site', return_value=main))

    def run_check(self):
        with patch('sewingworld.telegram.send_message') as post:
            call_command('check_health', stdout=StringIO())
        return post

    def test_command_sends_a_heartbeat_through_each_queue(self):
        self.run_check()
        sent = {call.kwargs['queue']: call for call in self.published.call_args_list}
        self.assertEqual(set(sent), set(health.QUEUES))
        self.assertEqual(sent['priority'].args, (('priority',),))
        self.assertEqual(sent['priority'].kwargs['expires'], 300)
        self.assertFalse(sent['priority'].kwargs['retry'])
        # Watched from the start, so that a queue that never takes one goes stale
        self.assertEqual(HealthCheck.objects.filter(integration=None, operation__startswith='celery.').count(), 6)  # and the broker
        self.assertEqual(health.summary(health.QUEUES_GROUP)['level'], health.OK)

    def test_heartbeat_is_the_queue_success(self):
        heartbeat.run('priority')
        self.assertIsNotNone(HealthCheck.objects.get(integration=None, operation='celery.priority').last_success_at)

    def test_a_queue_that_leaves_its_heartbeat_waiting_is_raised(self):
        self.run_check()
        HealthCheck.objects.filter(operation='celery.priority').update(created_at=timezone.now() - timedelta(minutes=6))
        status = health.summary(health.QUEUES_GROUP)
        self.assertEqual(status['level'], health.PROBLEM)
        self.assertTrue(status['title'].startswith('очередь priority: Очередь не обработала проверочную задачу с'))

        post = self.run_check()
        self.assertIn('очередь priority', post.call_args.args[0])
        self.assertEqual((mail.outbox[0].subject, mail.outbox[0].to), ('Сбой: очередь priority', ['main@shop.test']))

        # The workers come back: recovery goes through Celery
        with self.captureOnCommitCallbacks(execute=True):
            heartbeat.run('priority')
        self.queued.assert_called_once()
        self.assertEqual(self.queued.call_args.args[0][0]['operation'], 'celery.priority')

    def test_broker_that_takes_no_task_is_a_problem_at_once_and_its_return_is_told(self):
        self.published.side_effect = OperationalError('Error 111 connecting to localhost:6379. Connection refused.')
        post = self.run_check()
        self.assertIn('брокер Celery (Redis)', post.call_args.args[0])
        self.assertIn('Connection refused', HealthCheck.objects.get(operation=health.BROKER).error)

        self.published.side_effect = None
        post = self.run_check()
        self.assertTrue(post.call_args.args[0].startswith('Восстановлено'))
        self.assertEqual(health.level(HealthCheck.objects.get(operation=health.BROKER), timezone.now()), health.OK)

    def test_beat_that_runs_nothing_for_a_while_is_a_problem(self):
        schedule = IntervalSchedule.objects.create(every=5, period=IntervalSchedule.MINUTES)
        task = PeriodicTask.objects.create(name='poll', task='ozon.tasks.get_unfulfilled_orders', interval=schedule,
                                           last_run_at=timezone.now() - timedelta(minutes=20))
        post = self.run_check()
        self.assertIn('celery_beat остановлен', post.call_args.args[0])
        task.last_run_at = timezone.now()
        task.save()
        post = self.run_check()
        self.assertIn('запуск задач по расписанию', post.call_args.args[0])
        self.assertTrue(post.call_args.args[0].startswith('Восстановлено'))

    def test_a_check_that_stops_running_shows(self):
        self.run_check()
        HealthCheck.objects.filter(operation=health.MONITOR).update(last_success_at=timezone.now() - timedelta(minutes=20))
        status = health.summary(health.QUEUES_GROUP)
        self.assertEqual(status['level'], health.PROBLEM)
        self.assertIn('Проверка состояния не запускалась', status['title'])

    def test_heartbeat_has_no_task_result_rows(self):
        create_task_result_on_publish(headers={'task': 'shop.tasks.heartbeat', 'id': 'h1', 'argsrepr': '', 'kwargsrepr': ''})
        create_task_result_on_publish(headers={'task': 'shop.tasks.send_message', 'id': 't1', 'argsrepr': '', 'kwargsrepr': ''})
        self.assertEqual(list(TaskResult.objects.values_list('task_id', flat=True)), ['t1'])
        self.assertTrue(heartbeat.ignore_result)


class SmsTests(HealthTestCase):
    def setUp(self):
        super().setUp()
        self.enterContext(patch('sewingworld.sms.config', new=Mock(sw_sms_provider='smsru')))
        self.client = self.enterContext(patch('sewingworld.sms.smsru.Client')).return_value

    def send(self, code, descr='Сообщение принято к отправке'):
        self.client.send.return_value = {'code': code, 'descr': descr, 'msg': '201-123'}
        return sms.send_sms('+79161234567', 'Код для доступа на сайт: 1234')

    def check(self):
        return HealthCheck.objects.get(integration=None, operation=health.SMS)

    def test_provider_failures_raise_and_count(self):
        for _ in range(3):
            with self.assertRaisesRegex(sms.SmsFailure, 'sms.ru 201: Не хватает средств'),                     self.captureOnCommitCallbacks(execute=True):
                self.send(201, 'Не хватает средств на лицевом счету')
        self.assertEqual((self.check().failures, self.check().error), (3, 'SmsFailure: sms.ru 201: Не хватает средств на лицевом счету'))
        self.queued.assert_called_once()
        self.assertEqual(health.summary(health.INTEGRATIONS)['problems'][0]['name'], 'отправка SMS')

        with self.captureOnCommitCallbacks(execute=True):
            self.assertEqual(self.send(100)['code'], 100)
        self.assertEqual(self.check().failures, 0)
        self.assertEqual(self.queued.call_count, 2)  # restored

    def test_errors_about_the_recipient_are_not_the_provider(self):
        self.assertEqual(self.send(202, 'Неправильно указан получатель')['code'], 202)
        self.assertEqual(self.check().failures, 0)

    def test_connection_errors_count(self):
        self.client.send.side_effect = URLError('timed out')
        with self.assertRaises(URLError):
            sms.send_sms('+79161234567', 'Текст')
        self.assertEqual(self.check().error, 'Нет связи: timed out')


@override_settings(ROOT_URLCONF=__name__)
class AdminTests(HealthTestCase):
    def setUp(self):
        super().setUp()
        self.factory = RequestFactory()
        self.superuser = ShopUser.objects.create(phone='+79990000000', is_staff=True, is_superuser=True)
        self.superuser.is_verified = lambda: True  # as the OTP middleware sets it

    def request(self, user, url='/admin/'):
        request = self.factory.get(url)
        request.user = user
        return request

    def test_checks_are_in_the_system_tab(self):
        response = admin.site.index(self.request(self.superuser))
        tabs = {tab['id']: [app['app_label'] for app in tab['apps']] for tab in response.context_data['tabs']}
        self.assertIn('monitoring', tabs['system'])
        self.assertEqual(tabs['system'][tabs['system'].index('errors') + 1], 'monitoring')
        shop = next(app for app in response.context_data['app_list'] if app['app_label'] == 'shop')
        self.assertNotIn('HealthCheck', [model['object_name'] for model in shop['models']])

    def test_top_bar_shows_the_level_and_the_problems(self):
        for _ in range(3):
            self.failure(error='HTTP 401: Token expired')
        content = admin.site.index(self.request(self.superuser)).render().content.decode()
        self.assertIn('id="health_integrations" data-group="integrations" title="Ozon, получение заказов: HTTP 401: Token expired"', content)
        self.assertIn('class="sw-level" style="color: red">&#9670;</span> Интеграции', content)
        self.assertIn('id="health_queues" data-group="queues" title="Очереди Celery в порядке"', content)
        self.assertIn('?group=queues', content)

    def test_status_view_needs_the_view_permission(self):
        model_admin = admin.site._registry[HealthCheck]
        self.failure()
        response = model_admin.status_view(self.request(self.superuser))
        levels = {group: status['level'] for group, status in json.loads(response.content).items()}
        self.assertEqual(levels, {health.INTEGRATIONS: health.WARNING, health.QUEUES_GROUP: health.OK})

        staff = ShopUser.objects.create(phone='+79990000001', is_staff=True)
        staff.is_verified = lambda: True
        content = admin.site.index(self.request(staff)).render().content.decode()
        self.assertNotIn('class="sw-health"', content)
        with self.assertRaises(PermissionDenied):
            model_admin.status_view(self.request(staff))

        staff.user_permissions.add(Permission.objects.get(codename='view_healthcheck'))
        staff = ShopUser.objects.get(pk=staff.pk)
        staff.is_verified = lambda: True
        self.assertEqual(model_admin.status_view(self.request(staff)).status_code, 200)

    def test_reset_clears_a_check(self):
        for _ in range(3):
            self.failure()
        model_admin = admin.site._registry[HealthCheck]
        with patch.object(model_admin, 'message_user'):
            model_admin.reset(self.request(self.superuser), HealthCheck.objects.all())
        self.assertEqual(health.level(self.check(), timezone.now()), health.OK)
