from django.urls import include, path

from rest_framework.routers import DefaultRouter

from . import api


router = DefaultRouter()
router.register(r'entries', api.EntryViewSet, basename='entry')
router.register(r'tags', api.TagViewSet, basename='tag')
router.register(r'categories', api.CategoryViewSet, basename='category')

app_name = 'blog'

urlpatterns = [
    path('api/v0/', include(router.urls)),
    path('<int:year>/<int:month>/<int:day>/<slug:slug>/', api.EntryViewSet.as_view({'get': 'retrieve'}), name='entry_detail'),  # used for path reversing, frontend will intercept it
    path('<str:token>/', api.EntryViewSet.as_view({'get': 'retrieve'}), name='entry_shortlink')  # used for path reversing, frontend will intercept it
]
