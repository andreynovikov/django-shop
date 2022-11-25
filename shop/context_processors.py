from django.conf import settings


def shop_info(request):
    return {
        'shop_info': getattr(settings, 'SHOP_INFO', {})
    }
