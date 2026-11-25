from django.urls import path

from . import views


urlpatterns = [
    path('notifications/<int:integration_id>/', views.notifications, name='ozon-notifications'),
]
