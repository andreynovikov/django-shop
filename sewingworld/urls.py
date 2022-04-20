from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

import mptt_urls

from . import views


urlpatterns = [
    # ex: /
    url(r'^$', views.index, name='index'),
    # ex: /products.xml
    url(r'^products\.xml$', views.products, {'templates': 'products', 'filters': None}, name='products'),
    # ex: /catalog/
    url(r'^catalog/$', views.catalog, name='catalog'),
    # ex: /catalog/expand/1234
    url(r'^catalog/expand/(?P<product_id>\d+)/$', views.expand, name='expand'),
    # ex: /catalog/prinadlezhnosti/
    url(r'^catalog/(?P<path>.*)', mptt_urls.view(model='shop.models.Category', view='sewingworld.views.category', slug_field='slug', root=settings.MPTT_ROOT), name='category'),
    # ex: /products/JanomeEQ60/
    url(r'^products/(?P<code>[-\.\w]+)/$', views.product, name='product'),

    url(r'^pages/', include('django.contrib.flatpages.urls')),
    url(r'^shop/', include('shop.urls', namespace='shop')),
]

urlpatterns += staticfiles_urlpatterns()
