import json
import logging
from urllib.request import Request, urlopen
from urllib.error import HTTPError

from django.conf import settings
from django.core.management.base import BaseCommand

from shop.models import Order

logger = logging.getLogger(__name__)


order_types = {
    'PAID': [
        Order.STATUS_DONE,
        Order.STATUS_FINISHED
    ],
    'CANCELLED': [
        Order.STATUS_CANCELED,
        Order.STATUS_UNCLAIMED
    ]
}


def status_mapping(status):
    (id, name) = status
    ym_type = 'IN_PROGRESS'
    for t, statuses in order_types.items():
        if id in statuses:
            ym_type = t

    return {
        "id": str(id),
        "humanized": name,
        "type": ym_type
    }


class Command(BaseCommand):
    help = 'Upload order status mappings to Yandex Metrika'

    def handle(self, *args, **options):
        data = {
            "order_statuses": list(map(status_mapping, Order.STATUS_CHOICES))
        }
        data_encoded = json.dumps(data).encode('utf-8')
        self.stdout.write(str(data))
        url = 'https://api-metrika.yandex.net/cdp/api/v1/counter/{counterId}/schema/order_statuses'.format(counterId=settings.YM_COUNTER_ID)
        headers = {
            'Authorization': 'OAuth {oauth_token}'.format(oauth_token=settings.YM_API_TOKEN),
            'Content-Type': 'application/json; charset=utf-8'
        }
        request = Request(url, data_encoded, headers, method='POST')
        logger.info('<<< ' + request.full_url)
        logger.info(data_encoded)
        try:
            response = urlopen(request)
            result = json.loads(response.read().decode('utf-8'))
            self.stdout.write(str(result))
        except HTTPError as e:
            content = e.read()
            logger.error(content)
            self.stdout.write(str(content))
