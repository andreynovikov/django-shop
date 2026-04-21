import logging
import time

from django.http import Http404, StreamingHttpResponse, JsonResponse
from django.conf import settings
from django.core.paginator import Paginator
from django.db.models import Sum, F, Q, Case, When, OuterRef, Subquery
from django.shortcuts import render, redirect, get_object_or_404
from django.core.files.storage import default_storage
from django.contrib.auth.decorators import login_required
from django.contrib.sites.models import Site
from django.template import loader
from django.urls import reverse
from django.utils.text import capfirst

from sewingworld.models import SiteProfile
from shop.models import Category, Product, ProductRelation, ProductSet, ProductKind, Manufacturer, \
    Advert, SalesAction, City, Store, ServiceCenter, Stock, Favorites, Integration, ProductIntegration, \
    Serial
from shop.filters import get_product_filter

logger = logging.getLogger(__name__)


def products_stream(request, integration, template, filter_type):
    started = time.monotonic()
    use_categories = integration is None or not integration.output_skip_categories

    if integration:
        template = integration.output_template
        utm_source = integration.utm_source
    else:
        utm_source = filter_type

    filters = {
        'enabled': True,
        'price__gt': 0,
        'variations__exact': ''
    }
    context = {
        'utm_source': utm_source,
    }

    categories = {}
    if use_categories:
        root = Category.objects.get(slug=settings.MPTT_ROOT)
        children = root.get_children().filter(active=True, feed=True)
        for child in children:
            categories[child.pk] = child.pk
            descendants = child.get_descendants().filter(active=True, feed=True)
            for descendant in descendants:
                categories[descendant.pk] = child.pk
        filters['categories__in'] = root.get_descendants(include_self=True).filter(active=True, feed=True)
        context['children'] = children
        context['category_map'] = categories

    pre_t = time.monotonic()

    t = loader.get_template('xml/_{}_header.xml'.format(template))
    header = t.render(context, request)

    pre_p = time.monotonic()

    t = loader.get_template('xml/_{}_product.xml'.format(template))

    if filter_type == 'prym':
        filters['market'] = True
        filters['num__gt'] = 0
        try:
            filters['manufacturer'] = Manufacturer.objects.get(code='Prym')
        except Manufacturer.DoesNotExist:
            pass

    products = Product.objects.order_by().filter(**filters).distinct()

    if integration:
        if not integration.output_all:
            products = products.filter(
                integration=integration
            ).annotate(
                integration_price=Subquery(
                    ProductIntegration.objects.filter(
                        product=OuterRef('id'),
                        integration=integration
                    ).values('price')
                )
            )

        if integration.output_with_images:
            products.exclude(image__isnull=True).exclude(image__exact='')

        if integration.output_available:
            products = products.annotate(
                quantity=Sum('stock_item__quantity', filter=Q(stock_item__supplier__integration=integration)),
                correction=Sum('stock_item__correction', filter=Q(stock_item__supplier__integration=integration)),
                available=F('quantity') + F('correction')
            ).filter(available__gt=0)

        if integration.output_paged:
            paginator = Paginator(products.order_by('id'), 300)
            products = paginator.get_page(request.GET.get('page'))

    yield header

    pre_loop = time.monotonic()

    for product in products:
        context['product'] = product
        if integration:
            if integration.output_stock:
                context['stock'] = product.get_stock(integration=integration)
        yield t.render(context, request)

    post_loop = time.monotonic()

    context.pop('product', None)
    context.pop('integration', None)
    context.pop('stock', None)
    t = loader.get_template('xml/_{}_footer.xml'.format(template))
    yield t.render(context, request)

    ended = time.monotonic()

    logger.error(
        """
        Total: %s
        Prepare: %s
        Header: %s
        Products prepare: %s
        Products output: %s
        Footer: %s
        """,
        ended - started,
        pre_t - started,
        pre_p - pre_t,
        pre_loop - pre_p,
        post_loop - pre_loop,
        ended - post_loop
    )


def products(request, integration=None, template=None, filters=None):
    if integration:
        integration = Integration.objects.filter(utm_source=integration).first()
        if integration is None:
            raise Http404("Does not exist")
    stream = products_stream(request, integration, template, filters)
    return StreamingHttpResponse(stream, content_type='text/xml; charset=utf-8')


def stock(request):
    root = Category.objects.get(slug=settings.MPTT_ROOT)
    filters = {
        'enabled': True,
        'price__gt': 0,
        'variations__exact': '',
        'categories__in': root.get_descendants(include_self=True),
        'avito': True
    }
    integration = Integration.objects.filter(utm_source='avito').first()
    products = Product.objects.filter(**filters).distinct()
    products = map(lambda p: (p, max(int(p.get_stock(integration=integration)), 0)), products)
    context = {
        'products': products
    }
    return render(request, 'stock.csv', context, content_type='text/csv')
