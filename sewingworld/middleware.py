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
