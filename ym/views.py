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

from shop.models import Integration

from .tasks import _positive_id, sync_integration_order


logger = logging.getLogger('ym')

# Sender ranges published in the Market API notification setup guide.
MARKET_NETWORKS = tuple(map(ip_network, ('5.45.207.0/25', '141.8.142.0/25', '5.255.253.0/25')))
ORDER_EVENTS = {'ORDER_CREATED', 'ORDER_CANCELLED', 'ORDER_STATUS_UPDATED', 'ORDER_UPDATED'}


def _error(status, error_type, message):
    return JsonResponse({'error': {'type': error_type, 'message': message}}, status=status)


# Yandex.Market notifications, accepted as Ozon's are (see ozon.views.notifications): from the Market's networks,
# with the integration's push_token. An order event of the integration's campaign queues a sync of that order.
@csrf_exempt
@require_POST
@sensitive_variables()
def notification(request, integration_id):
    received_at = timezone.now()
    try:
        sender = ip_address(request.META.get('REMOTE_ADDR', ''))
    except ValueError:
        return _error(403, 'UNKNOWN', 'Forbidden')
    if not any(sender in network for network in MARKET_NETWORKS):
        return _error(403, 'UNKNOWN', 'Forbidden')

    integration = Integration.objects.filter(pk=integration_id, enabled=True, uses_api=True).only('settings').first()
    market_settings = (integration.settings or {}) if integration else {}
    campaign_id = _positive_id(market_settings.get('ym_campaign'))
    token = market_settings.get('push_token')
    if campaign_id is None or not isinstance(token, str) or not token or not constant_time_compare(request.GET.get('token', ''), token):
        return _error(403, 'UNKNOWN', 'Forbidden')

    try:
        data = json.loads(request.body)
    except ValueError:
        return _error(400, 'WRONG_EVENT_FORMAT', 'Invalid JSON')
    event = data.get('notificationType') if isinstance(data, dict) else None
    if not isinstance(event, str) or not event:
        return _error(400, 'WRONG_EVENT_FORMAT', 'Invalid notificationType')

    if event in ORDER_EVENTS:
        order_id, event_campaign_id = data.get('orderId'), data.get('campaignId')
        if not all(type(value) is int and 0 < value < 2**63 for value in (order_id, event_campaign_id)):
            return _error(400, 'WRONG_EVENT_FORMAT', 'Invalid orderId or campaignId')
        if event_campaign_id == campaign_id:
            try:
                sync_integration_order.apply_async((integration_id, campaign_id, order_id), retry=False)
            except OperationalError:
                logger.error('Could not queue Yandex.Market order sync for integration %s', integration_id)
                return _error(500, 'UNKNOWN', 'Could not queue notification')

    return JsonResponse({'version': '1.0', 'name': 'Sewing World', 'time': received_at.isoformat().replace('+00:00', 'Z')})
