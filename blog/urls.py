from django.urls import include, path

from rest_framework.routers import DefaultRouter

from . import api


router = DefaultRouter()
router.register(r'entries', api.EntryViewSet, basename='entry')
router.register(r'categories', api.CategoryViewSet, basename='category')

urlpatterns = [
    path('', include(router.urls)),
    path('tags/', api.TagView.as_view())
]
