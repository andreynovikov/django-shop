from django.http import Http404, StreamingHttpResponse, JsonResponse
from django.conf import settings
from django.db.models import Sum, F, Q
from django.shortcuts import render, redirect, get_object_or_404
from django.core.files.storage import default_storage
from django.contrib.auth.decorators import login_required
from django.contrib.sites.models import Site
from django.template import loader
from django.utils.text import capfirst

from sewingworld.models import SiteProfile
from facebook.tasks import FACEBOOK_TRACKING, notify_view_content
from shop.models import Category, Product, ProductRelation, ProductSet, ProductKind, Manufacturer, \
    Advert, SalesAction, City, Store, ServiceCenter, Stock, Favorites, Integration, ProductIntegration
from shop.filters import get_product_filter


def index(request):
    site = Site.objects.get_current()

    if request.user.is_authenticated:
        favorites = Favorites.objects.filter(user=request.user).values_list('product', flat=True)
    else:
        favorites = []

    context = {
        'top_adverts': Advert.objects.filter(active=True, place='index_top', sites=site).order_by('order'),
        'middle_adverts': Advert.objects.filter(active=True, place='index_middle', sites=site).order_by('order'),
        'bottom_adverts': Advert.objects.filter(active=True, place='index_bottom', sites=site).order_by('order'),
        'ground_adverts': Advert.objects.filter(active=True, place='index_ground', sites=site).order_by('order'),
        'actions': SalesAction.objects.filter(active=True, sites=site).order_by('order'),
        'gift_products': Product.objects.filter(enabled=True, show_on_sw=True, gift=True).order_by('-price')[:25],
        'recomended_products': Product.objects.filter(enabled=True, show_on_sw=True, recomended=True).order_by('-price')[:25],
        'first_page_products': Product.objects.filter(enabled=True, show_on_sw=True, firstpage=True).order_by('-price')[:25],
        'favorites': favorites
    }
    return render(request, 'index.html', context)


def search(request):
    context = {}
    return render(request, 'search.html', context)


def products_stream(request, integration, template, filter_type):
    root = Category.objects.get(slug=settings.MPTT_ROOT)
    children = root.get_children()

    if integration:
        template = integration.output_template
        utm_source = integration.utm_source
        if integration.utm_source in ['yandex', 'beru', 'google', 'avito']:
            children = children.filter(ya_active=True)
    else:
        utm_source = filter_type

    categories = {}
    for child in children:
        categories[child.pk] = child.pk
        descendants = child.get_descendants()
        for descendant in descendants:
            categories[descendant.pk] = child.pk

    context = {
        'utm_source': utm_source,
        'children': children,
        'category_map': categories
    }
    t = loader.get_template('xml/_{}_header.xml'.format(template))
    yield t.render(context, request)

    t = loader.get_template('xml/_{}_product.xml'.format(template))

    filters = {
        'enabled': True,
        'price__gt': 0,
        'variations__exact': '',
        'categories__in': root.get_descendants(include_self=True)
    }

    if integration and not integration.output_all:
        filters['integration'] = integration

    if filter_type == 'yandex':
        filters['market'] = True
        filters['num__gt'] = 0
    if filter_type == 'prym':
        filters['market'] = True
        filters['num__gt'] = 0
        try:
            filters['manufacturer'] = Manufacturer.objects.get(code='Prym')
        except Manufacturer.DoesNotExist:
            pass

    products = Product.objects.order_by().filter(**filters).distinct()

    if integration and integration.output_available:
        products = products.annotate(
            quantity=Sum('stock_item__quantity', filter=Q(stock_item__supplier__integration=integration)),
            correction=Sum('stock_item__correction', filter=Q(stock_item__supplier__integration=integration)),
            available=F('quantity') + F('correction')
        ).filter(available__gt=0)

    for product in products:
        context['product'] = product
        product.images = []
        if default_storage.exists(product.image_prefix):
            try:
                dirs, files = default_storage.listdir(product.image_prefix)
                if files is not None:
                    for file in sorted(files):
                        if file.endswith('.jpg') and not file.endswith('.s.jpg'):
                            product.images.append(file[:-4])
            except NotADirectoryError:
                pass
        if integration:
            if integration.output_with_images and len(product.images) == 0:
                yield ''
            if not integration.output_all:
                context['integration'] = ProductIntegration.objects.get(product=product, integration=integration)
            if integration.output_stock:
                context['stock'] = product.get_stock(integration=integration)
        yield t.render(context, request)

    context.pop('product', None)
    context.pop('integration', None)
    context.pop('stock', None)
    t = loader.get_template('xml/_{}_footer.xml'.format(template))
    yield t.render(context, request)


def products(request, integration=None, template=None, filters=None):
    if integration:
        integration = Integration.objects.filter(utm_source=integration).first()
        if integration is None:
            raise Http404("Does not exist")
    return StreamingHttpResponse(products_stream(request, integration, template, filters), content_type='text/xml; charset=utf-8')


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

    site_profile = SiteProfile.objects.get(site=Site.objects.get_current())
    context = {
        'stores': stores,
        'store_groups': store_groups,
        'city': site_profile.city
    }

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
    city = getattr(settings, 'SHOP_CITY_ID', None)
    if city:
        context['city'] = City.objects.get(pk=city)

    return render(request, 'service.html', context)


def catalog(request):
    context = {'root': Category.objects.get(slug=settings.MPTT_ROOT)}
    return render(request, 'catalog.html', context)


def category(request, path, instance):
    products = None
    gtm_list = None
    if not instance or not instance.active:
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

    if request.user.is_authenticated:
        favorites = Favorites.objects.filter(user=request.user).values_list('product', flat=True)
    else:
        favorites = []

    context = {
        'category': instance,
        'product_filter': product_filter,
        'products': products,
        'favorites': favorites,
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
                    if file.endswith('.jpg') and not file.endswith('.s.jpg'):
                        product.images.append(file[:-4])
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

    comparison_list = list(map(int, request.session.get('comparison_list', '0').split(',')))

    favorite = request.user.is_authenticated and Favorites.objects.filter(user=request.user, product=product).exists()

    if FACEBOOK_TRACKING:
        notify_view_content.delay(product.id, request.build_absolute_uri(),
                                  request.META.get('REMOTE_ADDR'), request.META['HTTP_USER_AGENT'])

    context = {
        'category': category,
        'product': product,
        'constituents': constituents,
        'accessories': product.related.filter(child_products__child_product__enabled=True, child_products__kind=ProductRelation.KIND_ACCESSORY),
        'similar': product.related.filter(child_products__child_product__enabled=True, child_products__kind=ProductRelation.KIND_SIMILAR),
        'gifts': product.related.filter(child_products__child_product__enabled=True, child_products__kind=ProductRelation.KIND_GIFT),
        'utm_source': request.GET.get('utm_source', None),
        'is_compared': product.id in comparison_list,
        'is_favorite': favorite
    }
    return render(request, 'product.html', context)


def product_stock(request, code):
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


def compare_product(request, code):
    product = get_object_or_404(Product, code=code)
    if product.categories.exists() and not product.breadcrumbs:
        raise Http404("Product does not exist")

    comparison_list = request.session.get('comparison_list', None)
    if comparison_list:
        product_ids = list(map(int, comparison_list.split(',')))
        if product.id not in product_ids:
            product_ids.append(product.id)
        request.session['comparison_list'] = ','.join(map(str, product_ids))
    else:
        request.session['comparison_list'] = str(product.id)

    return JsonResponse({})


def uncompare_product(request, code):
    product = get_object_or_404(Product, code=code)
    if product.categories.exists() and not product.breadcrumbs:
        raise Http404("Product does not exist")

    comparison_list = request.session.get('comparison_list', None)
    if comparison_list:
        product_ids = list(filter(lambda id: id != product.id, map(int, comparison_list.split(','))))
        if product_ids:
            request.session['comparison_list'] = ','.join(map(str, product_ids))
        else:
            del request.session['comparison_list']

    return JsonResponse({})


def compare_products(request, compare=None, kind=None):
    product_ids = list(map(int, request.session.get('comparison_list', '0').split(',')))

    if not compare:
        if kind:
            kind = get_object_or_404(ProductKind, pk=kind)
        else:
            try:
                product = Product.objects.get(pk=product_ids[-1])
                kind = product.kind.all()[0]
            except Product.DoesNotExist:
                kind = 0
        products = Product.objects.filter(pk__in=product_ids, kind=kind).values_list('id', flat=True)
        if products:
            return redirect('compare_products', compare=','.join(map(str, products)))
        else:
            return redirect('compare')

    all_kinds = ProductKind.objects.filter(product__in=product_ids).distinct()

    compare_ids = list(map(int, compare.split(',')))
    products = Product.objects.filter(pk__in=compare_ids)
    kinds = products.first().kind.all()
    if not len(kinds):
        return redirect('compare')
    kind = kinds[0]

    field_map = {}
    for field_id in kind.comparison:
        field = Product._meta.get_field(field_id)
        field_map[field_id] = capfirst(field.verbose_name) if hasattr(field, 'verbose_name') else capfirst(field.name)

    context = {
        'kind': kind,
        'kinds': all_kinds,
        'products': products,
        'field_map': field_map
    }
    return render(request, 'compare.html', context)


def compare_notice(request):
    comparison_list = request.session.get('comparison_list', None)
    count = 0
    if comparison_list:
        count = len(list(map(int, comparison_list.split(','))))
    context = {
        'count': count,
    }
    return render(request, 'compare_notice.html', context)


@login_required
def review_product(request, code):
    product = get_object_or_404(Product, code=code)
    if product.categories.exists() and not product.breadcrumbs:
        raise Http404("Product does not exist")
    context = {
        'target': product,
    }
    return render(request, 'reviews/post.html', context)
