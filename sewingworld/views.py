from django.conf import settings
from django.shortcuts import render, get_object_or_404
from django.core.files.storage import default_storage
from django.contrib.auth.decorators import login_required, permission_required

from shop.models import Category, Product, Basket


def ensure_session(request):
    if hasattr(request, 'session') and not request.session.session_key:
        request.session.save()
        request.session.modified = True


def index(request):
    context = {'root': Category.objects.get(slug=settings.MPTT_ROOT)}
    return render(request, 'index.html', context)


def products(request, template):
    root = Category.objects.get(slug=settings.MPTT_ROOT)
    children = root.get_children() #.filter(ya_active=True)
    categories = {}
    for child in children:
        #if not child.ya_active:
        #    continue
        categories[child.pk] = child.pk;
        descendants = child.get_descendants()
        for descendant in descendants:
            categories[descendant.pk] = child.pk;
    context = {
        'root': root,
        'children': children,
        'category_map': categories,
        'products': Product.objects.filter(enabled=True, categories__in=root.get_descendants(include_self=True)).distinct()
        }
    return render(request, template, context, content_type='text/xml; charset=utf-8')


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
