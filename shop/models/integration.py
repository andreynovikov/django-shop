from django.contrib.postgres.fields import JSONField
from django.contrib.sites.models import Site
from django.db import models

from . import Product, Supplier

__all__ = [
    'Integration', 'ProductIntegration'
]


class Integration(models.Model):
    name = models.CharField('название', max_length=100)
    utm_source = models.CharField('источник', max_length=20)
    site = models.ForeignKey(Site, verbose_name='сайт', related_name='integrations', related_query_name='integration', on_delete=models.PROTECT)
    uses_api = models.BooleanField('использует API', default=False)
    uses_boxes = models.BooleanField('использует коробки', default=False)
    settings = JSONField('настройки', null=True, blank=True)
    admin_user_fields = JSONField('поля покупателя', null=True, blank=True)
    suppliers = models.ManyToManyField(Supplier, related_name='integrations', related_query_name='integration', verbose_name='поставщики', blank=True)
    products = models.ManyToManyField(Product, related_name='integrations', related_query_name='integration', through='ProductIntegration', blank=True)

    class Meta:
        verbose_name = 'интеграция'
        verbose_name_plural = 'интеграции'
        ordering = ['name']

    def __str__(self):
        return self.name


class ProductIntegration(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    integration = models.ForeignKey(Integration, on_delete=models.CASCADE)
    price = models.DecimalField('цена, руб', max_digits=10, decimal_places=2, default=0)
