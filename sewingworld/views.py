from django.conf import settings
from django.shortcuts import render, get_object_or_404
from django.core.files.storage import default_storage

from shop.models import Category, Product


def index(request):
    context = {'root': Category.objects.get(slug=settings.MPTT_ROOT)}
    return render(request, 'index.html', context)


def search_xml(request):
    root = Category.objects.get(slug=settings.MPTT_ROOT)
    context = {
        'shop_info': getattr(settings, 'SHOP_INFO', {}),
        'root': root,
        'products': Product.objects.filter(enabled=True, categories__in=root.get_descendants(include_self=True))
        }
    return render(request, 'search.xml', context, content_type='text/xml; charset=utf-8')


def products(request, template):
    root = Category.objects.get(slug=settings.MPTT_ROOT)
    context = {
        'root': root,
        'products': Product.objects.filter(enabled=True, market=True, categories__in=root.get_descendants(include_self=True)).distinct()
        }
    return render(request, template, context, content_type='text/xml; charset=utf-8')


def catalog(request):
    context = {'root': Category.objects.get(slug=settings.MPTT_ROOT)}
    return render(request, 'catalog.html', context)


def category(request, path, instance):
    products = None
    if instance:
        order = instance.product_order.split(',')
        products = instance.products.filter(enabled=True).order_by(*order)
    context = {'category': instance, 'products': products}
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
    if cat_id is not None:
        try:
            category = Category.objects.get(pk=cat_id)
        except Category.DoesNotExist:
            pass
        except ValueError:
            pass
    if category is None and product.breadcrumbs:
        category = product.breadcrumbs.last()

    # temporary
    if not product.categories.exists():
        product.enabled = False

    if not product.hide_contents:
        constituents = ProductSet.objects.filter(declaration=product).order_by('-constituent__price')
    else:
        constituents = None

    context = {
        'category': category,
        'product': product,
        'constituents': constituents,
        'accessories': product.related.filter(child_products__child_product__enabled=True, child_products__kind=ProductRelation.KIND_ACCESSORY),
        'similar': product.related.filter(child_products__child_product__enabled=True, child_products__kind=ProductRelation.KIND_SIMILAR),
        'gifts': product.related.filter(child_products__child_product__enabled=True, child_products__kind=ProductRelation.KIND_GIFT),
        'utm_source': request.GET.get('utm_source', None)
        }
    return render(request, 'product.html', context)


def review_product(request, code):
    product = get_object_or_404(Product, code=code)
    if product.categories.exists() and not product.breadcrumbs:
        raise Http404("Product does not exist")

    context = {
        'target': product,
        }
    return render(request, 'reviews/post.html', context)
