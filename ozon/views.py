import json
import logging
from ipaddress import ip_address, ip_network

from django.http import JsonResponse
from django.utils import timezone
from django.utils.crypto import constant_time_compare
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.debug import sensitive_variables
from django.views.decorators.http import require_POST
from kombu.exceptions import OperationalError

from shop.models import Integration, Order

from .tasks import sync_integration_posting


logger = logging.getLogger('ozon')

# Sender ranges published in the Seller API push notification setup guide.
OZON_NETWORKS = tuple(map(ip_network, ('195.34.21.0/24', '185.73.192.0/22', '91.223.93.0/24')))
POSTING_EVENTS = {
    'TYPE_NEW_POSTING',
    'TYPE_POSTING_CANCELLED',
    'TYPE_STATE_CHANGED',
    'TYPE_CUTOFF_DATE_CHANGED',
    'TYPE_DELIVERY_DATE_CHANGED',
}


def _error(status, message, *, code='ERROR_UNKNOWN'):
    return JsonResponse({'error': {'code': code, 'message': message, 'details': None}}, status=status)


@csrf_exempt
@require_POST
@sensitive_variables()
def notifications(request, integration_id):
    received_at = timezone.now()
    try:
        sender = ip_address(request.META.get('REMOTE_ADDR', ''))
    except ValueError:
        return _error(403, 'Forbidden')
    if not any(sender in network for network in OZON_NETWORKS):
        return _error(403, 'Forbidden')

    integration = Integration.objects.filter(pk=integration_id, source_site__domain='ozon.ru', enabled=True).only('settings').first()
    token = (integration.settings or {}).get('push_token') if integration else None
    if not isinstance(token, str) or not token or not constant_time_compare(request.GET.get('token', ''), token):
        return _error(403, 'Forbidden')

    try:
        data = json.loads(request.body)
    except ValueError:
        return _error(400, 'Invalid JSON')
    message_type = data.get('message_type') if isinstance(data, dict) else None
    if not isinstance(message_type, str) or not message_type:
        return _error(400, 'Invalid message_type', code='ERROR_PARAMETER_VALUE_MISSED')
    if message_type == 'TYPE_PING':
        return JsonResponse({'version': '1.0', 'name': 'Sewing World', 'time': received_at.isoformat().replace('+00:00', 'Z')})

    if message_type in POSTING_EVENTS:
        posting_number = data.get('posting_number')
        if (not isinstance(posting_number, str) or not posting_number or not posting_number.isprintable()
                or len(posting_number) > Order._meta.get_field('delivery_tracking_number').max_length
                or posting_number != posting_number.strip()):
            return _error(400, 'Invalid posting_number', code='ERROR_PARAMETER_VALUE_MISSED')
        try:
            sync_integration_posting.apply_async((integration_id, posting_number), retry=False)
        except OperationalError:
            logger.error('Could not queue Ozon posting sync for integration %s', integration_id)
            return _error(503, 'Could not queue notification')

    return JsonResponse({'result': True})
