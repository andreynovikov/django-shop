from django.conf import settings
from django.contrib.sitemaps import Sitemap
from django.contrib.sites.models import Site
from django.urls import reverse

from shop.models import Product, Category, Store, SalesAction


class StaticViewSitemap(Sitemap):
    priority = 0.5
    changefreq = 'weekly'
    protocol = 'https'

    def items(self):
        return ['index', 'catalog', 'service']

    def location(self, item):
        return reverse(item)


class ProductSitemap(Sitemap):
    changefreq = 'weekly'
    protocol = 'https'

    def items(self):
        root = Category.objects.get(slug=settings.MPTT_ROOT)
        return Product.objects.filter(enabled=True, categories__in=root.get_descendants(include_self=True)).distinct()
    """
    def lastmod(self, obj):
        return obj.pub_date
    """


class CategorySitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.8
    protocol = 'https'

    def items(self):
        root = Category.objects.get(slug=settings.MPTT_ROOT)
        return root.get_descendants(include_self=True)


class StoreSitemap(Sitemap):
    changefreq = 'monthly'
    priority = 0.6
    protocol = 'https'

    def items(self):
        return Store.objects.filter(enabled=True)


class SalesActionSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.7
    protocol = 'https'

    def items(self):
        return SalesAction.objects.filter(active=True, show_in_list=True, sites=Site.objects.get_current())


class FlatPageSitemap(Sitemap):
    def items(self):
        site = Site.objects.get_current()
        return site.flatpage_set.filter(registration_required=False, template_name='')

    def location(self, item):
        return reverse('django.contrib.flatpages.views.flatpage', args=[item.url[1:]])
