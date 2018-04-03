from django.conf import settings
from django.shortcuts import render, get_object_or_404
from django.core.files.storage import default_storage

from shop.models import Category, Product, ProductRelation, SalesAction


def index(request):
    context = {}
    return render(request, 'index.html', context)


def search_xml(request):
    root = Category.objects.get(slug=settings.MPTT_ROOT)
    children = root.get_children()
    categories = {}
    for child in children:
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
    return render(request, 'search.xml', context, content_type='text/xml; charset=utf-8')


def search(request):
    context = {}
    return render(request, 'search.html', context)


def products(request, template):
    root = Category.objects.get(slug=settings.MPTT_ROOT)
    context = {
        'products': Product.objects.filter(enabled=True, market=True, categories__in=root.get_descendants(include_self=True)).distinct()
        }
    return render(request, template, context, content_type='text/xml; charset=utf-8')


def sales_actions(request):
    context = {'actions': SalesAction.objects.filter(active=True).order_by('order')}
    return render(request, 'sales_actions.html', context)


def sales_action(request, slug):
    action = get_object_or_404(SalesAction, slug=slug)
    context = {'action': action}
    products = action.products.filter(enabled=True).order_by('-price')
    context = {
        'action': action,
        'products': products
    }
    return render(request, 'sales_action.html', context)


def catalog(request):
    context = {'root': Category.objects.get(slug=settings.MPTT_ROOT)}
    return render(request, 'catalog.html', context)


def category(request, path, instance):
    products = None
    if instance:
        products = instance.products.filter(enabled=True).order_by('-price')
    context = {
        'category': instance,
        'products': products
    }
    return render(request, 'category.html', context)


def product(request, code):
    product = get_object_or_404(Product, code=code)
    product.images = []
    if default_storage.exists(product.image_prefix):
        try:
            dirs, files = default_storage.listdir(product.image_prefix)
            if files is not None:
                for file in sorted(files):
                    if file.endswith('.s.jpg'):
                        product.images.append(file[:-6])
        except NotADirectoryError:
            pass
    category = None
    cat_id = request.GET.get('cat', None)
    try:
        if cat_id is not None:
            category = Category.objects.get(pk=cat_id)
        else:
            cat_id = request.META['QUERY_STRING']
            if cat_id:
                cat_id = int(cat_id)
                category = Category.objects.get(basset_id=cat_id)
    except Category.DoesNotExist:
        pass
    except ValueError:
        pass
    if category is None:
        root = Category.objects.get(slug=settings.MPTT_ROOT)
        for instance in product.categories.all():
            if instance.get_ancestors().all().first() == root:
                category = instance
                break

    context = {
        'category': category,
        'product': product,
        'accessories': product.related.filter(child_products__child_product__enabled=True, child_products__kind=ProductRelation.KIND_ACCESSORY),
        'similar': product.related.filter(child_products__child_product__enabled=True, child_products__kind=ProductRelation.KIND_SIMILAR),
        'gifts': product.related.filter(child_products__child_product__enabled=True, child_products__kind=ProductRelation.KIND_GIFT)
        }
    return render(request, 'product.html', context)
