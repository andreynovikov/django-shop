from django.contrib.postgres.fields import ArrayField
from django.contrib.sites.models import Site
from django.db import models

from shop.models import City


class SiteProfile(models.Model):
    site = models.OneToOneField(Site, related_name='profile', on_delete=models.CASCADE)
    title = models.CharField('название', max_length=255, blank=True)
    description = models.CharField('описание', max_length=255, blank=True)
    category_root_slug = models.CharField('slug корневой категории', max_length=30, blank=True)
    product_thumbnail_size = models.PositiveSmallIntegerField('размер малого изображения товара', default=200)
    product_small_thumbnail_size = models.PositiveSmallIntegerField('размер супермалого изображения товара', default=80)
    city = models.ForeignKey(City, verbose_name='город', blank=True, null=True, on_delete=models.PROTECT)
    phone = models.CharField('телефон', max_length=255, blank=True)
    manager_emails = models.CharField('адреса менеджеров', max_length=255, blank=True, help_text='Можно несколько через запятую')
    manager_phones = models.CharField('телефоны менеджеров', max_length=255, blank=True, help_text='Можно несколько через запятую')
    order_prefix = models.CharField('префикс заказов', max_length=10, blank=True)
    aliases = ArrayField(models.CharField(max_length=100), verbose_name='домены-ссылки', blank=True, null=True)

    class Meta:
        verbose_name = 'профиль сайта'
        verbose_name_plural = 'профили сайтов'

    def __str__(self):
        return self.title or self.site.name
