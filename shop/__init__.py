default_app_config = 'shop.apps.ShopAppConfig'

def get_review_model():
    from .models import ProductReview
    return ProductReview


def get_review_form():
    from .forms import ProductReviewForm
    return ProductReviewForm


def get_review_api_user_serializer():
    from sewingworld.serializers import UserListSerializer
    return UserListSerializer


def get_review_user_weight(user, target):
    if user.has_perm('reviews.can_moderate'):
        return 50
    from .models import Product, Order
    if isinstance(target, Product):
        count = Order.objects.filter(user=user.pk,
                                     item__product=target.pk,
                                     status__in=[Order.STATUS_DONE, Order.STATUS_OTHERSHOP]
                                     ).count()
        if count > 0:
            return 10
    return 1
