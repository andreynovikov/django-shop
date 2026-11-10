"""
Records server errors into Error groups with their latest ErrorTrace.

An error is grouped by its kind, exception class, source (view or task) and location: the innermost frame of the
project code, without the line number. Messages, parameters and the rest of the stack may differ within a group.
Project code is any code outside the standard library and installed packages.

Recording never raises: a failure is logged, the response or the task goes on as it would without it.
"""
import hashlib
import logging
import os
import sys
import sysconfig
import traceback

from django.conf import settings
from django.db import transaction
from django.db.models import F, QuerySet
from django.http import HttpRequest
from django.template.defaultfilters import pprint
from django.urls import resolve
from django.utils import timezone
from django.utils.functional import LazyObject, empty
from django.views.debug import ExceptionReporter, get_exception_reporter_filter

from .models import Error, ErrorTrace

try:
    from rest_framework.request import Request
    REQUEST_CLASSES = (HttpRequest, Request)
except ImportError:  # Django REST framework is optional
    REQUEST_CLASSES = (HttpRequest,)

logger = logging.getLogger(__name__)

MAX_TRACES = 10  # per error by default, see ERRORS_MAX_TRACES; with the locals a trace takes tens of kilobytes
MAX_MESSAGE_LENGTH = 10000
MAX_VALUE_LENGTH = 4096  # of a variable, as on the debug page
LIBRARY_DIRS = tuple(f'{os.sep}{name}{os.sep}' for name in ('site-packages', 'dist-packages'))
STDLIB_DIRS = tuple({os.path.join(sysconfig.get_path(name), '') for name in ('stdlib', 'platstdlib')})


def record_request(request, response, exception=None):
    """ Records a response with 5xx status, and the exception it was made of if there was one """
    try:
        if exception is not None:
            details = describe_exception(exception, exception.__traceback__, request)
        else:
            # such as an APIException, which DRF turns into a response itself
            data = getattr(response, 'data', None)
            message = str(data['detail']) if isinstance(data, dict) and 'detail' in data else response.reason_phrase
            details = {'name': f'HTTP {response.status_code}', 'message': message}
        record(Error.Kind.REQUEST, request_source(request), context=request_context(request, response), **details)
    except Exception:
        logger.exception('Could not record the error of %s %s', request.method, request.path)


def record_task(task, task_id, exception, tb):
    """ Records a Celery task that failed. Its arguments are in the locals of its frame. """
    try:
        request = getattr(task, 'request', None)
        context = {
            'task_id': task_id,
            'retries': getattr(request, 'retries', None),
            'hostname': getattr(request, 'hostname', None),
        }
        record(Error.Kind.TASK, task.name, context=context, **describe_exception(exception, tb))
    except Exception:
        logger.exception('Could not record the failure of task %s', task_id)


def record(kind, source, name, message='', location='', traceback_text='', frames=(), context=None):
    message = message[:MAX_MESSAGE_LENGTH]
    name, source, location = name[:255], source[:255], location[:255]
    fingerprint = hashlib.sha256('\n'.join((kind, name, source, location)).encode()).hexdigest()
    now = timezone.now()
    with transaction.atomic():
        error, created = Error.objects.get_or_create(fingerprint=fingerprint, defaults={
            'kind': kind, 'name': name, 'message': without_nul(message), 'source': source, 'location': location,
            'first_seen': now, 'last_seen': now,
        })
        if not created:
            Error.objects.filter(pk=error.pk).update(count=F('count') + 1, last_seen=now, message=without_nul(message))
        ErrorTrace.objects.create(
            error=error, created=now, message=without_nul(message), traceback=without_nul(traceback_text),
            frames=without_nul(list(frames)), context=without_nul(context or {}),
        )
        limit = getattr(settings, 'ERRORS_MAX_TRACES', MAX_TRACES)
        stale = error.traces.order_by('-created', '-pk').values_list('pk', flat=True)[limit:]
        ErrorTrace.objects.filter(pk__in=list(stale)).delete()
    return error


def describe_exception(exception, tb, request=None):
    try:
        message = str(exception)
    except Exception:
        message = '<message not available>'
    return {
        'name': exception_name(exception),
        'message': message,
        'location': find_location(tb),
        'traceback_text': ''.join(traceback.format_exception(type(exception), exception, tb)),
        'frames': collect_frames(exception, tb, request),
    }


def exception_name(exception):
    cls = type(exception)
    return cls.__qualname__ if cls.__module__ == 'builtins' else f'{cls.__module__}.{cls.__qualname__}'


def find_location(tb):
    """ The innermost frame of the project code, or the innermost one if the project has none """
    frames = [frame for frame, _ in traceback.walk_tb(tb)]
    if not frames:
        return ''
    frame = ([frame for frame in frames if is_project_file(frame.f_code.co_filename)] or frames)[-1]
    return f'{short_path(frame.f_code.co_filename)} in {frame.f_code.co_qualname}'


def is_project_file(filename):
    """ Not of the standard library or an installed package. A virtualenv may lie inside the project. """
    return (
        not filename.startswith('<')  # such as <frozen importlib._bootstrap>
        and not filename.startswith(STDLIB_DIRS)
        and not any(name in filename for name in LIBRARY_DIRS)
    )


def short_path(filename):
    """ Relative to the sys.path entry it is imported from: shop/models.py, django/views/debug.py """
    roots = [os.path.join(os.path.abspath(entry), '') for entry in sys.path if isinstance(entry, str)]
    root = max((root for root in roots if filename.startswith(root)), key=len, default='')
    return filename[len(root):]


def collect_frames(exception, tb, request=None):
    """
    The frames of the exception and its causes, as on Django's debug page. ExceptionReporter takes care of
    @sensitive_variables and request.POST, names that look sensitive, such as password or token, are masked here.
    """
    reporter = ExceptionReporter(request, type(exception), exception, tb)
    frames = []
    for frame in reporter.get_traceback_frames():
        if frame.get('tb') is None:
            continue
        first = frame['pre_context_lineno']
        lines = frame['pre_context'] + [frame['context_line']] + frame['post_context']
        cause = frame['exc_cause']
        frames.append({
            'file': short_path(frame['filename']),
            'function': frame['function'],
            'lineno': frame['lineno'],
            'in_app': is_project_file(frame['filename']),
            'lines': [[first + index, line] for index, line in enumerate(lines)],
            'vars': [[name, format_value(reporter.filter, name, value)] for name, value in frame['vars']],
            'cause': f'{exception_name(cause)}: {cause}' if cause is not None else None,
            'cause_explicit': bool(frame['exc_cause_explicit']),
        })
    return frames


def format_value(reporter_filter, name, value):
    try:
        value = reporter_filter.cleanse_setting(name, value)
        if isinstance(value, str) and value == reporter_filter.cleansed_substitute:
            return value
        if isinstance(value, QuerySet) and value._result_cache is None:
            return f'<QuerySet of {value.model.__name__}, not evaluated>'
        if isinstance(value, REQUEST_CLASSES):
            # their repr has the query string, which may hold a token; the context has it masked
            return f'<{type(value).__name__}: {value.method} {value.path!r}>'
        text = pprint(value)
    except Exception as e:
        return f'Error in formatting: {e.__class__.__name__}: {e}'
    if len(text) > MAX_VALUE_LENGTH:
        text = '%s… <trimmed %d bytes string>' % (text[:MAX_VALUE_LENGTH], len(text))
    return text


def request_source(request):
    """ The method and the URL name, Django falls back to the view's dotted path for unnamed ones """
    match = resolver_match(request)
    return f'{request.method} {match.view_name if match is not None else request.path}'


def resolver_match(request):
    match = getattr(request, 'resolver_match', None)
    if match is None:  # the error came before the URL was resolved
        try:
            match = resolve(request.path_info, getattr(request, 'urlconf', None))
        except Exception:
            match = None
    return match


def request_context(request, response):
    match = resolver_match(request)
    reporter_filter = get_exception_reporter_filter(request)
    return {
        'method': request.method,
        'path': request.path,
        'query': {
            key: reporter_filter.cleanse_setting(key, values[0] if len(values) == 1 else values)
            for key, values in request.GET.lists()
        },
        'status': response.status_code,
        'view': match._func_path if match is not None else None,
        'route': match.route if match is not None else None,
        'site': getattr(getattr(request, 'site', None), 'domain', None),
        'user': user_id(request),
        'ip': request.META.get('REMOTE_ADDR'),
    }


def user_id(request):
    """ Only a user known by now, so that recording does not load the session """
    user = getattr(request, 'user', None)
    if isinstance(user, LazyObject):
        if user._wrapped is empty:
            return None
        user = user._wrapped
    return user.pk if getattr(user, 'is_authenticated', False) else None


def without_nul(value):
    """ PostgreSQL rejects NUL in text and JSON, and it comes in query strings of bots """
    if isinstance(value, str):
        return value.replace('\x00', '\\x00')
    if isinstance(value, dict):
        return {without_nul(key): without_nul(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [without_nul(item) for item in value]
    return value
