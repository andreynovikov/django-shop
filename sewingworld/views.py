from django.http import Http404, HttpResponseForbidden, StreamingHttpResponse
from django.conf import settings
from django.shortcuts import render, get_object_or_404
from django.core.files.storage import default_storage
from django.contrib.sites.models import Site
from django.template import loader

from shop.models import Category, Product, ProductRelation, ProductSet, Manufacturer, Advert, SalesAction, City, \
    Store, ServiceCenter, Stock
from shop.filters import get_product_filter


def index(request):
    site = Site.objects.get_current()
    context = {
        'top_adverts': Advert.objects.filter(active=True, place='index_top', sites=site).order_by('order'),
        'middle_adverts': Advert.objects.filter(active=True, place='index_middle', sites=site).order_by('order'),
        'bottom_adverts': Advert.objects.filter(active=True, place='index_bottom', sites=site).order_by('order'),
        'actions': SalesAction.objects.filter(active=True, sites=site).order_by('order'),
        'gift_products': Product.objects.filter(enabled=True, show_on_sw=True, gift=True).order_by('-price')[:25],
        'recomended_products': Product.objects.filter(enabled=True, show_on_sw=True, recomended=True).order_by('-price')[:25],
        'first_page_products': Product.objects.filter(enabled=True, show_on_sw=True, firstpage=True).order_by('-price')[:25]
        }
    return render(request, 'index.html', context)


def search(request):
    context = {}
    return render(request, 'search.html', context)


def products_stream(request, templates, filter_type):
    root = Category.objects.get(slug=settings.MPTT_ROOT)
    children = root.get_children()
    if filter_type == 'yandex':
        children = children.filter(ya_active=True)
    categories = {}
    for child in children:
        categories[child.pk] = child.pk;
        descendants = child.get_descendants()
        for descendant in descendants:
            categories[descendant.pk] = child.pk;
    context = {
        'children': children,
        'category_map': categories
    }
    t = loader.get_template('xml/_{}_header.xml'.format(templates))
    yield t.render(context, request)

    t = loader.get_template('xml/_{}_product.xml'.format(templates))

    filters = {
        'enabled': True,
        'price__gt': 0,
        'variations__exact': '',
        'categories__in': root.get_descendants(include_self=True)
        }
    if filter_type == 'yandex':
        filters['market'] = True
        filters['num__gt'] = 0
    if filter_type == 'beru':
        filters['beru'] = True
    if filter_type == 'prym':
        filters['market'] = True
        filters['num__gt'] = 0
        try:
            filters['manufacturer'] = Manufacturer.objects.get(code='Prym')
        except Manufacturer.DoesNotExist:
            pass

    products = Product.objects.filter(**filters).distinct()
    for product in products:
        context['product'] = product
        yield t.render(context, request)

    context.pop('product', None)
    t = loader.get_template('xml/_{}_footer.xml'.format(templates))
    yield t.render(context, request)


def products(request, templates, filters):
    return StreamingHttpResponse(products_stream(request, templates, filters), content_type='text/xml; charset=utf-8')


def sales_actions(request):
    context = {'actions': SalesAction.objects.filter(active=True, show_in_list=True, sites=Site.objects.get_current()).order_by('order')}
    return render(request, 'sales_actions.html', context)


def sales_action(request, slug):
    action = get_object_or_404(SalesAction, slug=slug)
    if not Site.objects.get_current().salesaction_set.filter(slug=slug).exists():
        raise Http404("Sales action does not exist")
    products = action.products.filter(enabled=True).order_by('-price')
    context = {
        'action': action,
        'products': products
    }
    return render(request, 'sales_action.html', context)


def stores(request):
    stores = Store.objects.filter(enabled=True).order_by('city__country__ename', 'city__name')
    store_groups = []
    cur_country = None
    cur_country_index = -1
    cur_city = None
    cur_city_index = -1
    for store in stores:
        if cur_country != store.city.country:
            store_groups.append({'country': store.city.country, 'cities': []})
            cur_country = store.city.country
            cur_country_index += 1
            cur_city = None
            cur_city_index = -1
        if cur_city != store.city:
            store_groups[cur_country_index]['cities'].append({'city': store.city, 'stores': []})
            cur_city = store.city
            cur_city_index += 1
        store_groups[cur_country_index]['cities'][cur_city_index]['stores'].append(store)

    context = {
        'stores': stores,
        'store_groups': store_groups,
        }
    city = settings.SHOP_SETTINGS.get('city_id')
    if city:
        context['city'] = City.objects.get(pk=city)

    return render(request, 'stores.html', context)


def store(request, id):
    store = get_object_or_404(Store, pk=id)
    context = {'store': store}
    return render(request, 'store.html', context)


def service(request):
    services = ServiceCenter.objects.filter(enabled=True).order_by('city__country__ename', 'city__name')
    service_groups = []
    cur_country = None
    cur_country_index = -1
    cur_city = None
    cur_city_index = -1
    for service in services:
        if cur_country != service.city.country:
            service_groups.append({'country': service.city.country, 'cities': []})
            cur_country = service.city.country
            cur_country_index += 1
            cur_city = None
            cur_city_index = -1
        if cur_city != service.city:
            service_groups[cur_country_index]['cities'].append({'city': service.city, 'services': []})
            cur_city = service.city
            cur_city_index += 1
        service_groups[cur_country_index]['cities'][cur_city_index]['services'].append(service)

    context = {
        'services': services,
        'service_groups': service_groups,
        }
    city = settings.SHOP_SETTINGS.get('city_id')
    if city:
        context['city'] = City.objects.get(pk=city)

    return render(request, 'service.html', context)


def catalog(request):
    context = {'root': Category.objects.get(slug=settings.MPTT_ROOT)}
    return render(request, 'catalog.html', context)


def category(request, path, instance):
    products = None
    gtm_list = None
    if not instance:
        raise Http404("Category does not exist")
    filters = {
        'enabled': True,
        'show_on_sw': True
        }
    order = instance.product_order.split(',')
    products = instance.products.filter(**filters).order_by(*order)
    if products.count() < 1:
        filters['recomended'] = True
        filters['categories__in'] = instance.get_descendants()
        products = Product.objects.filter(**filters).order_by(*order).distinct()
        gtm_list = "Рекомендуем в каталоге"
    else:
        gtm_list = "Каталог"

    product_filter = None
    if instance.filters:
        fields = instance.filters.split(',')
        product_filter = get_product_filter(request.GET, queryset=products, fields=fields, request=request)
        products = product_filter.qs

    context = {
        'category': instance,
        'product_filter': product_filter,
        'products': products,
        'gtm_list': gtm_list
    }
    return render(request, 'category.html', context)


def product(request, code):
    product = get_object_or_404(Product, code=code)
    if product.categories.exists() and not product.breadcrumbs:
        raise Http404("Product does not exist")
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


def product_stock(request, code):
    if not request.is_ajax():
        return HttpResponseForbidden()

    product = get_object_or_404(Product, code=code)
    if product.categories.exists() and not product.breadcrumbs:
        raise Http404("Product does not exist")

    if product.constituents.count() == 0:
        suppliers = product.stock.all()
        stores = Store.objects.filter(enabled=True, supplier__in=suppliers).order_by('city__country__ename', 'city__name')
    else:
        stores = Store.objects.filter(enabled=True).order_by('city__country__ename', 'city__name')
    store_groups = []
    cur_country = None
    cur_country_index = -1
    cur_city = None
    cur_city_index = -1
    for store in stores:
        if product.constituents.count() == 0:
            stock = Stock.objects.get(product=product, supplier=store.supplier)
            quantity = stock.quantity + stock.correction
        else:
            quantity = 32767
            for item in ProductSet.objects.filter(declaration=product):
                try:
                    stock = Stock.objects.get(product=item.constituent, supplier=store.supplier)
                    q = stock.quantity + stock.correction
                    if item.quantity > 1:
                        q = int(q / item.quantity)
                except Stock.DoesNotExist:
                    q = 0.0
                if q < quantity:
                    quantity = q
        if not quantity > 0.0:
            continue
        if cur_country != store.city.country:
            store_groups.append({'country': store.city.country, 'cities': []})
            cur_country = store.city.country
            cur_country_index += 1
            cur_city = None
            cur_city_index = -1
        if cur_city != store.city:
            store_groups[cur_country_index]['cities'].append({'city': store.city, 'stores': []})
            cur_city = store.city
            cur_city_index += 1
        store_groups[cur_country_index]['cities'][cur_city_index]['stores'].append({
            'store': store,
            'quantity': quantity
        })

    context = {
        'product': product,
        'store_groups': store_groups,
        }
    response = render(request, 'stock.html', context)
    response['X-Robots-Tag'] = 'noindex'
    return response


def review_product(request, code):
    product = get_object_or_404(Product, code=code)
    if product.categories.exists() and not product.breadcrumbs:
        raise Http404("Product does not exist")

    context = {
        'target': product,
        }
    return render(request, 'reviews/post.html', context)
