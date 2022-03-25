from django.contrib.sites.models import Site
from django.db import models

from shop.models import City


class SiteProfile(models.Model):
    site = models.OneToOneField(Site, related_name='profile', on_delete=models.CASCADE)
    title = models.CharField('название', max_length=255, blank=True)
    description = models.CharField('описание', max_length=255, blank=True)
    city = models.ForeignKey(City, verbose_name='город', blank=True, null=True, on_delete=models.PROTECT)
    phone = models.CharField('телефон', max_length=255, blank=True)
    managers = models.CharField('менеджеры заказов', max_length=255, blank=True, help_text='Можно несколько через запятую')
    order_prefix = models.CharField('префикс заказов', max_length=10, blank=True)

    class Meta:
        verbose_name = 'профиль сайта'
        verbose_name_plural = 'профили сайтов'

    def __str__(self):
        return self.title or self.site.name
