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
    url(r'^search\.xml$', views.search_xml, name='search_xml'),
    # ex: /products.xml
    url(r'^products\.xml$', views.products, {'template': 'products.xml'}, name='products'),
    # ex: /google.xml
    url(r'^google\.xml$', views.products, {'template': 'google.xml'}, name='google'),
    # ex: /catalog/
    url(r'^catalog/$', views.catalog, name='catalog'),
    # ex: /catalog/prinadlezhnosti/
    url(r'^catalog/(?P<path>.*)', mptt_urls.view(model='shop.models.Category', view='sewingworld.views.category', slug_field='slug', root=settings.MPTT_ROOT), name='category'),
    # ex: /products/JanomeEQ60.html
    url(r'^products/(?P<code>[-\w]+)\.html$', views.product, name='product'),
    # /pages/*
    url(r'^pages/', include('django.contrib.flatpages.urls')),
    # /shop/*
    url(r'^shop/', include('shop.urls', namespace='shop')),
]

urlpatterns += staticfiles_urlpatterns()

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
