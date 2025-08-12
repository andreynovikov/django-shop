from django.urls import include, path
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from two_factor.urls import urlpatterns as tf_urls


urlpatterns = [
    path('', include(tf_urls)),
    path('admin/', include('massadmin.urls')),
    path('admin/', include('loginas.urls')),
    path('admin/', admin.site.urls),
]

urlpatterns += staticfiles_urlpatterns()
