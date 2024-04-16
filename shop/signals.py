from datetime import timedelta

from django.db.models import Q
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.cache import InvalidCacheBackendError, caches
from django.core.cache.utils import make_template_fragment_key
from django.contrib.sites.models import Site
from django.utils import timezone

from tagging.utils import parse_tag_input

from django.contrib.flatpages.models import FlatPage

from django_cleanup.signals import cleanup_pre_delete
from sorl.thumbnail import delete as delete_thumbnail

from sewingworld.tasks import PRIORITY_HIGH, PRIORITY_NORMAL, PRIORITY_LOW, PRIORITY_IDLE

from reviews import get_review_model
from reviews.signals import review_was_posted

from shop.models import Product, Order, OrderItem, News
from shop.tasks import notify_user_order_collected, notify_user_order_delivered_shop, \
    notify_user_order_delivered, notify_user_review_products, notify_review_posted, \
    create_modulpos_order, delete_modulpos_order, notify_manager, notify_manager_sms, \
    revalidate_nextjs, ym_upload_user, ym_upload_order

import logging

logger = logging.getLogger(__name__)

SITE_SW = Site.objects.get(domain='www.sewing-world.ru')
SITE_YANDEX = Site.objects.get(domain='market.yandex.ru')


@receiver(post_save, sender=Product, dispatch_uid='product_saved_receiver')
def product_saved(sender, **kwargs):
    product = kwargs['instance']
    if product.num >= 0:  # renew pages only if stock is reset (this disables double renew on stocks import)
        return

    try:
        fragment_cache = caches['template_fragments']
    except InvalidCacheBackendError:
        fragment_cache = caches['default']
    vary_on = [product.id]
    cache_key = make_template_fragment_key('product', vary_on)
    fragment_cache.delete(cache_key)
    cache_key = make_template_fragment_key('product_description', vary_on)
    fragment_cache.delete(cache_key)

    payload = {
        'model': 'product',
        'pk': product.pk,
        'code': product.code
    }
    root_slugs = set()
    for category in product.categories.all():
        root_slugs.add(category.get_root().slug)
    for site in Site.objects.filter(profile__category_root_slug__in=root_slugs).exclude(profile__revalidation_token__exact=''):
        revalidate_nextjs.s(site.domain, site.profile.revalidation_token, payload).apply_async(priority=PRIORITY_IDLE)


@receiver(post_save, sender=OrderItem, dispatch_uid='order_item_saved_receiver')
def order_item_saved(sender, **kwargs):
    order_item = kwargs['instance']
    if order_item.tracker.has_changed('quantity'):
        order_item.product.num = -1
        order_item.product.save()


@receiver(post_save, sender=Order, dispatch_uid='order_saved_receiver')
def order_saved(sender, **kwargs):
    order = kwargs['instance']

    if order.tracker.has_changed('status'):
        if not order.status:  # new order
            if order.delivery == Order.DELIVERY_EXPRESS and hasattr(order.site, 'profile') and order.site.profile.manager_phones:
                for phone in order.site.profile.manager_phones.split(','):
                    notify_manager_sms.s(order.id, phone).apply_async(priority=PRIORITY_HIGH)

            """ wait 5 minutes to let user supply comments and other stuff """
            notify_manager.apply_async((order.id,), countdown=300)

            if not order.integration and order.meta and 'clientID' in order.meta:
                ym_upload_user.apply_async((order.user.id, order.id), countdown=300)

        if order.integration and order.integration.uses_api:
            return

        if not order.integration and order.meta and 'clientID' in order.meta:
            ym_upload_order.apply_async((order.id,), countdown=360)  # let user data be uploaded before order data for new order

        if order.status == Order.STATUS_ACCEPTED:
            for item in order.items.all():
                if item.product.tags:
                    tags = parse_tag_input(item.product.tags)
                    order.append_user_tags(tags)

        if order.status == Order.STATUS_SENT:
            if order.courier and order.courier.pos_terminal:
                create_modulpos_order.delay(order.id)

        if order.tracker.previous('status') == Order.STATUS_SENT:
            if order.courier and order.courier.pos_terminal and order.hidden_tracking_number:
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
                if order.site == SITE_SW or order.site == SITE_YANDEX:
                    next_week = timezone.now() + timedelta(days=7)
                    notify_user_review_products.apply_async((order.id,), eta=next_week)


@receiver(review_was_posted, sender=get_review_model(), dispatch_uid='review_posted_receiver')
def review_posted(sender, review, request, **kwargs):
    notify_review_posted.s(review.id).apply_async(priority=PRIORITY_IDLE)


@receiver(post_save, sender=FlatPage, dispatch_uid='flatpage_saved_receiver')
def page_saved(sender, **kwargs):
    page = kwargs['instance']
    payload = {
        'model': 'page',
        'pk': page.pk,
        'uri': page.url
    }
    for site in page.sites.exclude(profile__revalidation_token__exact=''):
        revalidate_nextjs.s(site.domain, site.profile.revalidation_token, payload).apply_async(priority=PRIORITY_IDLE)


@receiver(post_save, sender=News, dispatch_uid='news_saved_receiver')
def news_saved(sender, **kwargs):
    news = kwargs['instance']
    payload = {
        'model': 'news',
        'pk': news.pk
    }
    for site in news.sites.exclude(profile__revalidation_token__exact=''):
        revalidate_nextjs.s(site.domain, site.profile.revalidation_token, payload).apply_async(priority=PRIORITY_IDLE)


@receiver(cleanup_pre_delete)
def sorl_delete(**kwargs):
    delete_thumbnail(kwargs['file'])
