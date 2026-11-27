"""
Health of what the shop depends on, a HealthCheck per operation: the integrations' exchange with the marketplaces'
APIs and the SMS provider ("Интеграции" in the admin's top bar), and Celery's queues, broker and beat ("Очереди").

A task wraps its exchange in monitor(integration, self.name), or monitor(None, operation) for one without an
integration, such as sending an SMS. An exception counts a failure, with a description such as the body of the API's
4xx reply, and finishing without one clears them. The first failure is a warning, gold in the top bar.
config.sw_integration_failures failures in a row raise a problem: red, and the managers get a notice by Telegram and
mail, once. The next success clears it and tells them that the operation is restored. Operations count apart, so that
stocks sent every two minutes don't hide orders that fail to come.

Operations with a max_age in OPERATIONS succeed on schedule whatever happens, so not succeeding for longer means that
they stopped. The check_health command, run every two minutes by a systemd timer rather than by Celery, sends a
heartbeat task through each queue (QUEUES), whose success is the queue's, and checks beat and the broker. summary()
shows stale operations as problems right away, and the command raises them and sends the notices itself, so that they
go out while Celery is down. A command that stops running shows as a stale MONITOR.

Open admin pages hear of a change of a group's level at once (publish()), and the command publishes both groups on
each run, which covers what goes stale with time.
"""
import base64
import binascii
import json
import logging
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from typing import NamedTuple
from urllib.error import HTTPError, URLError

from django.contrib.sites.models import Site
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import Q
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.formats import date_format
from django.views.decorators.debug import sensitive_variables

from celery.exceptions import Ignore, Retry
from constance import config

from shop.models import HealthCheck, Integration

logger = logging.getLogger('shop')

OK, WARNING, PROBLEM = 'ok', 'warning', 'problem'
LEVELS = (OK, WARNING, PROBLEM)  # by severity
# The colours of the admin's top bar, as its 1C import indicator's, see templates/admin/base_site.html
COLORS = {OK: 'limegreen', WARNING: 'gold', PROBLEM: 'red'}
INTEGRATIONS, QUEUES_GROUP = 'integrations', 'queues'
GROUPS = {INTEGRATIONS: 'Интеграции', QUEUES_GROUP: 'Очереди'}
ALL_WELL = {INTEGRATIONS: 'Обмен с маркетплейсами и SMS в порядке', QUEUES_GROUP: 'Очереди Celery в порядке'}
MAX_ERROR = 4000
# While all is well, a success refreshes last_success_at at most this often
SUCCESS_THROTTLE = timedelta(minutes=1)

TOKEN = 'token'
TOKEN_WARNING = timedelta(days=14)
TOKEN_PROBLEM = timedelta(days=3)
SMS = 'sms'
BROKER = 'celery.broker'
BEAT = 'celery.beat'
BEAT_MAX_AGE = timedelta(minutes=15)
MONITOR = 'monitor'
# Celery's queues and how long each may go without taking a heartbeat: import runs one 1C import at a time, for up
# to two hours
QUEUES = {
    'priority': timedelta(minutes=5),
    'default': timedelta(minutes=30),
    'integrations': timedelta(minutes=30),
    'revalidation': timedelta(minutes=30),
    'import': timedelta(hours=3),
}
QUEUES_OPERATIONS = {f'celery.{queue}' for queue in QUEUES}


class Operation(NamedTuple):
    label: str
    # How long an operation that succeeds on schedule may go without a success
    max_age: timedelta | None = None
    group: str = INTEGRATIONS


OPERATIONS = {
    'ozon.tasks.get_integration_unfulfilled_orders': Operation('получение заказов', timedelta(minutes=30)),
    'ozon.tasks.sync_integration_posting': Operation('уведомления о заказах'),
    'ozon.tasks.notify_product_stocks': Operation('передача остатков'),
    'wb.tasks.get_integration_new_orders': Operation('получение новых заказов', timedelta(minutes=30)),
    'wb.tasks.get_integration_detached_orders': Operation('получение заказов других складов', timedelta(hours=1)),
    'wb.tasks.get_integration_order_statuses': Operation('получение статусов заказов'),
    'wb.tasks.notify_product_stocks': Operation('передача остатков'),
    TOKEN: Operation('срок действия токена API'),
    SMS: Operation('отправка SMS'),
    BROKER: Operation('брокер Celery (Redis)', group=QUEUES_GROUP),
    BEAT: Operation('запуск задач по расписанию (beat)', group=QUEUES_GROUP),
    MONITOR: Operation('проверка состояния (check_health)', timedelta(minutes=10), QUEUES_GROUP),
    **{f'celery.{queue}': Operation(f'очередь {queue}', max_age, QUEUES_GROUP) for queue, max_age in QUEUES.items()},
}


def label(operation):
    known = OPERATIONS.get(operation)
    return known.label if known else operation


def group(operation):
    known = OPERATIONS.get(operation)
    return known.group if known else INTEGRATIONS


def operations(group_name):
    return [operation for operation, known in OPERATIONS.items() if known.group == group_name]


def name(check):
    """ What the check is about, for people """
    operation = label(check.operation)
    return f'{check.integration}, {operation}' if check.integration_id else operation


class IntegrationFailure(Exception):
    """ A failed exchange: the API's message, with the HTTP status and the body of its reply when it had one """
    def __init__(self, message, status=None, body=None):
        super().__init__(message)
        self.status = status
        self.body = body


def read_body(error):
    """ The text of an HTTPError's reply, empty once read """
    try:
        return error.read().decode('utf-8', 'replace').strip()
    except Exception:
        return ''


def describe(exc):
    """ What went wrong, for the managers: the API's reply, the network's error, or ours. Never request headers. """
    if isinstance(exc, IntegrationFailure):
        text = str(exc)
        if exc.status:
            text = f'HTTP {exc.status}: {text}'
        if exc.body and exc.body.strip() != str(exc):
            text += '\n' + exc.body.strip()
    elif isinstance(exc, HTTPError):
        text = f'HTTP {exc.code} {exc.reason}'
        body = read_body(exc)
        if body:
            text += '\n' + body
    elif isinstance(exc, URLError):
        text = f'Нет связи: {exc.reason}'
    elif isinstance(exc, TimeoutError):
        text = 'Нет ответа: истекло время ожидания'
    else:
        text = f'{type(exc).__name__}: {exc}'
    return truncate(text)


def truncate(text):
    return text if len(text) <= MAX_ERROR else text[:MAX_ERROR - 1] + '…'


def watched():
    """ The checks that count: those of enabled integrations, and those without one """
    return HealthCheck.objects.filter(Q(integration__isnull=True) | Q(integration__enabled=True))


def stale_since(check, now):
    """ The last success of a scheduled operation that has gone without one for too long, otherwise None """
    known = OPERATIONS.get(check.operation)
    if known is None or known.max_age is None:
        return None
    since = check.last_success_at or check.created_at
    return since if now - since > known.max_age else None


def stale_message(check, since):
    when = date_format(timezone.localtime(since), 'd.m.Y H:i')
    if check.operation == MONITOR:
        return f'Проверка состояния не запускалась с {when}: таймер health_check не работает, оповещений не будет'
    if check.operation in QUEUES_OPERATIONS:
        return f'Очередь не обработала проверочную задачу с {when}: обработчики Celery остановлены или заняты'
    return f'Нет успешного обмена с {when}'


def level(check, now):
    if check.raised_at is not None or stale_since(check, now):
        return PROBLEM
    if check.failures or check.error:
        return WARNING
    return OK


def status_text(check, now):
    """ The check's error, or that it went stale while the command hasn't raised it yet """
    since = stale_since(check, now)
    if since and check.raised_at is None:
        return stale_message(check, since) + (f'\n{check.error}' if check.error else '')
    return check.error


def summary(group_name, now=None):
    """
    The worst level of the group's checks with its colour, and those that aren't ok, worst first, also as the
    indicator's title
    """
    now = now or timezone.now()
    worst, items = OK, []
    for check in watched().filter(operation__in=operations(group_name)).select_related('integration'):
        check_level = level(check, now)
        if check_level == OK:
            continue
        lines = status_text(check, now).splitlines()
        items.append({'name': name(check), 'level': check_level, 'error': lines[0][:200] if lines else ''})
        worst = max(worst, check_level, key=LEVELS.index)
    items.sort(key=lambda item: -LEVELS.index(item['level']))
    title = '\n'.join(f"{item['name']}: {item['error']}" for item in items)
    return {'level': worst, 'color': COLORS[worst], 'title': title or ALL_WELL[group_name], 'problems': items}


def _locked(integration, operation):
    check, created = HealthCheck.objects.get_or_create(integration_id=_pk(integration), operation=operation)
    if created:
        return check
    return HealthCheck.objects.select_for_update().get(pk=check.pk)


def _pk(integration):
    return getattr(integration, 'pk', integration)


def _notice(check, since):
    """ What a notice tells about a check, as Celery can pass it """
    return {
        'integration': check.integration_id, 'operation': check.operation, 'error': check.error,
        'failures': check.failures, 'since': since.isoformat() if since else None,
    }


def publish(group_name):
    """ Tells the open admin pages the group's state, see sewingworld/notifications.py """
    from sewingworld.notifications import publish_status
    publish_status('health', group=group_name, **summary(group_name))


def _publish_change(check, before):
    """ Publishes the check's group once the transaction commits, when its level changed """
    if level(check, timezone.now()) != before:
        transaction.on_commit(lambda: publish(group(check.operation)), robust=True)


def _queue(notices, raised):
    from shop.tasks.admin import notify_health  # the tasks import this module
    transaction.on_commit(lambda: notify_health.delay(notices, raised), robust=True)


def expect(integration, operation):
    """ Starts watching a scheduled operation, so that it goes stale even if it never succeeds """
    HealthCheck.objects.get_or_create(integration_id=_pk(integration), operation=operation)


def record_success(integration, operation, *, notify=True):
    """ Clears the check's failures. Returns the notice that a raised problem is gone, queued unless notify is off. """
    now = timezone.now()
    current = HealthCheck.objects.filter(integration_id=_pk(integration), operation=operation) \
        .values('failures', 'error', 'raised_at', 'last_success_at').first()
    if current and not current['failures'] and not current['error'] and current['raised_at'] is None \
            and current['last_success_at'] and now - current['last_success_at'] < SUCCESS_THROTTLE:
        return None
    with transaction.atomic():
        check = _locked(integration, operation)
        before = level(check, now)
        notice = None
        if check.raised_at is not None:
            notice = _notice(check, check.first_failed_at or check.last_success_at or check.raised_at)
        check.failures = 0
        check.error = ''
        check.first_failed_at = check.raised_at = None
        check.last_success_at = now
        check.save()
        _publish_change(check, before)
        if notice and notify:
            _queue([notice], raised=False)
    return notice


def record_failure(integration, operation, error, *, notify=True):
    """ Counts a failure. Returns the notice of the problem it raises, queued unless notify is off. """
    now = timezone.now()
    with transaction.atomic():
        check = _locked(integration, operation)
        before = level(check, now)
        check.failures += 1
        check.error = truncate(error)
        check.last_failed_at = now
        check.first_failed_at = check.first_failed_at or now
        notice = None
        if check.raised_at is None and check.failures >= max(1, config.sw_integration_failures):
            check.raised_at = now
            notice = _notice(check, check.first_failed_at)
        check.save()
        _publish_change(check, before)
        if notice and notify:
            _queue([notice], raised=True)
    return notice


def raise_problem(integration, operation, error, *, notify=True):
    """ Raises a problem at once. Returns its notice when it wasn't raised yet, queued unless notify is off. """
    now = timezone.now()
    with transaction.atomic():
        check = _locked(integration, operation)
        before = level(check, now)
        check.error = truncate(error)
        check.first_failed_at = check.first_failed_at or now
        notice = None
        if check.raised_at is None:
            check.raised_at = now
            notice = _notice(check, check.first_failed_at)
        check.save()
        _publish_change(check, before)
        if notice and notify:
            _queue([notice], raised=True)
    return notice


def warn(integration, operation, error):
    """ A warning, which takes back a problem raised earlier, such as for a token replaced with a shorter one """
    with transaction.atomic():
        check = _locked(integration, operation)
        before = level(check, timezone.now())
        check.error = truncate(error)
        check.first_failed_at = check.first_failed_at or timezone.now()
        check.raised_at = None
        check.save()
        _publish_change(check, before)


def _quietly(func, *args):
    """ Health records never break or mask a task's own outcome """
    try:
        func(*args)
    except Exception:
        logger.exception('Could not record the health of %s', args[1] if len(args) > 1 else 'an operation')


def _record_exception(integration, operation, exc):
    record_failure(integration, operation, describe(exc))


class Outcome:
    """ What monitor() gives: fail() counts a failure that raised nothing, such as errors in a reply of HTTP 200 """
    error = None

    def fail(self, error):
        self.error = error


@contextmanager
def monitor(integration, operation):
    """ Records the outcome of an exchange with an outside service, see the module's description """
    outcome = Outcome()
    try:
        yield outcome
    except (Retry, Ignore):
        raise
    except Exception as exc:
        _quietly(_record_exception, integration, operation, exc)
        raise
    else:
        if outcome.error:
            _quietly(record_failure, integration, operation, outcome.error)
        else:
            _quietly(record_success, integration, operation)


def raise_stale(now=None):
    """ Raises the checks that went stale, see stale_since(), and returns their notices to send """
    now = now or timezone.now()
    scheduled = [operation for operation, known in OPERATIONS.items() if known.max_age]
    notices = []
    for candidate in watched().filter(raised_at__isnull=True, operation__in=scheduled):
        if stale_since(candidate, now) is None:
            continue
        with transaction.atomic():
            check = HealthCheck.objects.select_for_update().get(pk=candidate.pk)
            since = stale_since(check, now)
            if check.raised_at is not None or since is None:
                continue
            check.raised_at = now
            error = stale_message(check, since)
            check.error = truncate(error + (f'\nПоследняя ошибка: {check.error}' if check.error else ''))
            check.save()
            notices.append(_notice(check, since))
    return notices


def send_heartbeats():
    """
    Sends a heartbeat through each queue, see QUEUES, without retrying when the broker doesn't take it. Returns the
    notice of a broker problem raised, or of one gone, as (raised, restored).
    """
    from shop.tasks.monitoring import heartbeat  # the tasks import this module

    try:
        for queue, max_age in QUEUES.items():
            # One that waits longer than the queue may doesn't tell anything any more
            heartbeat.apply_async((queue,), queue=queue, expires=max_age.total_seconds(), retry=False)
    except Exception as exc:
        notice = raise_problem(None, BROKER, f'Брокер не принимает задачи: {describe(exc)}', notify=False)
        return [notice] if notice else [], []
    notice = record_success(None, BROKER, notify=False)
    return [], [notice] if notice else []


def check_beat(now=None):
    """ Raises a problem when no periodic task has run for BEAT_MAX_AGE; returns (raised, restored) as above """
    from django_celery_beat.models import PeriodicTask

    now = now or timezone.now()
    last = PeriodicTask.objects.filter(enabled=True, last_run_at__isnull=False).order_by('-last_run_at') \
        .values_list('last_run_at', flat=True).first()
    if last is None:
        return [], []
    if now - last > BEAT_MAX_AGE:
        when = date_format(timezone.localtime(last), 'd.m.Y H:i')
        notice = raise_problem(None, BEAT, f'Задачи по расписанию не запускались с {when}: celery_beat остановлен', notify=False)
        return [notice] if notice else [], []
    notice = record_success(None, BEAT, notify=False)
    return [], [notice] if notice else []


@sensitive_variables()
def token_expiry(token):
    """ The expiry of a JWT, read without verifying it, or None for a token that isn't one """
    try:
        payload = token.split('.')[1]
        claims = json.loads(base64.urlsafe_b64decode(payload + '=' * (-len(payload) % 4)))
        return datetime.fromtimestamp(int(claims['exp']), UTC)
    except (AttributeError, IndexError, KeyError, TypeError, ValueError, OverflowError, binascii.Error):
        return None


@sensitive_variables()
def check_tokens(now=None):
    """
    Checks the expiry of the Wildberries API tokens: a warning two weeks ahead, a problem three days ahead. Returns
    the notices of raised problems and of those that are gone, to send.
    """
    now = now or timezone.now()
    raised, restored = [], []
    for integration in Integration.objects.filter(source_site__domain='wildberries.ru', enabled=True):
        expiry = token_expiry((integration.settings or {}).get('api_key', ''))
        if expiry is None:
            continue
        left = expiry - now
        when = date_format(timezone.localtime(expiry), 'd.m.Y H:i')
        if left <= timedelta(0):
            message = f'Токен API истёк {when}. Выпустите новый в кабинете Wildberries и замените api_key в настройках интеграции.'
        else:
            message = f'Токен API истекает {when}. Выпустите новый в кабинете Wildberries и замените api_key в настройках интеграции.'
        if left < TOKEN_PROBLEM:
            notice = raise_problem(integration, TOKEN, message, notify=False)
            if notice:
                raised.append(notice)
        elif left < TOKEN_WARNING:
            warn(integration, TOKEN, message)
        else:
            notice = record_success(integration, TOKEN, notify=False)
            if notice:
                restored.append(notice)
    return raised, restored


def _manager_emails(site):
    profile = getattr(site, 'profile', None)
    return profile.manager_emails if profile is not None else ''


class Notice(NamedTuple):
    subject: str
    telegram: str
    mail: str
    recipients: list


def render_notice(notices, raised):
    """
    The texts of a notice about raised problems, or about their end, and who gets its mail: the managers of the
    integrations' channels, and of the main site for those without a channel or an integration
    """
    from shop.tasks.common import get_default_site  # the tasks import this module

    integrations = Integration.objects.select_related('source_site__profile', 'target_site').in_bulk(
        {notice['integration'] for notice in notices if notice['integration'] is not None})
    items = []
    for notice in notices:
        integration = None
        if notice['integration'] is not None:
            integration = integrations.get(notice['integration'])
            if integration is None:
                continue
        since = datetime.fromisoformat(notice['since']) if notice.get('since') else None
        items.append({
            'integration': integration,
            'label': label(notice['operation']),
            'error': notice.get('error', ''),
            'failures': notice.get('failures', 0),
            'since': since,
        })

    recipients = set()
    for item in items:
        emails = _manager_emails(item['integration'].source_site) if item['integration'] else ''
        if not emails:
            try:
                emails = _manager_emails(get_default_site())
            except Site.DoesNotExist:
                pass
        recipients.update(email.strip() for email in emails.split(',') if email.strip())

    if len(items) == 1:
        item = items[0]
        subject = f'{item["integration"]}, {item["label"]}' if item['integration'] else item['label']
        subject = f'Сбой: {subject}' if raised else f'Восстановлено: {subject}'
    else:
        subject = f'Сбои ({len(items)})' if raised else f'Восстановлено ({len(items)})'
    context = {'items': items, 'raised': raised, 'now': timezone.now()}
    return Notice(
        subject,
        render_to_string('telegram/health.txt', context),
        render_to_string('mail/shop/health.txt', context),
        sorted(recipients),
    )


def deliver(notices, raised):
    """
    Sends a notice right away, without Celery, for the check_health command. Returns whether at least one of the
    channels took it.
    """
    from sewingworld.telegram import send_message

    if not notices:
        return True
    notice = render_notice(notices, raised)
    delivered = False
    if notice.recipients:
        try:
            send_mail(notice.subject, notice.mail, config.sw_email_from, notice.recipients)
            delivered = True
        except Exception:
            logger.exception('Could not mail a health notice')
    try:
        send_message(notice.telegram)
        delivered = True
    except Exception:
        logger.exception('Could not post a health notice')
    return delivered
