from django.urls import include, path

from rest_framework.routers import DefaultRouter

from . import api


router = DefaultRouter()
router.register(r'entries', api.EntryViewSet, basename='entry')

urlpatterns = [
    path('api/v0/', include(router.urls))
]
