import logging
import sys
import traceback

from urllib.parse import urlparse

from django.contrib.sites.models import Site
from django.db.models import Q


logger = logging.getLogger("django")


class SiteDetectionMiddleware:
    """
    This logic is used in Rest API
    TODO: accommodate it to general use
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        logger.error("Origin: " + request.META.get('HTTP_ORIGIN', ''))
        logger.error("Referer: " + request.META.get('HTTP_REFERER', ''))
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
        logger.error(site)
        response = self.get_response(request)
        return response


class ProcessExceptionMiddleware(object):
    def process_exception(self, request, exception):
        print('\n'.join(traceback.format_exception(*sys.exc_info())), file=sys.stderr)
        return None
