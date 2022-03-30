from datetime import timedelta

from django.db.models import Q
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.cache import InvalidCacheBackendError, caches
from django.core.cache.utils import make_template_fragment_key
from django.contrib.sites.models import Site
from django.utils import timezone

from tagging.utils import parse_tag_input

from reviews import get_review_model
from reviews.signals import review_was_posted

from shop.models import Product, Order
from shop.tasks import notify_user_order_collected, notify_user_order_delivered_shop, \
    notify_user_order_delivered, notify_user_order_done, notify_user_review_products, \
    notify_review_posted, create_modulpos_order, delete_modulpos_order, \
    notify_manager, notify_manager_sms


SITE_SW = Site.objects.get(domain='www.sewing-world.ru')
SITE_YANDEX = Site.objects.get(domain='market.yandex.ru')


@receiver(post_save, sender=Product, dispatch_uid='product_saved_receiver')
def product_saved(sender, **kwargs):
    product = kwargs['instance']
    try:
        fragment_cache = caches['template_fragments']
    except InvalidCacheBackendError:
        fragment_cache = caches['default']
    vary_on = [product.id]
    cache_key = make_template_fragment_key('product', vary_on)
    fragment_cache.delete(cache_key)
    cache_key = make_template_fragment_key('product_description', vary_on)
    fragment_cache.delete(cache_key)


@receiver(post_save, sender=Order, dispatch_uid='order_saved_receiver')
def order_saved(sender, **kwargs):
    order = kwargs['instance']

    for item in order.items.all():
        item.product.num = -1
        item.product.spb_num = -1
        item.product.ws_num = -1
        item.product.save()

    if order.tracker.has_changed('status'):
        if not order.status:  # new order
            if hasattr(order.site, 'profile') and order.site.profile.manager_phones:
                for phone in order.site.profile.manager_phones.split(','):
                    notify_manager_sms.delay(order.id, phone)
            """ wait for 5 minutes to let user supply comments and other stuff """
            notify_manager.apply_async((order.id,), countdown=300)

        if order.integration and order.integration.uses_api:
            return

        if order.status == Order.STATUS_ACCEPTED:
            for item in order.items.all():
                if item.product.tags:
                    tags = parse_tag_input(item.product.tags)
                    order.append_user_tags(tags)

        if order.status == Order.STATUS_SENT:
            if order.courier and order.courier.pos_id:
                create_modulpos_order.delay(order.id)

        if order.tracker.previous('status') == Order.STATUS_SENT:
            if order.courier and order.courier.pos_id and order.hidden_tracking_number:
                delete_modulpos_order.delay(order.id)

        if order.status == Order.STATUS_COLLECTED:
            if order.payment == Order.PAYMENT_CARD or order.payment == Order.PAYMENT_TRANSFER:
                notify_user_order_collected.delay(order.id)

        if order.status == Order.STATUS_DELIVERED_SHOP and order.store:
            notify_user_order_delivered_shop.delay(order.id)

        if order.status == Order.STATUS_DELIVERED:
            if order.delivery in (Order.DELIVERY_TRANSPORT, Order.DELIVERY_POST, Order.DELIVERY_OZON, Order.DELIVERY_PICKPOINT):
                notify_user_order_delivered.delay(order.id)

        if order.status == Order.STATUS_DONE or order.status == Order.STATUS_FINISHED:
            total = 0
            complete_orders = order.user.orders.filter(Q(status=Order.STATUS_DONE) | Q(status=Order.STATUS_FINISHED))
            for complete_order in complete_orders:
                total += complete_order.total
            if total >= 30000 and order.user.discount < 10:
                order.user.discount = 10
                order.user.save()
            if total >= 3000 and order.user.discount < 5:
                order.user.discount = 5
                order.user.save()
            if order.status == Order.STATUS_DONE:
                notify_user_order_done.delay(order.id)
                if order.site == SITE_SW or order.site == SITE_YANDEX:
                    next_week = timezone.now() + timedelta(days=7)
                    notify_user_review_products.apply_async((order.id,), eta=next_week)


@receiver(review_was_posted, sender=get_review_model(), dispatch_uid='review_posted_receiver')
def review_posted(sender, review, request, **kwargs):
    notify_review_posted.delay(review.id)
