import logging
from decimal import Decimal, ROUND_HALF_EVEN

from django.db import Error as DatabaseError

from celery import shared_task

from yookassa import Receipt

from shop.models import Order
from shop.tasks import update_order

from . import configure_yookassa

logger = logging.getLogger('yandex_kassa')


@shared_task(bind=True, autoretry_for=(EnvironmentError, DatabaseError), retry_backoff=60, retry_jitter=False)
def get_receipt(self, order_id, payment_id):
    order = Order.objects.get(id=order_id)

    configure_yookassa(order)

    receipts = Receipt.list({'payment_id': payment_id})

    if not receipts.items:
        raise self.retry(countdown=3600, max_retries=12)  # 1 hour

    receipt = receipts.items[0]

    if receipt.receipt_registration != 'succeeded':
        raise self.retry(countdown=3600, max_retries=12)  # 1 hour

    total = Decimal('0')
    for item in receipt.items:
        total = total + item.quantity * item.amount.value

    fiscalInfo = {
        'providerId': receipt.fiscal_provider_id,
        'fnNumber': receipt.fiscal_storage_number,
        'date': receipt.registered_at,
        'checkType': receipt.type,
        'fnDocMark': receipt.fiscal_attribute,
        'sum': int(total.quantize(Decimal('1'), rounding=ROUND_HALF_EVEN)),
        'fnDocNumber': receipt.fiscal_document_number,
        'registration': receipt.receipt_registration
    }
    update_order.delay(order.pk, {'meta': {'fiscalInfo': fiscalInfo}})
    return receipt.fiscal_attribute
