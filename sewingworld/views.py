from django.http import HttpResponseNotFound
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
        products = Product.objects.filter(enabled=True, categories__in=instance.get_descendants(include_self=True)) # .order_by('-price')
    else:
        return HttpResponseNotFound()
    context = {'category': instance, 'products': products}
    return render(request, 'category.html', context)


def product(request, code):
    product = get_object_or_404(Product, code=code)
    if not product.breadcrumbs:
        return HttpResponseNotFound()
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
    context = {'product': product}
    return render(request, 'product.html', context)
