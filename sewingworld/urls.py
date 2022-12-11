from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.urls import path
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

import mptt_urls
from zinnia.sitemaps import EntrySitemap
from forum.sitemaps import ThreadSitemap
from rest_framework.routers import DefaultRouter

from reviews.api import ReviewViewSet

from shop.models.integration import Integration

from . import api
from . import views
from .sitemaps import StaticViewSitemap, ProductSitemap, CategorySitemap, SalesActionSitemap, StoreSitemap, FlatPageSitemap


sitemaps = {
    'static': StaticViewSitemap,
    'products': ProductSitemap,
    'categories': CategorySitemap,
    'sales actions': SalesActionSitemap,
    'stores': StoreSitemap,
    'pages': FlatPageSitemap,
    'blog': EntrySitemap,
    'threads': ThreadSitemap
}

router = DefaultRouter()
router.register(r'sites', api.SiteProfileViewSet, basename='site')
router.register(r'baskets', api.BasketViewSet, basename='basket')
router.register(r'orders', api.OrderViewSet, basename='order')
router.register(r'favorites', api.FavoritesViewSet, basename='favorite')
router.register(r'comparisons', api.ComparisonsViewSet, basename='comparison')
router.register(r'categories', api.CategoryViewSet, basename='category')
router.register(r'products', api.ProductViewSet, basename='product')
router.register(r'kinds', api.ProductKindViewSet, basename='kind')
router.register(r'users', api.UserViewSet, basename='user')
router.register(r'pages', api.FlatPageViewSet, basename='page')
router.register(r'news', api.NewsViewSet, basename='news')
router.register(r'stores', api.StoreViewSet, basename='store')
router.register(r'servicecenters', api.ServiceCenterViewSet, basename='servicecenter')
router.register(r'reviews', ReviewViewSet, basename='review')
router.register(r'reviews/(?P<model>[a-z]+.[a-z]+)/(?P<identifier>[^/.]+)', ReviewViewSet, basename='review')

urlpatterns = [
    # ex: /
    url(r'^$', views.index, name='index'),
    # Rest API
    path('api/v0/', include(router.urls)),
    path('api/v0/csrf/', api.CsrfTokenView.as_view()),
    path('api/v0/warrantycard/<str:code>/', api.WarrantyCardView.as_view()),
    # ex: /sitemap.xml
    url(r'^sitemap\.xml$', sitemap, {'sitemaps': sitemaps}, name='sitemap'),
    # ex: /search.xml
    url(r'^search\.xml$', views.products, {'template': 'search', 'filters': None}, name='search_xml'),
    # ex: /full.xml
    url(r'^full\.xml$', views.products, {'template': 'products', 'filters': None}, name='full'),
    # ex: /products.xml
    url(r'^products\.xml$', views.products, {'template': 'products', 'filters': 'yandex'}, name='products'),
    # ex: /cc-prym.xml
    url(r'^cc-prym\.xml$', views.products, {'template': 'prym', 'filters': 'prym'}, name='cc-prym'),
    # ex: /beru.xml
    path('<slug:integration>.xml', views.products),
    # ex: /stock_avito.csv
    url(r'^stock_avito\.csv$', views.stock, name='stock'),
    # ex: /search/
    url(r'^search/$', views.search, name='search'),
    # ex: /catalog/
    url(r'^catalog/$', views.catalog, name='catalog'),
    # ex: /catalog/prinadlezhnosti/
    url(r'^catalog/(?P<path>.*)', mptt_urls.view(model='shop.models.Category', view='sewingworld.views.category', slug_field='slug', root=settings.MPTT_ROOT), name='category'),
    # ex: /products/JanomeEQ60.html
    url(r'^products/(?P<code>[-\.\w]+)\.html$', views.product, name='product'),
    # ex: /products/JanomeEQ60/stock/
    url(r'^products/(?P<code>[-\.\w]+)/stock/$', views.product_stock, name='product_stock'),
    # ex: /products/JanomeEQ60/review/
    url(r'^products/(?P<code>[-\.\w]+)/review/$', views.review_product, name='review_product'),
    # ex: /products/JanomeEQ60/compare/
    url(r'^products/(?P<code>[-\.\w]+)/compare/$', views.compare_product, name='compare_product'),
    # ex: /products/JanomeEQ60/uncompare/
    url(r'^products/(?P<code>[-\.\w]+)/uncompare/$', views.uncompare_product, name='uncompare_product'),
    # ex: /compare/notice/
    url(r'^compare/notice/$', views.compare_notice, name='compare_notice'),
    # ex: /compare/kind/1/
    url(r'^compare/kind/(?P<kind>\d+)/$', views.compare_products, name='compare_kind'),
    # ex: /compare/1,2,3/
    url(r'^compare/(?P<compare>[\d,]+)/$', views.compare_products, name='compare_products'),
    # ex: /compare/
    url(r'^compare/$', views.compare_products, name='compare'),
    # ex: /actions/
    url(r'^actions/$', views.sales_actions, name='sales_actions'),
    # ex: /actions/trade-in/
    url(r'^actions/(?P<slug>[-\.\w]+)/$', views.sales_action, name='sales_action'),
    # ex: /stores/
    url(r'^stores/$', views.stores, name='stores'),
    # ex: /stores/1/
    url(r'^stores/(?P<id>\d+)/$', views.store, name='store'),
    # ex: /service/
    url(r'^service/$', views.service, name='service'),
    # /pages/*
    url(r'^pages/', include('django.contrib.flatpages.urls')),
    # /shop/*
    url(r'^shop/', include('shop.urls')),

    url(r'^sber/', include('sber.urls')),
    url(r'^kassa/', include('yandex_kassa.urls')),
    url(r'^blog/', include('zinnia.urls')),
    url(r'^comments/', include('django_comments.urls')),
    url(r'^reviews/', include('reviews.urls')),
    url(r'^oldforum/', include('forum.urls')),

    path('admin/', admin.site.urls),
    url(r'^admin/', include('massadmin.urls')),
    url(r'^admin/', include('loginas.urls')),
]

# Add Yandex integrations
for integration in Integration.objects.filter(uses_api=True):
    if integration.settings:
        ym_campaign = integration.settings.get('ym_campaign', None)
        if ym_campaign is not None:
            urlpatterns.append(path(integration.utm_source + '/', include('beru.urls'), {'account': integration.utm_source}))

urlpatterns += staticfiles_urlpatterns()

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [path('__debug__/', include(debug_toolbar.urls))]
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
