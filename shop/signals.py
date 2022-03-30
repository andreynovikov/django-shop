from django.db.models.signals import post_save
from django.dispatch import receiver

from tagging.utils import parse_tag_input

from shop.models import Order
from shop.tasks import notify_user_order_collected, notify_user_order_delivered_shop, \
    notify_user_order_delivered, notify_user_order_done, \
    notify_manager, notify_manager_sms


@receiver(post_save, sender=Order, dispatch_uid='order_saved_receiver')
def order_saved(sender, **kwargs):
    order = kwargs['instance']

    for item in order.items.all():
        item.product.num = -1
        item.product.spb_num = -1
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
