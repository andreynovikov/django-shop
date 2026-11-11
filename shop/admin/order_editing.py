"""
Changes staff make to an order besides its form: items of another order taken in, a discount on every item,
and the address staff entered confirmed for the buyer.
"""
from django.contrib import messages

from shop.models import ShopUser


def combine_orders(order, other):
    """ Copies the items of another order of the same buyer into the order. Returns False for another buyer's order. """
    if order.user != other.user:
        return False
    for item in other.items.all():
        item.pk = None
        item.order = order
        item.save()
    return True


def apply_discount(order, discount, unit):
    """
    Gives the discount to the items that have a smaller one: in percent ('pct'), no more than the product's
    max_discount, or in roubles ('val'). Items that have a bigger discount keep it.
    """
    for item in order.items.all():
        if unit == 'pct':
            pct_discount = int(discount)
            if pct_discount > item.pct_discount:
                if pct_discount <= item.product.max_discount:
                    item.pct_discount = pct_discount
                else:
                    item.pct_discount = item.product.max_discount
                item.save()
        elif unit == 'val':
            val_discount = float(discount)
            if val_discount > item.val_discount:
                item.val_discount = val_discount
                item.save()


def confirm_buyer_email(order):
    """
    An address staff enter for the order becomes the buyer's confirmed one: order mail goes only to such.
    Returns the level and text of a message for staff, None when there is nothing to tell.
    """
    user = order.user
    if not user.phone.startswith('+'):  # service account of a marketplace, its orders get no mail
        return None
    if user.email_verified and user.email.lower() == order.email.lower():
        return None
    other = ShopUser.objects.filter(email__iexact=order.email).exclude(pk=user.pk).first()
    if other is not None:
        return messages.WARNING, ('Адрес %s указан у другого пользователя (%s), письма по заказу на него не придут'
                                  % (order.email, other.related_label()))
    user.email = order.email
    user.email_verified = True
    user.save(update_fields=['email', 'email_verified'])
    return messages.INFO, 'Адрес %s записан в профиль покупателя как подтверждённый' % order.email
