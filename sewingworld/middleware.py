import logging
import re
import sys
import traceback

from importlib import import_module
from urllib.parse import urlparse

from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.sites.models import Site
from django.core.exceptions import MiddlewareNotUsed
from django.db.models import Q
from django.http import HttpResponseForbidden


logger = logging.getLogger("django")


class SiteDetectionMiddleware:
    """
    This logic is used in Rest API
    TODO: accommodate it to general use
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        site = None
        # Prefer Origin header over Referer
        url = request.META.get('HTTP_ORIGIN', request.META.get('HTTP_REFERER', ''))
        if url != '':
            try:
                domain = urlparse(url).hostname
                if domain:
                    site = Site.objects.filter(Q(domain=domain) | Q(profile__aliases__contains=[domain])).first()
            except ValueError:
                pass
        if site is None:
            site = Site.objects.get_current()
        request.site = site
        response = self.get_response(request)
        return response


class SessionCookieMiddleware:
    """
    Fallback middleware when cookies are blocked or broken
    (e.g. https://www.chromium.org/updates/same-site/incompatible-clients/)
    Should be called *after* Django session middleware
    """
    def __init__(self, get_response):
        self.get_response = get_response
        engine = import_module(settings.SESSION_ENGINE)
        self.SessionStore = engine.SessionStore

    def __call__(self, request):
        if 'X-Session' in request.headers and not settings.SESSION_COOKIE_NAME in request.COOKIES:  # skip if cookie is available
            session_key = request.headers.get('X-Session')
            request.session = self.SessionStore(session_key)

        response = self.get_response(request)

        try:
            empty = request.session.is_empty()
        except AttributeError:
            return response

        if response.status_code != 500:
            if not empty:
                response['X-Session'] = request.session.session_key
            elif 'X-Session' in request.headers:
                # response['X-Session'] = ''  # clean empty session
                pass  # TODO: fix logout and basket request, it should be delayed
        return response


class CsrfCookieMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if settings.CSRF_HEADER_NAME in request.META and not settings.CSRF_COOKIE_NAME in request.COOKIES:
            request.COOKIES[settings.CSRF_COOKIE_NAME] = request.META.get(settings.CSRF_HEADER_NAME)

        response = self.get_response(request)
        return response


class BlockedIpMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.BLOCKED_IPS = getattr(settings, 'BLOCKED_IPS', None)
        if self.BLOCKED_IPS is None:
            return MiddlewareNotUsed()

    def __call__(self, request):
        if request.META.get('REMOTE_ADDR') in self.BLOCKED_IPS:
            return HttpResponseForbidden()
        return self.get_response(request)


class ProcessExceptionMiddleware(object):
    def process_exception(self, request, exception):
        print('\n'.join(traceback.format_exception(*sys.exc_info())), file=sys.stderr)
        return None


class RequireStaffMiddleware(object):
    """
    Middleware component that wraps the staff_member_required decorator around
    matching URL patterns. To use, add the class to MIDDLEWARE_CLASSES and
    define STAFF_REQUIRED_URLS and STAFF_REQUIRED_URLS_EXCEPTIONS in your
    settings.py. For example:
    ------
    STAFF_REQUIRED_URLS = (
        r'/topsecret/(.*)$',
    )
    STAFF_REQUIRED_URLS_EXCEPTIONS = (
        r'/topsecret/login(.*)$',
        r'/topsecret/logout(.*)$',
    )
    ------
    STAFF_REQUIRED_URLS is where you define URL patterns; each pattern must
    be a valid regex.

    STAFF_REQUIRED_URLS_EXCEPTIONS is, conversely, where you explicitly
    define any exceptions (like login and logout URLs).
    """
    def __init__(self, get_response):
        self.get_response = get_response
        self.STAFF_REQUIRED_URLS = getattr(settings, 'STAFF_REQUIRED_URLS', None)
        if self.STAFF_REQUIRED_URLS is None:
            return MiddlewareNotUsed()
        self.STAFF_REQUIRED_URLS_EXCEPTIONS = getattr(settings, 'STAFF_REQUIRED_URLS_EXCEPTIONS', ())
        self.required = tuple([re.compile(url) for url in self.STAFF_REQUIRED_URLS])
        self.exceptions = tuple([re.compile(url) for url in self.STAFF_REQUIRED_URLS_EXCEPTIONS])

    def __call__(self, request):
        return self.get_response(request)

    def process_view(self,request,view_func,view_args,view_kwargs):
        # No need to process URLs if user already logged in
        if request.user.is_authenticated: return None
        # An exception match should immediately return None
        for url in self.exceptions:
            if url.match(request.path): return None
        # Requests matching a restricted URL pattern are returned
        # wrapped with the login_required decorator
        for url in self.required:
            if url.match(request.path): return staff_member_required(view_func)(request,*view_args,**view_kwargs)
        # Explicitly return None for all non-matching requests
        return None
