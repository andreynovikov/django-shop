from django.urls import include, path

from rest_framework.routers import DefaultRouter

from . import api


router = DefaultRouter()
router.register(r'entries', api.EntryViewSet, basename='entry')
router.register(r'tags', api.TagViewSet, basename='tag')
router.register(r'categories', api.CategoryViewSet, basename='category')

urlpatterns = [
    path('api/v0/', include(router.urls))
]
