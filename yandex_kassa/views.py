import logging
import json
from decimal import Decimal, ROUND_HALF_EVEN

from django.conf import settings
from django.contrib.admin.models import LogEntry, CHANGE
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.encoding import force_text

from yandex_checkout import Configuration, Payment, WebhookNotification

import uuid

from shop.models import Order, ShopUser
from shop.tasks import update_order

KASSA_ACCOUNT_ID = getattr(settings, 'KASSA_ACCOUNT_ID', 0)
KASSA_SECRET_KEY = getattr(settings, 'KASSA_SECRET_KEY', '')

logger = logging.getLogger('yandex_kassa')

CANCELLATION_REASONS = {
    '3d_secure_failed': 'не пройдена аутентификация по 3-D Secure',
    'call_issuer': 'оплата данным платежным средством отклонена по неизвестным причинам',
    'card_expired': 'истек срок действия банковской карты',
    'country_forbidden': 'нельзя заплатить банковской картой, выпущенной в этой стране',
    'fraud_suspected': 'платеж заблокирован из-за подозрения в мошенничестве',
    'general_decline': 'причина не детализирована',
    'identification_required': 'превышены ограничения на платежи для кошелька в Яндекс.Деньгах',
    'insufficient_funds': 'не хватает денег для оплаты',
    'invalid_card_number': 'неправильно указан номер карты',
    'invalid_csc': 'неправильно указан код CVV2 (CVC2, CID)',
    'issuer_unavailable': 'организация, выпустившая платежное средство, недоступна',
    'payment_method_limit_exceeded': 'исчерпан лимит платежей для данного платежного средства или вашего магазина',
    'payment_method_restricted': 'запрещены операции данным платежным средством',
    'permission_revoked': 'нельзя провести безакцептное списание, пользователь отозвал разрешение на автоплатежи'
}


@login_required
def payment(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    if order.user.id != request.user.id:
        """ This is not the user's order, someone tries to hack us """
        return HttpResponseForbidden()

    Configuration.account_id = KASSA_ACCOUNT_ID
    Configuration.secret_key = KASSA_SECRET_KEY

    items = []
    for item in order.items.all():
        items.append({
            'description': str(item.product),
            'quantity': item.quantity,
            'amount': {
                'value': str(item.cost.quantize(Decimal('1'), rounding=ROUND_HALF_EVEN)),
                'currency': 'RUB'
            },
            'vat_code': 1
        })
    if order.delivery_price > 0:
        items.append({
            'description': "Доставка",
            'quantity': 1,
            'amount': {
                'value': str(order.delivery_price.quantize(Decimal('1'), rounding=ROUND_HALF_EVEN)),
                'currency': 'RUB'
            },
            'vat_code': 1
        })

    return_url = 'https://{}{}'.format(
        Site.objects.get_current().domain,
        reverse('shop:order', args=[order.id])
    )

    payment_details = {
        'amount': {
            'value': str(order.total.quantize(Decimal('1'), rounding=ROUND_HALF_EVEN)),
            'currency': 'RUB'
        },
        'receipt': {
            'customer': {
                'phone': order.phone,
                'full_name': order.name
            },
            'tax_system_code': 2,
            'items': items
        },
        'confirmation': {
            'type': 'redirect',
            'return_url': return_url
        },
        'metadata': {
            'order_id': order.id,
            'user_id': order.user.id
        },
        'description': 'Заказ №{}'.format(order.id)
    }
    if order.payment == order.PAYMENT_CREDIT:
        payment_details['payment_method_data'] = {'type': 'installments'}

    payment = Payment.create(payment_details, str(uuid.uuid4()))
    return HttpResponseRedirect(payment.confirmation.confirmation_url)


@require_POST
@csrf_exempt
def callback(request):
    if request.body:
        data = json.loads(request.body.decode('utf-8'))
    else:
        return HttpResponseForbidden()
    logger.debug(data)
    try:
        notification_object = WebhookNotification(data)
        payment = notification_object.object
        order = Order.objects.get(pk=int(payment.metadata.get('order_id', '-1')))
        user = ShopUser.objects.get(pk=int(payment.metadata.get('user_id', '-1')))
        if order.user.id != user.id:
            raise Exception()
        update = {
            'paid': order.paid or payment.paid
        }
        if payment.paid and not order.paid:
            change_message = "Получено уведомление об оплате"
        if payment.status == 'canceled':
            if order.paid:
                update['alert'] = "Попытка оплаты уже оплаченного заказа"
            else:
                change_message = "Оплата отклонена: {}".format(CANCELLATION_REASONS.get(payment.cancellation_details.reason, "неизвестная причина"))
        if change_message:
            LogEntry.objects.log_action(
                user_id=order.user.id,
                content_type_id=ContentType.objects.get_for_model(order).pk,
                object_id=order.pk,
                object_repr=force_text(order),
                action_flag=CHANGE,
                change_message=change_message
            )
        update_order.delay(order.pk, update)
    except Exception:
        logger.exception("Failed to process payment status")
        return HttpResponseForbidden()
    return HttpResponse('')
