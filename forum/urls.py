from django.conf.urls import url

from . import views

app_name = 'forum'

urlpatterns = [
    # ex /
    url(r'^$', views.index, name='index'),
    # ex: /topic/8/
    url(r'^topic/(?P<id>\d+)/$', views.topic, name='topic'),
    # ex: /thread/8/
    url(r'^thread/(?P<id>\d+)/$', views.thread, name='thread'),
]
