from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.cache import InvalidCacheBackendError, caches
from django.core.cache.utils import make_template_fragment_key

from tagging.utils import parse_tag_input

from reviews import get_model
from reviews.signals import review_was_posted

from shop.models import Product, Order
from shop.tasks import notify_user_order_collected, notify_user_order_delivered_shop, \
    notify_user_order_delivered, notify_user_order_done, notify_review_posted


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
    print("Post save emited for", order)

    for item in order.items.all():
        item.product.num = -1
        item.product.spb_num = -1
        item.product.ws_num = -1
        item.product.save()

    if order.tracker.has_changed('status'):
        if order.status == Order.STATUS_ACCEPTED:
            for item in order.items.all():
                if item.product.tags:
                    tags = parse_tag_input(item.product.tags)
                    order.append_user_tags(tags)

        if order.status == Order.STATUS_COLLECTED:
            if order.payment == Order.PAYMENT_CARD or order.payment == Order.PAYMENT_TRANSFER:
                notify_user_order_collected.delay(order.id)

        if order.status == Order.STATUS_DELIVERED_SHOP and order.store:
            notify_user_order_delivered_shop.delay(order.id)

        if order.status == Order.STATUS_DELIVERED:
            if order.delivery == Order.DELIVERY_TRANSPORT or order.delivery == Order.DELIVERY_PICKPOINT:
                notify_user_order_delivered.delay(order.id)

        if order.status == Order.STATUS_DONE or order.status == Order.STATUS_FINISHED:
            if order.total >= 3000 and order.user.discount < 5:
                order.user.discount = 5
                order.user.save()
            if order.total >= 30000 and order.user.discount < 10:
                order.user.discount = 10
                order.user.save()
            if order.status == Order.STATUS_DONE:
                notify_user_order_done.delay(order.id)

        print(order.tracker.changed())


@receiver(review_was_posted, sender=get_model(), dispatch_uid='review_posted_receiver')
def review_posted(sender, review, request, **kwargs):
    notify_review_posted.delay(review.id)
