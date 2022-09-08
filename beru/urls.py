from django.urls import path

from . import views


urlpatterns = [
    path('stocks', views.stocks),
    path('cart', views.cart),
    path('order/accept', views.accept_order),
    path('order/status', views.order_status),
]
