from .recorder import record_request

EXCEPTION_ATTRIBUTE = '_error_exception'


def remember_exception(request, exception, replace=True):
    if replace or getattr(request, EXCEPTION_ATTRIBUTE, None) is None:
        setattr(request, EXCEPTION_ATTRIBUTE, exception)


class ErrorCaptureMiddleware:
    """
    Records responses with 5xx status into errors.Error. Comes first, so that it also sees the 500 Django makes of an
    exception in another middleware. The exception of a view is taken in process_exception, the one of a middleware
    in the got_request_exception receiver, see signals.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        # popped in any case, the exception's frames refer to the request
        exception = request.__dict__.pop(EXCEPTION_ATTRIBUTE, None)
        if response.status_code >= 500:
            record_request(request, response, exception)
        return response

    def process_exception(self, request, exception):
        remember_exception(request, exception)
        return None
