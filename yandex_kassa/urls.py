from django.urls import path

from . import views


app_name = 'yandex_kassa'

urlpatterns = [
    path('payment/<int:order_id>/', views.payment, name='payment'),
    path('callback/', views.callback),
    path('receipt/<int:order_id>/', views.receipt, name='receipt')
]
