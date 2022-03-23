import logging

from decimal import Decimal, ROUND_HALF_EVEN

from django.conf import settings
from django.utils import timezone

from celery import shared_task

from shop.models import Order, Basket, Product, ShopUser

import time

from facebook_business.adobjects.serverside.action_source import ActionSource
from facebook_business.adobjects.serverside.content import Content
from facebook_business.adobjects.serverside.custom_data import CustomData
from facebook_business.adobjects.serverside.event import Event
from facebook_business.adobjects.serverside.event_request import EventRequest
from facebook_business.adobjects.serverside.user_data import UserData
from facebook_business.api import FacebookAdsApi


log = logging.getLogger('shop')

FACEBOOK_TRACKING = getattr(settings, 'FACEBOOK_TRACKING', False)
FACEBOOK_PIXEL_ID = getattr(settings, 'FACEBOOK_PIXEL_ID', '')
FACEBOOK_TOKEN = getattr(settings, 'FACEBOOK_TOKEN', '')

log.error(FACEBOOK_TOKEN)
FacebookAdsApi.init(access_token=FACEBOOK_TOKEN)


@shared_task(ignore_result=True)
def notify_view_content(product_id, url, remote_address, user_agent):
    user_data = UserData(
        # It is recommended to send Client IP and User Agent for Conversions API Events.
        client_ip_address=remote_address,
        client_user_agent=user_agent
        # fbc='fb.1.1554763741205.AbCdEfGhIjKlMnOpQrStUvWxYz1234567890',
        # fbp='fb.1.1558571054389.1098115397',
    )

    content = Content(
        product_id=product_id,
    )

    custom_data = CustomData(
        contents=[content],
    )

    event = Event(
        event_name='ViewContent',
        event_time=int(time.time()),
        user_data=user_data,
        custom_data=custom_data,
        event_source_url=url,
        action_source=ActionSource.WEBSITE,
    )

    event_request = EventRequest(
        events=[event],
        pixel_id=FACEBOOK_PIXEL_ID,
    )

    event_response = event_request.execute()


@shared_task(ignore_result=True, store_errors_even_if_ignored=True)
def notify_add_to_cart(product_id, url, remote_address, user_agent):
    product = Product.objects.get(id=product_id)

    user_data = UserData(
        # It is recommended to send Client IP and User Agent for Conversions API Events.
        client_ip_address=remote_address,
        client_user_agent=user_agent
        # fbc='fb.1.1554763741205.AbCdEfGhIjKlMnOpQrStUvWxYz1234567890',
        # fbp='fb.1.1558571054389.1098115397',
    )

    content = Content(
        product_id=product_id,
        item_price=str(product.price.quantize(Decimal('1'), rounding=ROUND_HALF_EVEN))
    )

    custom_data = CustomData(
        contents=[content],
        content_type='product',
        currency='rub'
    )

    event = Event(
        event_name='AddToCart',
        event_time=int(time.time()),
        user_data=user_data,
        custom_data=custom_data,
        event_source_url=url,
        action_source=ActionSource.WEBSITE,
    )

    event_request = EventRequest(
        events=[event],
        pixel_id=FACEBOOK_PIXEL_ID,
    )

    event_response = event_request.execute()
    log.error(event_response)


@shared_task(ignore_result=True, store_errors_even_if_ignored=True)
def notify_initiate_checkout(basket_id, user_id, url, remote_address, user_agent):
    basket = Basket.objects.get(id=basket_id)
    user_phone = None
    user_email = None
    if user_id:
        user = ShopUser.objects.get(id=user_id)
        user_phone = user.phone
        user_email = user.email

    user_data = UserData(
        email=user_email,
        phone=user_phone,
        # It is recommended to send Client IP and User Agent for Conversions API Events.
        client_ip_address=remote_address,
        client_user_agent=user_agent
        # fbc='fb.1.1554763741205.AbCdEfGhIjKlMnOpQrStUvWxYz1234567890',
        # fbp='fb.1.1558571054389.1098115397',
    )

    contents = []
    for item in basket.items.all():
        contents.append(Content(
            product_id=item.product.id,
            title=item.product.title,
            brand=item.product.manufacturer.name,
            item_price=str(item.price.quantize(Decimal('1'), rounding=ROUND_HALF_EVEN)),
            quantity=item.quantity
        ))

    custom_data = CustomData(
        contents=contents,
        content_type='product',
        currency='rub',
        value=float(basket.total)
    )

    event = Event(
        event_name='InitiateCheckout',
        event_time=int(time.time()),
        user_data=user_data,
        custom_data=custom_data,
        event_source_url=url,
        action_source=ActionSource.WEBSITE,
    )

    event_request = EventRequest(
        events=[event],
        pixel_id=FACEBOOK_PIXEL_ID,
    )

    event_response = event_request.execute()
    log.error(event_response)


@shared_task(ignore_result=True, store_errors_even_if_ignored=True)
def notify_purchase(order_id, url, remote_address, user_agent):
    order = Order.objects.get(id=order_id)

    user_data = UserData(
        email=order.user.email,
        phone=str(order.user.phone),
        # It is recommended to send Client IP and User Agent for Conversions API Events.
        client_ip_address=remote_address,
        client_user_agent=user_agent
        # fbc='fb.1.1554763741205.AbCdEfGhIjKlMnOpQrStUvWxYz1234567890',
        # fbp='fb.1.1558571054389.1098115397',
    )

    contents = []
    for item in order.items.all():
        contents.append(Content(
            product_id=item.product.id,
            title=item.product.title,
            brand=item.product.manufacturer.name,
            item_price=str(item.price.quantize(Decimal('1'), rounding=ROUND_HALF_EVEN)),
            quantity=item.quantity
        ))

    custom_data = CustomData(
        order_id=order_id,
        contents=contents,
        content_type='product',
        currency='rub',
        value=float(order.total)
    )

    event = Event(
        event_name='Purchase',
        event_time=int(timezone.localtime(order.created).timestamp()),
        user_data=user_data,
        custom_data=custom_data,
        event_source_url=url,
        action_source=ActionSource.WEBSITE,
    )

    event_request = EventRequest(
        events=[event],
        pixel_id=FACEBOOK_PIXEL_ID,
    )

    event_response = event_request.execute()
    log.error(event_response)
