from django.urls import path

from . import views


urlpatterns = [
    path('<int:integration_id>/notification', views.notification, name='beru-notification'),
]
