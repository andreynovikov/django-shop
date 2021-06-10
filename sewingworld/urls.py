from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.urls import path
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

import mptt_urls
import spirit.urls
from zinnia.sitemaps import EntrySitemap
from forum.sitemaps import ThreadSitemap

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


urlpatterns = [
    # ex: /
    url(r'^$', views.index, name='index'),
    # ex: /sitemap.xml
    url(r'^sitemap\.xml$', sitemap, {'sitemaps': sitemaps}, name='sitemap'),
    # ex: /search.xml
    url(r'^search\.xml$', views.products, {'templates': 'search', 'filters': None}, name='search_xml'),
    # ex: /full.xml
    url(r'^full\.xml$', views.products, {'templates': 'products', 'filters': None}, name='full'),
    # ex: /products.xml
    url(r'^products\.xml$', views.products, {'templates': 'products', 'filters': 'yandex'}, name='products'),
    # ex: /avito.xml
    url(r'^avito\.xml$', views.products, {'templates': 'avito', 'filters': 'avito'}, name='avito'),
    # ex: /beru.xml
    url(r'^beru\.xml$', views.products, {'templates': 'beru', 'filters': 'beru'}, name='beru'),
    # ex: /taxi.xml
    url(r'^taxi\.xml$', views.products, {'templates': 'beru', 'filters': 'taxi'}, name='taxi'),
    # ex: /mdbs.xml
    url(r'^mdbs\.xml$', views.products, {'templates': 'beru', 'filters': 'mdbs'}, name='mdbs'),
    # ex: /sber.xml
    url(r'^sber\.xml$', views.products, {'templates': 'sber', 'filters': 'sber'}, name='sber'),
    # ex: /google.xml
    url(r'^google\.xml$', views.products, {'templates': 'google', 'filters': 'google'}, name='google'),
    # ex: /cc-prym.xml
    url(r'^cc-prym\.xml$', views.products, {'templates': 'prym', 'filters': 'prym'}, name='cc-prym'),
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
    url(r'^beru/', include('beru.urls'), {'account': 'beru'}),
    url(r'^taxi/', include('beru.urls'), {'account': 'taxi'}),
    url(r'^mdbs/', include('beru.urls'), {'account': 'mdbs'}),
    url(r'^sber/', include('sber.urls')),
    url(r'^kassa/', include('yandex_kassa.urls')),
    url(r'^blog/', include('zinnia.urls')),
    url(r'^comments/', include('django_comments.urls')),
    url(r'^forum/', include(spirit.urls)),
    url(r'^reviews/', include('reviews.urls')),
    url(r'^oldforum/', include('forum.urls')),
    url(r'^lock_tokens/', include('lock_tokens.urls', namespace='lock-tokens')),
    path('admin/', admin.site.urls),
    url(r'^admin/', include('massadmin.urls')),
    url(r'^admin/', include('loginas.urls')),
]

urlpatterns += staticfiles_urlpatterns()

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [path('__debug__/', include(debug_toolbar.urls))]
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
