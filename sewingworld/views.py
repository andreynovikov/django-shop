from django.http import Http404, StreamingHttpResponse
from django.conf import settings
from django.shortcuts import render, get_object_or_404
from django.core.files.storage import default_storage
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.sites.models import Site
from django.template import loader, Context

from shop.models import Category, Product, Basket


def ensure_session(request):
    if hasattr(request, 'session') and not request.session.session_key:
        request.session.save()
        request.session.modified = True


def index(request):
    context = {'root': Category.objects.get(slug=settings.MPTT_ROOT)}
    return render(request, 'index.html', context)


def products_stream(request, templates, filter_type):
    root = Category.objects.get(slug=settings.MPTT_ROOT)
    children = root.get_children()
    categories = {}
    for child in children:
        categories[child.pk] = child.pk;
        descendants = child.get_descendants()
        for descendant in descendants:
            categories[descendant.pk] = child.pk;
    context = {
        'request': request,
        'children': children,
        'category_map': categories
    }
    t = loader.get_template('xml/_{}_header.xml'.format(templates))
    yield t.render(context)

    t = loader.get_template('xml/_{}_product.xml'.format(templates))
    filters = {
        'enabled': True,
        'price__gt': 0,
        'variations__exact': '',
        'categories__in': root.get_descendants(include_self=True)
        }

    products = Product.objects.filter(**filters).distinct()
    for product in products:
        context['product'] = product
        yield t.render(context)

    del context['product']
    t = loader.get_template('xml/_{}_footer.xml'.format(templates))
    yield t.render(context)


def products(request, templates, filters):
    return StreamingHttpResponse(products_stream(request, templates, filters), content_type='text/xml; charset=utf-8')


def catalog(request):
    context = {'root': Category.objects.get(slug=settings.MPTT_ROOT)}
    return render(request, 'catalog.html', context)


@login_required
@permission_required('shop.wholesale')
def category(request, path, instance):
    ensure_session(request)
    products = None
    if instance:
        order = instance.product_order.split(',')
        products = instance.products.filter(enabled=True).order_by(*order)
        basket, created = Basket.objects.get_or_create(session_id=request.session.session_key)
        quantities = {item.product: item.quantity for item in basket.items.all()}
        products = map(lambda p:(p,basket.product_cost(p),quantities.get(p, 0)), products)
    context = {'root': Category.objects.get(slug=settings.MPTT_ROOT),
               'category': instance, 'products': products}
    return render(request, 'category.html', context)


def expand(request, product_id):
    #ensure_session(request)
    product = get_object_or_404(Product, pk=product_id)
    context = {'product': product}
    return render(request, 'expand.html', context)
