from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from .models import Thread
from . import views


class ThreadSitemap(Sitemap):
    changefreq = 'never'
    protocol = 'https'
    priority = 0.2

    def items(self):
        return Thread.objects.filter(enabled=True)

    def lastmod(self, obj):
        return obj.mtime

    def location(self, obj):
        return reverse('forum:thread', args=[str(obj.pk)])
