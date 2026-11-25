import logging

from django.conf import settings
from django.shortcuts import render

from shop.models import Category, Product, Integration

logger = logging.getLogger(__name__)


def stock(request):
    """ /stock_avito.csv: stock of the products marked for Avito, counted at the suppliers of the Avito integration """
    root = Category.objects.get(slug=settings.MPTT_ROOT)
    filters = {
        'enabled': True,
        'price__gt': 0,
        'variations__exact': '',
        'categories__in': root.get_descendants(include_self=True),
        'avito': True
    }
    integration = Integration.objects.filter(target_site=request.site, utm_source='avito').first()
    products = list(Product.objects.filter(**filters).distinct())
    counted = Product.get_stocks([product.pk for product in products], integration=integration)
    products = [(product, max(int(counted[product.pk]), 0)) for product in products]
    context = {
        'products': products
    }
    return render(request, 'stock.csv', context, content_type='text/csv')
