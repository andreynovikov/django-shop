from django.conf.urls import url

from shop import views


app_name = 'shop'

urlpatterns = [
    # ex: /shop/
    url(r'^$', views.index, name='index'),
    # ex: /promo/
    url(r'^promo/$', views.view_promo, name='promo'),
    # ex: /shop/basket/
    url(r'^basket/$', views.view_basket, name='basket'),
    # ex: /shop/basket/empty/
    url(r'^basket/empty/$', views.view_empty_basket, name='empty'),
    # ex: /shop/basket/notice/
    url(r'^basket/notice/$', views.view_basket_notice, name='notice'),
    # ex: /shop/basket/notice_new/
    url(r'^basket/notice_new/$', views.view_basket_notice_new, name='notice_new'),
    # ex: /shop/basket/extnotice/
    url(r'^basket/extnotice/$', views.view_basket_extnotice, name='extnotice'),
    # ex: /shop/basket/update/5/
    url(r'^basket/update/(?P<product_id>\d+)/$', views.update_basket, name='update'),
    # ex: /shop/basket/add/5/
    url(r'^basket/add/(?P<product_id>\d+)/$', views.add_to_basket, name='add'),
    # ex: /shop/basket/delete/5/
    url(r'^basket/delete/(?P<product_id>\d+)/$', views.delete_from_basket, name='delete'),
    # ex: /shop/basket/unbind/
    url(r'^basket/unbind/$', views.unbind, name='unbind'),
    # ex: /shop/basket/authorize/
    url(r'^basket/authorize/$', views.authorize, name='authorize'),
    # ex: /shop/order/confirm/
    url(r'^order/confirm/$', views.confirm_order, name='confirm'),
    # ex: /shop/order/confirm/8/
    url(r'^order/confirm/(?P<order_id>\d+)/$', views.confirm_order, name='confirm'),
    # ex: /shop/order/update/
    url(r'^order/update/(?P<order_id>\d+)/$', views.update_order, name='update_order'),
    # ex: /shop/user/register/
    url(r'^user/register/$', views.register_user, name='register'),
    # ex: /shop/user/login/
    url(r'^user/login/$', views.login_user, name='login'),
    # ex: /shop/user/logout/
    url(r'^user/logout/$', views.logout_user, name='logout'),
    # ex: /shop/user/update/
    url(r'^user/update/$', views.update_user, name='update_user'),
    # ex: /shop/user/resetpassword/
    url(r'^user/resetpassword/$', views.reset_password, name='reset_password'),
    # ex: /shop/user/orders/
    url(r'^user/orders/$', views.orders, name='user_orders'),
    # ex: /shop/user/orders/8/
    url(r'^user/orders/(?P<order_id>\d+)/$', views.order, name='order'),
    # ex: /shop/user/orders/8/bill/
    url(r'^user/orders/(?P<order_id>\d+)/(?P<template_name>[a-z]+)/$', views.order_document, name='order_document'),
]
