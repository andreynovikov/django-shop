default_app_config = 'shop.apps.ShopAppConfig'


def get_user_weight(user, target):
    if user.has_perm('reviews.can_moderate'):
        return 50
    from .models import Product, Order
    if isinstance(target, Product):
        count = Order.objects.filter(user=user.pk,
                                     item__product=target.pk,
                                     status__in=[Order.STATUS_DONE, Order.STATUS_OTHERSHOP, Order.STATUS_DONE]
                                     ).count()
        if count > 0:
            return 10
    return 1
