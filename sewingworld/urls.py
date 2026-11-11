from django.conf import settings
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import include, path

from rest_framework.routers import DefaultRouter
from drf_spectacular.views import SpectacularAPIView
from two_factor.urls import urlpatterns as tf_urls

from reviews.api import ReviewViewSet
from forum.api import TopicViewSet, ThreadViewSet

from .api import catalog, content, integrations, orders, shopping, users
from . import views


if settings.IS_ADMIN_SITE:
    urlpatterns = [
        path('', include(tf_urls)),
        path('admin/', include('massadmin.urls')),
        path('admin/', include('loginas.urls')),
        path('admin/', admin.site.urls),
    ]
else:
    router = DefaultRouter()
    router.register(r'sites', content.SiteProfileViewSet, basename='site')
    router.register(r'baskets', shopping.BasketViewSet, basename='basket')
    router.register(r'orders', orders.OrderViewSet, basename='order')
    router.register(r'favorites', shopping.FavoritesViewSet, basename='favorite')
    router.register(r'comparisons', shopping.ComparisonsViewSet, basename='comparison')
    router.register(r'categories', catalog.CategoryViewSet, basename='category')
    router.register(r'products', catalog.ProductViewSet, basename='product')
    router.register(r'stocks', integrations.StockViewSet, basename='stock')
    router.register(r'kinds', catalog.ProductKindViewSet, basename='kind')
    router.register(r'serials', orders.SerialViewSet, basename='serial')
    router.register(r'users', users.UserViewSet, basename='user')
    router.register(r'pages', content.FlatPageViewSet, basename='page')
    router.register(r'news', content.NewsViewSet, basename='news')
    router.register(r'salesactions', content.SalesActionViewSet, basename='salesaction')
    router.register(r'adverts', content.AdvertViewSet, basename='advert')
    router.register(r'stores', content.StoreViewSet, basename='store')
    router.register(r'servicecenters', content.ServiceCenterViewSet, basename='servicecenter')
    router.register(r'integrations', integrations.IntegrationViewSet, basename='integration')
    router.register(r'reviews', ReviewViewSet, basename='review')
    router.register(r'reviews/(?P<model>[a-z]+.[a-z]+)/(?P<identifier>[^/.]+)', ReviewViewSet, basename='model-review')
    router.register(r'forum/topics', TopicViewSet, basename='topic')
    router.register(r'forum/threads', ThreadViewSet, basename='thread')

    urlpatterns = [
        # Rest API
        path('api/v0/', include(router.urls)),
        path('api/v0/schema/', SpectacularAPIView.as_view(), name='schema'),
        path('api/v0/blog/', include('blog.urls')),
        path('api/v0/csrf/', users.CsrfTokenView.as_view()),
        path('api/v0/warrantycard/<str:code>/', orders.WarrantyCardView.as_view()),
        # ex: /stock_avito.csv
        path('stock_avito.csv', views.stock, name='stock'),
        # /shop/*
        path('shop/', include('shop.urls')),
        path('sber/', include('sber.urls')),
        path('kassa/', include('yandex_kassa.urls')),

        path('', include('django_prometheus.urls')),
    ]

urlpatterns += staticfiles_urlpatterns()
