from django.conf.urls import url

from . import views

urlpatterns = [
    # ex: /thread/8/
    url(r'^thread/(?P<id>\d+)/$', views.thread, name='thread'),
]
