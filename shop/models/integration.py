from django.contrib.sites.models import Site
from django.db import models

from . import Product, Supplier, Contractor

__all__ = [
    'Integration', 'ProductIntegration'
]


class Integration(models.Model):
    name = models.CharField('название', max_length=100)
    utm_source = models.CharField('источник', max_length=20)
    site = models.ForeignKey(Site, verbose_name='сайт', related_name='integrations', related_query_name='integration', on_delete=models.PROTECT)
    output_template = models.CharField('шаблон выгрузки', max_length=20)
    output_all = models.BooleanField('выгражать все', default=False, help_text="Выгружать товары по дереву категорий, а не по флагу интеграции")
    output_available = models.BooleanField('выгражать только в наличии', default=False)
    output_with_images = models.BooleanField('выгражать только с картинками', default=False)
    output_stock = models.BooleanField('выгражать остатки', default=False)
    uses_api = models.BooleanField('использует API', default=False)
    uses_boxes = models.BooleanField('использует коробки', default=False)
    settings = models.JSONField('настройки', null=True, blank=True)
    admin_user_fields = models.JSONField('поля покупателя', null=True, blank=True)
    buyer = models.ForeignKey(Contractor, verbose_name='покупатель 1С по-умолчанию', related_name='+', blank=True, null=True, on_delete=models.SET_NULL)
    wirehouse = models.ForeignKey(Supplier, verbose_name='склад отгрузки по-умолчанию', related_name='+', blank=True, null=True,
                                  on_delete=models.SET_NULL, limit_choices_to={'show_in_list': True})
    suppliers = models.ManyToManyField(Supplier, verbose_name='поставщики', related_name='integrations', related_query_name='integration', blank=True)
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
