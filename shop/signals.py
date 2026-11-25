from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP

from django.db.models import Q
from django.db.models.signals import m2m_changed, post_delete, post_save, pre_delete, pre_save
from django.dispatch import receiver
from django.utils import timezone

# from tagging.utils import parse_tag_input

from django.contrib.flatpages.models import FlatPage

from mptt.signals import node_moved

from sewingworld.models import SiteProfile
from sewingworld.tasks import PRIORITY_HIGH, PRIORITY_IDLE

from reviews import get_review_model
from reviews.signals import review_was_posted

from shop.models import Advert, Category, Currency, Manufacturer, News, Order, OrderItem, Product, ProductPrice, \
    ProductRelation, ProductSet, SalesAction, ServiceCenter, Store
from shop.revalidation import CATEGORY_TREE_FIELDS, category_listing_tags, category_sites, revalidate, \
    revalidate_product_pages, revalidate_products, revalidate_stock
from shop.tasks.user_interaction import notify_user_order_collected, notify_user_order_delivered_shop, \
    notify_user_order_delivered, notify_user_review_products
from shop.tasks.admin import notify_review_posted, notify_manager, notify_manager_sms
from shop.tasks.integrations import create_modulpos_order, delete_modulpos_order, ym_upload_user, ym_upload_order

import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=OrderItem, dispatch_uid='order_item_saved_receiver')
def order_item_saved(sender, **kwargs):
    """
    A new quantity of an item changes the stock of its product: it is reset to be counted again, and the storefronts
    get the product's pages again if the stock they show changes
    """
    order_item = kwargs['instance']
    if order_item.tracker.has_changed('quantity'):
        product = order_item.product
        logger.error("### " + product.code + " saved in order_item_saved signal")
        revalidate_stock({product.pk: product.num})  # counted again once the order is saved
        product.num = -1
        product.save()


@receiver(post_save, sender=Order, dispatch_uid='order_saved_receiver')
def order_saved(sender, **kwargs):
    """
    Tasks are queued once the transaction commits: the admin saves the items after the order, in save_related(),
    and a status that is rolled back must not reach the customer
    """
    order = kwargs['instance']

    if order.tracker.has_changed('status'):
        if not order.status:  # new order
            if order.delivery == Order.DELIVERY_EXPRESS and hasattr(order.site, 'profile') and order.site.profile.manager_phones:
                for phone in order.site.profile.manager_phones.split(','):
                    notify_manager_sms.apply_async_on_commit((order.id, phone), priority=PRIORITY_HIGH)

            """ wait 5 minutes to let user supply comments and other stuff """
            notify_manager.apply_async_on_commit((order.id,), countdown=300)

            if not order.integration and order.meta and 'clientID' in order.meta:
                ym_upload_user.apply_async_on_commit((order.user.id, order.id), countdown=300)

        # Orders of marketplaces get none of what follows: no Metrika upload, POS order or customer notice
        if order.integration and order.integration.uses_api:
            return

        if not order.integration and order.meta and 'clientID' in order.meta:
            ym_upload_order.apply_async_on_commit((order.id,), countdown=360)  # let user data be uploaded before order data for new order

        if order.status == Order.STATUS_ACCEPTED:
            for item in order.items.all():
                if item.product.tags:
                    """
                    tags = parse_tag_input(item.product.tags)
                    order.append_user_tags(tags)
                    """
                    pass

        # An order on its way with a courier who has a ModulPOS terminal is on that terminal until its status changes
        if order.status == Order.STATUS_SENT:
            if order.courier and order.courier.pos_terminal:
                create_modulpos_order.delay_on_commit(order.id)

        if order.tracker.previous('status') == Order.STATUS_SENT:
            if order.courier and order.courier.pos_terminal and order.hidden_tracking_number:
                delete_modulpos_order.delay_on_commit(order.id)

        if order.status == Order.STATUS_COLLECTED:
            if order.payment == Order.PAYMENT_CARD or order.payment == Order.PAYMENT_TRANSFER:
                notify_user_order_collected.delay_on_commit(order.id)

        if order.status == Order.STATUS_DELIVERED_SHOP and order.store:
            notify_user_order_delivered_shop.delay_on_commit(order.id)

        if order.status == Order.STATUS_DELIVERED:
            if order.delivery in (Order.DELIVERY_TRANSPORT, Order.DELIVERY_POST, Order.DELIVERY_OZON, Order.DELIVERY_PICKPOINT):
                notify_user_order_delivered.delay_on_commit(order.id)

        if order.status == Order.STATUS_DONE or order.status == Order.STATUS_FINISHED:
            """ (by Sigalev request)
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
            """
            if order.status == Order.STATUS_DONE:
                if order.site.domain in ['www.sewing-world.ru', 'market.yandex.ru']:
                    next_week = timezone.now() + timedelta(days=7)
                    notify_user_review_products.apply_async_on_commit((order.id,), eta=next_week)


@receiver(review_was_posted, sender=get_review_model(), dispatch_uid='review_posted_receiver')
def review_posted(sender, review, request, **kwargs):
    notify_review_posted.s(review.id).apply_async(priority=PRIORITY_IDLE)


# Revalidation of the storefronts' pages, see shop/revalidation.py

# fields whose values before the save tell what else to revalidate
REMEMBERED = {
    Category: CATEGORY_TREE_FIELDS,
    SalesAction: ('slug', 'active', 'notice', 'brief'),
    Advert: ('place',),
    FlatPage: ('url',),
    Store: ('site_id',),
    SiteProfile: ('root_category_id',),
    Currency: ('rate',),
}


def remember_previous(sender, instance, raw=False, **kwargs):
    """ The fields of REMEMBERED as they are before the save, None for a new object """
    instance._previous = None
    if not raw and instance.pk is not None:
        instance._previous = sender._default_manager.filter(pk=instance.pk).values(*REMEMBERED[sender]).first()


for model in REMEMBERED:
    pre_save.connect(remember_previous, sender=model, dispatch_uid=f'remember_previous_{model._meta.label_lower}')


def previous(instance, field):
    return (getattr(instance, '_previous', None) or {}).get(field)


def changed(instance, *fields):
    """ Whether the save changed any of the fields; any changed for a new object """
    values = getattr(instance, '_previous', None)
    return values is None or any(values[field] != getattr(instance, field) for field in fields)


@receiver(post_save, sender=Category, dispatch_uid='category_saved_receiver')
def category_saved(sender, instance, raw=False, **kwargs):
    if raw:
        return
    tags = {f'category:{instance.pk}', f'category-path:{instance.get_api_path()}'}
    if changed(instance, *CATEGORY_TREE_FIELDS):
        tags.add('catalog')  # the menu of every page
    revalidate(tags, category_sites(instance))


@receiver(post_delete, sender=Category, dispatch_uid='category_deleted_receiver')
def category_deleted(sender, instance, **kwargs):
    revalidate({'catalog'}, category_sites(instance))


@receiver(node_moved, sender=Category, dispatch_uid='category_moved_receiver')
def category_moved(sender, instance, **kwargs):
    # the admin drags categories, also between catalogs of different sites
    revalidate({'catalog'})


@receiver(m2m_changed, sender=Product.categories.through, dispatch_uid='product_categories_changed_receiver')
def product_categories_changed(sender, instance, action, reverse, pk_set, **kwargs):
    """ The lists of the categories a product is put in or taken out of, the product's own page shows its categories """
    if action not in ('post_add', 'post_remove', 'pre_clear'):
        return
    if reverse:  # category.products
        products = set(instance.products.values_list('pk', flat=True)) if action == 'pre_clear' else pk_set
        revalidate_products(products, tags=category_listing_tags([instance.pk]))
    else:
        categories = set(instance.categories.values_list('pk', flat=True)) if action == 'pre_clear' else pk_set
        revalidate_products([instance.pk], tags=category_listing_tags(categories))


@receiver(m2m_changed, sender=Product.sales_actions.through, dispatch_uid='product_sales_actions_changed_receiver')
def product_sales_actions_changed(sender, instance, action, reverse, pk_set, **kwargs):
    if action not in ('post_add', 'post_remove', 'pre_clear'):
        return
    if reverse:  # sales_action.products
        products = set(instance.products.values_list('pk', flat=True)) if action == 'pre_clear' else pk_set
        revalidate_products(products, tags={f'action:{instance.slug}'})
    else:
        actions = instance.sales_actions.all() if action == 'pre_clear' else SalesAction.objects.filter(pk__in=pk_set)
        revalidate_products([instance.pk], tags={f'action:{slug}' for slug in actions.values_list('slug', flat=True)})


@receiver(m2m_changed, sender=Product.sites.through, dispatch_uid='product_sites_changed_receiver')
def product_sites_changed(sender, instance, action, reverse, pk_set, **kwargs):
    """ A site the product leaves renders its pages too: they show it no more """
    if action not in ('post_add', 'post_remove', 'pre_clear'):
        return
    if reverse:  # site.products
        products = set(instance.products.values_list('pk', flat=True)) if action == 'pre_clear' else pk_set
        revalidate_products(products, sites=[instance.pk])
    else:
        sites = set(instance.sites.values_list('pk', flat=True)) if action == 'pre_clear' else pk_set
        revalidate_products([instance.pk], sites=sites)


@receiver(post_save, sender=ProductPrice, dispatch_uid='product_price_saved_receiver')
@receiver(post_delete, sender=ProductPrice, dispatch_uid='product_price_deleted_receiver')
def product_price_changed(sender, instance, raw=False, **kwargs):
    if not raw:
        revalidate_products([instance.product_id])


@receiver(post_save, sender=ProductSet, dispatch_uid='product_set_saved_receiver')
@receiver(post_delete, sender=ProductSet, dispatch_uid='product_set_deleted_receiver')
def product_set_changed(sender, instance, raw=False, **kwargs):
    if not raw:
        revalidate_products([instance.declaration_id])  # its price and stock are those of its parts


@receiver(post_save, sender=ProductRelation, dispatch_uid='product_relation_saved_receiver')
@receiver(post_delete, sender=ProductRelation, dispatch_uid='product_relation_deleted_receiver')
def product_relation_changed(sender, instance, raw=False, **kwargs):
    if not raw:
        revalidate_product_pages([instance.parent_product_id])


@receiver(post_save, sender=Manufacturer, dispatch_uid='manufacturer_saved_receiver')
def manufacturer_saved(sender, instance, created, raw=False, **kwargs):
    if not raw and not created:
        revalidate_product_pages(instance.product_set.values_list('pk', flat=True))


@receiver(post_save, sender=Currency, dispatch_uid='currency_saved_receiver')
def currency_saved(sender, instance, raw=False, **kwargs):
    """ update_product_prices() has saved the products in the currency with the new rate, it is connected first """
    if raw:
        return
    # update_cbrf_currencies() sets the rate as a float, the database keeps two decimals of it
    rate = Decimal(str(instance.rate)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    if previous(instance, 'rate') != rate:
        revalidate_products(Product.objects.filter(Q(cur_code=instance) | Q(ws_cur_code=instance)).values_list('pk', flat=True))


@receiver(post_save, sender=SalesAction, dispatch_uid='sales_action_saved_receiver')
def sales_action_saved(sender, instance, created, raw=False, **kwargs):
    if raw:
        return
    tags = {'actions', f'action:{instance.slug}'}
    if previous(instance, 'slug') not in (None, instance.slug):
        tags.add(f'action:{previous(instance, "slug")}')
    revalidate(tags, instance.sites.all())
    products = instance.products.values_list('pk', flat=True)
    if changed(instance, 'active', 'notice'):
        revalidate_products(products)  # the cards of the products in lists show the notice
    elif changed(instance, 'slug', 'brief'):
        revalidate_product_pages(products)


@receiver(pre_delete, sender=SalesAction, dispatch_uid='sales_action_deleted_receiver')
def sales_action_deleted(sender, instance, **kwargs):
    # before the delete, which takes the sites and products away
    revalidate({'actions', f'action:{instance.slug}'}, instance.sites.all())
    revalidate_products(instance.products.values_list('pk', flat=True))


@receiver(post_save, sender=Advert, dispatch_uid='advert_saved_receiver')
def advert_saved(sender, instance, raw=False, **kwargs):
    if raw:
        return
    tags = {f'adverts:{instance.place}'}
    if previous(instance, 'place') not in (None, instance.place):
        tags.add(f'adverts:{previous(instance, "place")}')
    revalidate(tags, instance.sites.all())


@receiver(pre_delete, sender=Advert, dispatch_uid='advert_deleted_receiver')
def advert_deleted(sender, instance, **kwargs):
    revalidate({f'adverts:{instance.place}'}, instance.sites.all())


@receiver(post_save, sender=FlatPage, dispatch_uid='flatpage_saved_receiver')
def page_saved(sender, instance, raw=False, **kwargs):
    if raw:
        return
    tags = {'pages', f'page:{instance.url}'}
    if previous(instance, 'url') not in (None, instance.url):
        tags.add(f'page:{previous(instance, "url")}')
    revalidate(tags, instance.sites.all())


@receiver(pre_delete, sender=FlatPage, dispatch_uid='flatpage_deleted_receiver')
def page_deleted(sender, instance, **kwargs):
    revalidate({'pages', f'page:{instance.url}'}, instance.sites.all())


@receiver(post_save, sender=Store, dispatch_uid='store_saved_receiver')
@receiver(post_delete, sender=Store, dispatch_uid='store_deleted_receiver')
def store_changed(sender, instance, raw=False, **kwargs):
    if not raw:
        revalidate({'stores', f'store:{instance.pk}'}, {instance.site_id, previous(instance, 'site_id')} - {None})


@receiver(post_save, sender=ServiceCenter, dispatch_uid='service_center_saved_receiver')
@receiver(post_delete, sender=ServiceCenter, dispatch_uid='service_center_deleted_receiver')
def service_center_changed(sender, instance, raw=False, **kwargs):
    if not raw:
        revalidate({'servicecenters'})  # every site lists them


@receiver(post_save, sender=News, dispatch_uid='news_saved_receiver')
def news_saved(sender, instance, raw=False, **kwargs):
    if not raw:
        revalidate({'news'}, instance.sites.all())


@receiver(pre_delete, sender=News, dispatch_uid='news_deleted_receiver')
def news_deleted(sender, instance, **kwargs):
    revalidate({'news'}, instance.sites.all())


@receiver(post_save, sender=get_review_model(), dispatch_uid='review_saved_receiver')
@receiver(post_delete, sender=get_review_model(), dispatch_uid='review_deleted_receiver')
def review_changed(sender, instance, raw=False, **kwargs):
    if not raw:
        revalidate({'reviews'}, [instance.site_id])


@receiver(post_save, sender=SiteProfile, dispatch_uid='site_profile_saved_receiver')
def site_profile_saved(sender, instance, raw=False, **kwargs):
    if raw:
        return
    tags = {'site'}
    if changed(instance, 'root_category_id'):
        tags.add('catalog')
    revalidate(tags, [instance.site_id])
