"""
Views that fail in different ways, and the admin to render errors in
"""
from django.contrib import admin
from django.core.exceptions import BadRequest
from django.http import Http404, HttpResponse
from django.urls import path
from django.views.decorators.debug import sensitive_variables

from errors.models import Error

try:
    from rest_framework.exceptions import APIException
    from rest_framework.views import APIView
except ImportError:  # Django REST framework is optional
    APIView = None


def boom(request):
    password = request.GET.get('password')  # noqa: F841, the locals are what the tests look at
    data = {'name': 'Ann', 'token': 'abc'}  # noqa: F841
    pending = Error.objects.filter(name='never')  # noqa: F841
    long_text = 'x' * 5000  # noqa: F841
    raise ValueError(f"bad {request.GET.get('n')}")


def other_boom(request):
    raise ValueError('bad')


def unavailable(request):
    return HttpResponse('down', status=503)


def missing(request):
    raise Http404()


def bad_request(request):
    raise BadRequest()


def send_code(code):
    text = f'code {code}'  # noqa: F841
    raise ConnectionError('gateway is down')


@sensitive_variables()
def secret(request):
    code = str(1000 + 234)
    send_code(code)


class FailingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path == '/middleware/':
            raise RuntimeError('middleware failed')
        return self.get_response(request)


urlpatterns = [
    path('boom/', boom, name='boom'),
    path('other/', other_boom, name='other'),
    path('unavailable/', unavailable, name='unavailable'),
    path('missing/', missing, name='missing'),
    path('bad/', bad_request, name='bad'),
    path('secret/', secret, name='secret'),
    path('middleware/', unavailable, name='middleware'),
    path('admin/', admin.site.urls),
]

if APIView is not None:
    class ApiBoom(APIView):
        authentication_classes = []
        permission_classes = []

        def get(self, request):
            raise KeyError(request.query_params.get('n'))

    class ApiHandled(ApiBoom):
        def get(self, request):
            raise APIException('no such model')

    urlpatterns += [
        path('api/boom/', ApiBoom.as_view(), name='api-boom'),
        path('api/handled/', ApiHandled.as_view(), name='api-handled'),
    ]
