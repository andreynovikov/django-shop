import logging
import sys
import traceback

from urllib.parse import urlparse

from django.conf import settings
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


class CookieRenameMiddleware:
    """
    Moves visitors to new SESSION_COOKIE_NAME and CSRF_COOKIE_NAME without signing them out. A cookie under its
    Django default name is read under the new one, and the response sets it under the new name and deletes the old.
    Comes before SessionMiddleware. Remove it once SESSION_COOKIE_AGE has passed since the rename.
    """
    def __init__(self, get_response):
        self.get_response = get_response
        session = {
            'max_age': None if settings.SESSION_EXPIRE_AT_BROWSER_CLOSE else settings.SESSION_COOKIE_AGE,
            'path': settings.SESSION_COOKIE_PATH,
            'domain': settings.SESSION_COOKIE_DOMAIN,
            'secure': settings.SESSION_COOKIE_SECURE,
            'httponly': settings.SESSION_COOKIE_HTTPONLY,
            'samesite': settings.SESSION_COOKIE_SAMESITE,
        }
        csrf = {
            'max_age': settings.CSRF_COOKIE_AGE,
            'path': settings.CSRF_COOKIE_PATH,
            'domain': settings.CSRF_COOKIE_DOMAIN,
            'secure': settings.CSRF_COOKIE_SECURE,
            'httponly': settings.CSRF_COOKIE_HTTPONLY,
            'samesite': settings.CSRF_COOKIE_SAMESITE,
        }
        self.renames = [
            (old, new, options)
            for old, new, options in (
                ('sessionid', settings.SESSION_COOKIE_NAME, session),
                ('csrftoken', settings.CSRF_COOKIE_NAME, csrf),
            )
            if old != new
        ]
        if not self.renames:
            raise MiddlewareNotUsed()

    def __call__(self, request):
        moved = set()
        for old, new, _ in self.renames:
            if old in request.COOKIES and new not in request.COOKIES:
                request.COOKIES[new] = request.COOKIES[old]
                moved.add(new)

        response = self.get_response(request)

        for old, new, options in self.renames:
            if old not in request.COOKIES:
                continue
            # The session and CSRF middlewares set or delete the cookie themselves when the request changed it
            if new in moved and new not in response.cookies:
                response.set_cookie(new, request.COOKIES[new], **options)
            response.delete_cookie(old, path=options['path'], domain=options['domain'])
        return response


class BlockedIpMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.BLOCKED_IPS = getattr(settings, 'BLOCKED_IPS', None)
        if self.BLOCKED_IPS is None:
            raise MiddlewareNotUsed()

    def __call__(self, request):
        if request.META.get('REMOTE_ADDR') in self.BLOCKED_IPS:
            return HttpResponseForbidden()
        return self.get_response(request)


class ProcessExceptionMiddleware(object):
    def process_exception(self, request, exception):
        print('\n'.join(traceback.format_exception(*sys.exc_info())), file=sys.stderr)
        return None
