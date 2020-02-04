from django.http import Http404, StreamingHttpResponse
from django.conf import settings
from django.shortcuts import render, get_object_or_404
from django.core.files.storage import default_storage
from django.contrib.sites.models import Site
from django.template import loader

from haystack.forms import SearchForm
from haystack.views import SearchView as BaseSearchView

from sewingworld.models import SiteProfile
from shop.models import Category, Product, Basket, ProductRelation, ProductSet, \
    Manufacturer, SalesAction, Store, ServiceCenter
from shop.filters import get_product_filter


def ensure_session(request):
    if hasattr(request, 'session') and not request.session.session_key:
        request.session.save()
        request.session.modified = True


def index(request):
    ensure_session(request)
    products = None
    instance = Category.objects.get(slug='nitki-dor-tak')
    order = instance.product_order.split(',')
    products = instance.products.filter(enabled=True).order_by(*order)
    basket, created = Basket.objects.get_or_create(session_id=request.session.session_key)
    quantities = {item.product: item.quantity for item in basket.items.all()}
    products = map(lambda p: (p, basket.product_cost(p), quantities.get(p, 0)), products)
    context = {
        'products': products,
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
        categories[child.pk] = child.pk
        descendants = child.get_descendants()
        for descendant in descendants:
            categories[descendant.pk] = child.pk
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

    site_profile = SiteProfile.objects.get(site=Site.objects.get_current())
    context = {
        'services': services,
        'service_groups': service_groups,
        'city': site_profile.city
    }

    return render(request, 'service.html', context)


def catalog(request):
    context = {'root': Category.objects.get(slug=settings.MPTT_ROOT)}
    return render(request, 'catalog.html', context)


def category(request, path, instance):
    ensure_session(request)
    products = None
    gtm_list = None
    if not instance or not instance.active:
        raise Http404("Category does not exist")
    filters = {
        'enabled': True,
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

    basket, created = Basket.objects.get_or_create(session_id=request.session.session_key)
    quantities = {item.product: item.quantity for item in basket.items.all()}

    products = map(lambda p: (p, basket.product_cost(p), quantities.get(p, 0)), products)

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


def review_product(request, code):
    product = get_object_or_404(Product, code=code)
    if product.categories.exists() and not product.breadcrumbs:
        raise Http404("Product does not exist")

    context = {
        'target': product,
    }
    return render(request, 'reviews/post.html', context)


class SearchView(BaseSearchView):
    def __init__(self, *args, **kwargs):
        super(SearchView, self).__init__(form_class=SearchForm)

    def get_queryset(self):
        queryset = super(SearchView, self).get_queryset()
        return queryset.filter(enabled=True)

    def get_results(self):
        """
        Fetches the results via the form. Returns an empty list if there's no query to search with.
        """
        results = self.form.search()
        basket, created = Basket.objects.get_or_create(session_id=self.request.session.session_key)
        quantities = {item.product: item.quantity for item in basket.items.all()}
        return list(map(lambda r:(r,basket.product_cost(r.object),quantities.get(r.object, 0)), results))

    def __call__(self, request):
        ensure_session(request)
        return super(SearchView, self).__call__(request)
