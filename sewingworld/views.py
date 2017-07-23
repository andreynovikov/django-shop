from django.conf import settings
from django.shortcuts import render, get_object_or_404
from django.core.files.storage import default_storage

from shop.models import Category, Product


def index(request):
    context = {'root': Category.objects.get(slug=settings.MPTT_ROOT)}
    return render(request, 'index.html', context)


def catalog(request):
    context = {'root': Category.objects.get(slug=settings.MPTT_ROOT)}
    return render(request, 'catalog.html', context)


def category(request, path, instance):
    products = None
    if instance:
        products = instance.products.filter(enabled=True).order_by('-price')
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
    context = {'product': product}
    return render(request, 'product.html', context)
