from datetime import timedelta
from importlib.util import find_spec
from unittest import skipIf

from django.conf import settings
from django.test import Client, TestCase, override_settings
from django.utils import timezone

from errors.models import Error, ErrorTrace
from errors.recorder import record

try:
    from celery import shared_task
except ImportError:  # Celery is optional
    shared_task = None

MASK = '********************'
WITHOUT_DRF = find_spec('rest_framework') is None

if shared_task is not None:
    @shared_task
    def failing_task(order_id, password):
        raise RuntimeError(f'no order {order_id}')


def frame_vars(trace, function):
    frame = next(frame for frame in trace.frames if frame['function'] == function)
    return dict(frame['vars'])


@override_settings(ROOT_URLCONF='errors.tests.urls')
class RequestErrorTests(TestCase):
    def setUp(self):
        self.client = Client(raise_request_exception=False)

    def test_same_error_at_same_place_is_one_group(self):
        self.assertEqual(self.client.get('/boom/?n=1').status_code, 500)
        self.assertEqual(self.client.get('/boom/?n=2').status_code, 500)

        error = Error.objects.get()
        self.assertEqual(error.kind, Error.Kind.REQUEST)
        self.assertEqual(error.name, 'ValueError')
        self.assertEqual(error.message, 'bad 2')
        self.assertEqual(error.source, 'GET boom')
        self.assertEqual(error.location, 'errors/tests/urls.py in boom')
        self.assertEqual(error.count, 2)
        self.assertLess(error.first_seen, error.last_seen)
        self.assertEqual([trace.message for trace in error.traces.all()], ['bad 2', 'bad 1'])
        trace = error.traces.first()
        self.assertIn('raise ValueError', trace.traceback)
        self.assertEqual(trace.context['query'], {'n': '2'})
        self.assertEqual(trace.context['status'], 500)
        self.assertEqual(trace.context['view'], 'errors.tests.urls.boom')

    def test_other_place_or_method_is_another_group(self):
        self.client.get('/boom/')
        self.client.get('/other/')
        self.client.post('/boom/')

        self.assertEqual(
            sorted(Error.objects.values_list('source', 'location')),
            [
                ('GET boom', 'errors/tests/urls.py in boom'),
                ('GET other', 'errors/tests/urls.py in other_boom'),
                ('POST boom', 'errors/tests/urls.py in boom'),
            ],
        )

    def test_5xx_response_without_exception(self):
        self.client.get('/unavailable/')

        error = Error.objects.get()
        self.assertEqual((error.name, error.message, error.location), ('HTTP 503', 'Service Unavailable', ''))
        self.assertEqual(error.traces.get().frames, [])

    def test_4xx_are_not_recorded(self):
        self.assertEqual(self.client.get('/missing/').status_code, 404)
        self.assertEqual(self.client.get('/bad/').status_code, 400)
        self.assertEqual(self.client.get('/nowhere/').status_code, 404)

        self.assertFalse(Error.objects.exists())

    def test_exception_in_middleware(self):
        middleware = list(settings.MIDDLEWARE)
        middleware.insert(middleware.index('errors.middleware.ErrorCaptureMiddleware') + 1, 'errors.tests.urls.FailingMiddleware')
        with self.settings(MIDDLEWARE=middleware):
            self.assertEqual(self.client.get('/middleware/').status_code, 500)

        error = Error.objects.get()
        self.assertEqual(error.name, 'RuntimeError')
        self.assertEqual(error.source, 'GET middleware')  # resolved, though the view was never reached
        self.assertEqual(error.location, 'errors/tests/urls.py in FailingMiddleware.__call__')
        self.assertIn('middleware failed', error.traces.get().traceback)

    def test_locals(self):
        self.client.get('/boom/?n=1&token=qwerty-token&password=hunter2')

        trace = ErrorTrace.objects.get()
        self.assertEqual(trace.context['query'], {'n': '1', 'token': MASK, 'password': MASK})
        frame = next(frame for frame in trace.frames if frame['function'] == 'boom')
        self.assertTrue(frame['in_app'])
        self.assertIn([frame['lineno'], "    raise ValueError(f\"bad {request.GET.get('n')}\")"], frame['lines'])
        variables = dict(frame['vars'])
        self.assertEqual(variables['password'], MASK)
        self.assertEqual(variables['data'], f"{{'name': 'Ann', 'token': '{MASK}'}}")
        self.assertEqual(variables['pending'], '<QuerySet of Error, not evaluated>')
        self.assertTrue(variables['long_text'].startswith("'xxx"))
        self.assertTrue(variables['long_text'].endswith('<trimmed 5002 bytes string>'))
        self.assertEqual(variables['request'], "<WSGIRequest: GET '/boom/'>")
        self.assertFalse(next(frame for frame in trace.frames if frame['file'].startswith('django/'))['in_app'])
        self.assertNotIn('qwerty-token', str(trace.frames))
        self.assertNotIn('hunter2', str(trace.frames))

    def test_sensitive_variables_hide_called_frames_too(self):
        self.client.get('/secret/')

        trace = ErrorTrace.objects.get()
        self.assertEqual(frame_vars(trace, 'secret'), {'code': MASK, 'request': MASK})
        self.assertEqual(frame_vars(trace, 'send_code'), {'code': MASK, 'text': MASK})
        self.assertNotIn('1234', str(trace.frames))

    @skipIf(WITHOUT_DRF, 'Django REST framework is not installed')
    def test_drf_view(self):
        self.client.get('/api/boom/?token=qwerty-token')

        error = Error.objects.get()
        self.assertEqual((error.name, error.source), ('KeyError', 'GET api-boom'))
        self.assertEqual(error.location, 'errors/tests/urls.py in ApiBoom.get')
        self.assertEqual(frame_vars(error.traces.get(), 'get')['request'], "<Request: GET '/api/boom/'>")

    @skipIf(WITHOUT_DRF, 'Django REST framework is not installed')
    def test_drf_api_exception(self):
        self.assertEqual(self.client.get('/api/handled/').status_code, 500)

        error = Error.objects.get()
        self.assertEqual((error.name, error.message, error.source), ('HTTP 500', 'no such model', 'GET api-handled'))


@skipIf(shared_task is None, 'Celery is not installed')
class TaskErrorTests(TestCase):
    def test_failed_task(self):
        failing_task.apply(args=(5, 'hunter2'))

        error = Error.objects.get()
        self.assertEqual(error.kind, Error.Kind.TASK)
        self.assertEqual(error.name, 'RuntimeError')
        self.assertEqual(error.source, 'errors.tests.test_recording.failing_task')
        self.assertEqual(error.location, 'errors/tests/test_recording.py in failing_task')
        trace = error.traces.get()
        self.assertEqual(trace.message, 'no order 5')
        self.assertEqual(set(trace.context), {'task_id', 'retries', 'hostname'})
        self.assertEqual(frame_vars(trace, 'failing_task'), {'order_id': '5', 'password': MASK})


class RecordTests(TestCase):
    @override_settings(ERRORS_MAX_TRACES=3)
    def test_only_latest_traces_are_kept(self):
        for n in range(5):
            record(Error.Kind.TASK, 'task', 'ValueError', f'bad {n}', 'here.py in f')

        error = Error.objects.get()
        self.assertEqual(error.count, 5)
        self.assertEqual([trace.message for trace in error.traces.all()], ['bad 4', 'bad 3', 'bad 2'])

    def test_nul_is_escaped(self):
        record(Error.Kind.REQUEST, 'GET boom', 'ValueError', 'bad \x00', context={'query': {'q': '\x00'}})

        trace = ErrorTrace.objects.get()
        self.assertEqual((trace.message, trace.context['query']['q']), ('bad \\x00', '\\x00'))

    def test_frequency_per_day(self):
        now = timezone.now()
        self.assertAlmostEqual(Error(count=10, first_seen=now - timedelta(days=2)).frequency, 5, places=3)
        self.assertEqual(Error(count=3, first_seen=now - timedelta(hours=1)).frequency, 3)
