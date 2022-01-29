from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

import mptt_urls

from . import views


urlpatterns = [
    # ex: /
    url(r'^$', views.index, name='index'),
    # ex: /search.xml
    url(r'^search\.xml$', views.products, {'templates': 'search', 'filters': None}, name='search_xml'),
    # ex: /full.xml
    url(r'^full\.xml$', views.products, {'templates': 'products', 'filters': None}, name='full'),
    # ex: /products.xml
    url(r'^products\.xml$', views.products, {'templates': 'products', 'filters': 'yandex'}, name='products'),
    # ex: /google.xml
    url(r'^google\.xml$', views.products, {'templates': 'google', 'filters': 'yandex'}, name='google'),
    # ex: /search/
    url(r'^search/$', views.search, name='search'),
    # ex: /catalog/
    url(r'^catalog/$', views.catalog, name='catalog'),
    # ex: /catalog/prinadlezhnosti/
    url(r'^catalog/(?P<path>.*)', mptt_urls.view(model='shop.models.Category', view='sewingworld.views.category', slug_field='slug', root=settings.MPTT_ROOT), name='category'),
    # ex: /products/JanomeEQ60.html
    url(r'^products/(?P<code>[-\.\w]+)\.html$', views.product, name='product'),
    # ex: /products/JanomeEQ60/review
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
    # ex: /service/
    url(r'^service/$', views.service, name='service'),
    # ex: /stores/
    url(r'^stores/$', views.stores, name='stores'),
    # ex: /stores/1/
    url(r'^stores/(?P<id>\d+)/$', views.store, name='store'),
    # /pages/*
    url(r'^pages/', include('django.contrib.flatpages.urls')),
    # /shop/*
    url(r'^shop/', include('shop.urls', namespace='shop')),
    url(r'^reviews/', include('reviews.urls')),
]

urlpatterns += staticfiles_urlpatterns()

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
