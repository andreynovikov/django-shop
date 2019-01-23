from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.urls import path
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

import mptt_urls
import spirit.urls

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
    # ex: /cc-prym.xml
    url(r'^cc-prym\.xml$', views.products, {'template': 'prym.xml'}, name='cc-prym'),
    # ex: /search/
    url(r'^search/$', views.search, name='search'),
    # ex: /catalog/
    url(r'^catalog/$', views.catalog, name='catalog'),
    # ex: /catalog/prinadlezhnosti/
    url(r'^catalog/(?P<path>.*)', mptt_urls.view(model='shop.models.Category', view='sewingworld.views.category', slug_field='slug', root=settings.MPTT_ROOT), name='category'),
    # ex: /products/JanomeEQ60.html
    url(r'^products/(?P<code>[-\.\w]+)\.html$', views.product, name='product'),
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
    url(r'^shop/', include('shop.urls', namespace='shop')),
    url(r'^blog/', include('zinnia.urls')),
    url(r'^comments/', include('django_comments.urls')),
    url(r'^forum/', include(spirit.urls)),
    url(r'^oldforum/', include('forum.urls')),
    url(r'^lock_tokens/', include('lock_tokens.urls', namespace='lock-tokens')),
    path('admin/', admin.site.urls),
    #url(r'^admin/', include(admin.site.urls)),
    #url(r'^admin/', include('massadmin.urls')),
    url(r'^admin/', include('loginas.urls')),
]

urlpatterns += staticfiles_urlpatterns()

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [ path('__debug__/', include(debug_toolbar.urls)) ]
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
