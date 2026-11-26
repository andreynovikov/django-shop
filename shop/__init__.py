"""
The shop app. Its functions below are the hooks of django-rated-reviews, which REVIEW_APP = 'shop' in the settings
points here: reviews of products are ProductReview, belong to the request's site, and weigh by the reviewer.
"""


def get_review_model():
    from .models import ProductReview
    return ProductReview


def get_review_form():
    from .forms import ProductReviewForm
    return ProductReviewForm


def get_review_site_id(request):
    return request.site.id


def get_review_api_user_serializer():
    from sewingworld.serializers.users import UserListSerializer
    return UserListSerializer


def get_review_user_weight(user, target):
    """
    How much the user's rating counts: 50 for moderators, 10 for a buyer of the product (an order of it done or
    passed to another shop), 1 for anyone else
    """
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
