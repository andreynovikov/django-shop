from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from ajax_select import urls as ajax_select_urls

import mptt_urls

import shop

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
    # ex: /search/
    url(r'^search/$', views.search, name='search'),
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
    url(r'^blog/', include('zinnia.urls')),
    url(r'^comments/', include('django_comments.urls')),
    url(r'^autocomplete/', include('autocomplete_light.urls')),
    url(r'^admin/lookups/', include(ajax_select_urls)),
    url(r'^admin/import1c/$', shop.views.import_1c, name='import_1c'),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^admin/', include('massadmin.urls')),
]

urlpatterns += staticfiles_urlpatterns()

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [ url(r'^__debug__/', include(debug_toolbar.urls)) ]
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
