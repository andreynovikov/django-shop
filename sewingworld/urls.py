from django.urls import include, path
# from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from rest_framework.routers import DefaultRouter

from reviews.api import ReviewViewSet
from forum.api import TopicViewSet, ThreadViewSet

from . import api
from . import views


router = DefaultRouter()
router.register(r'sites', api.SiteProfileViewSet, basename='site')
router.register(r'baskets', api.BasketViewSet, basename='basket')
router.register(r'orders', api.OrderViewSet, basename='order')
router.register(r'favorites', api.FavoritesViewSet, basename='favorite')
router.register(r'comparisons', api.ComparisonsViewSet, basename='comparison')
router.register(r'categories', api.CategoryViewSet, basename='category')
router.register(r'products', api.ProductViewSet, basename='product')
router.register(r'stocks', api.StockViewSet, basename='stock')
router.register(r'kinds', api.ProductKindViewSet, basename='kind')
router.register(r'serials', api.SerialViewSet, basename='serial')
router.register(r'users', api.UserViewSet, basename='user')
router.register(r'pages', api.FlatPageViewSet, basename='page')
router.register(r'news', api.NewsViewSet, basename='news')
router.register(r'salesactions', api.SalesActionViewSet, basename='salesaction')
router.register(r'adverts', api.AdvertViewSet, basename='advert')
router.register(r'stores', api.StoreViewSet, basename='store')
router.register(r'servicecenters', api.ServiceCenterViewSet, basename='servicecenter')
router.register(r'integrations', api.IntegrationViewSet, basename='integration')
router.register(r'reviews', ReviewViewSet, basename='review')
router.register(r'reviews/(?P<model>[a-z]+.[a-z]+)/(?P<identifier>[^/.]+)', ReviewViewSet, basename='review')
router.register(r'forum/topics', TopicViewSet, basename='topic')
router.register(r'forum/threads', ThreadViewSet, basename='thread')

urlpatterns = [
    # Rest API
    path('api/v0/', include(router.urls)),
    path('api/v0/blog/', include('blog.urls')),
    path('api/v0/csrf/', api.CsrfTokenView.as_view()),
    path('api/v0/warrantycard/<str:code>/', api.WarrantyCardView.as_view()),
    # ex: /stock_avito.csv
    path('stock_avito.csv', views.stock, name='stock'),
    # /shop/*
    path('shop/', include('shop.urls')),
    path('sber/', include('sber.urls')),
    path('kassa/', include('yandex_kassa.urls')),
    path('notifications/', include('django_nyt.urls')),
    path('wiki/', include('wiki.urls')),

    # path('admin/', include('massadmin.urls')),
    # path('admin/', include('loginas.urls')),
    # path('admin/', admin.site.urls),
    path('', include('django_prometheus.urls')),
]

urlpatterns += staticfiles_urlpatterns()
