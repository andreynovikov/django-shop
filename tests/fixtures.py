"""
Shop data for API tests. Products are made without Product.save(), whose signals reach the marketplaces.
"""
from django.conf import settings
from django.contrib.sites.models import Site

from sewingworld.models import SiteProfile
from shop.models import Category, City, Country, Currency, Manufacturer, Product


def add_products(*ids, **fields):
    """ Products with these ids, each with the given fields """
    Currency.objects.get_or_create(code=643, defaults={'name': 'RUB'})
    Manufacturer.objects.get_or_create(pk=49, defaults={'code': 'test', 'name': 'Test'})
    Country.objects.get_or_create(pk=1, defaults={'name': 'Россия', 'ename': 'Russia'})
    return Product.objects.bulk_create(Product(**{'pk': pk, 'code': f'p{pk}', 'title': f'Товар {pk}', **fields}) for pk in ids)


def add_product(pk, sites=(), categories=(), **fields):
    """
    A product on sale on these sites, in these categories. It keeps its price when the code saves it,
    and has its stock counted already: reading instock of a product with num < 0 counts it and saves the product.
    """
    fields.setdefault('price', 1000)
    fields.setdefault('cur_price', fields['price'])
    fields.setdefault('num', 5)
    [product] = add_products(pk, **fields)
    product.sites.set(sites)
    product.categories.set(categories)
    return product


def add_catalog(site=None):
    """ Root of the site's catalog. The site needs a profile, see clients.add_storefront_key(). """
    root = Category.objects.create(name='Каталог', slug=settings.MPTT_ROOT)
    SiteProfile.objects.filter(site=site or Site.objects.get_current()).update(root_category=root)
    return root


def add_city(name='Москва'):
    country, _ = Country.objects.get_or_create(pk=1, defaults={'name': 'Россия', 'ename': 'Russia'})
    return City.objects.create(country=country, name=name)


def add_marketplace_sites():
    """ Saving a product with stock to report, as adding it to an order does, looks up the Ozon and Wildberries sites """
    for domain in ('ozon.ru', 'wildberries.ru'):
        Site.objects.get_or_create(domain=domain, defaults={'name': domain})
