from django.urls import path

from shop import views


app_name = 'shop'

urlpatterns = [
    # ex: /shop/user/orders/8/bill/
    path('user/orders/<int:order_id>/<str:template_name>/', views.order_document, name='order_document'),
    # ex: /shop/warranty_card/
    path('warranty_card/', views.print_warranty_card, name='warranty_card'),
]
