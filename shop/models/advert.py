from django.contrib.sites.models import Site
from django.db import models

from mptt.models import TreeManyToManyField

from . import Category

__all__ = ['Advert']


class Advert(models.Model):
    name = models.CharField('название', max_length=100)
    place = models.CharField('место', max_length=100, db_index=True)
    sites = models.ManyToManyField(Site, verbose_name='сайты', db_index=True)
    categories = TreeManyToManyField(Category, related_name='adverts',
                                     related_query_name='advert', verbose_name='категории', blank=True)
    active = models.BooleanField('активная', db_index=True)
    image = models.ImageField('изображение', upload_to='posters', blank=True)
    big_image = models.ImageField('больщое изображение', upload_to='posters', blank=True)
    content = models.TextField('содержимое')
    order = models.PositiveIntegerField()

    class Meta:
        verbose_name = 'реклама'
        verbose_name_plural = 'рекламы'
        ordering = ['order']

    def __str__(self):
        return self.name
