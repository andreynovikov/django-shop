from django.contrib.sites.models import Site
from django.db import models
from django.urls import reverse

__all__ = ['SalesAction']


class SalesAction(models.Model):
    name = models.CharField('название', max_length=100)
    slug = models.CharField(max_length=100, db_index=True)
    sites = models.ManyToManyField(Site, verbose_name='сайты', db_index=True)
    active = models.BooleanField('активная')
    show_in_list = models.BooleanField('показывать в списке', default=True)
    show_products = models.BooleanField('показывать список товаров', default=True)
    notice = models.CharField('уведомление', max_length=50, blank=True)
    brief = models.TextField('описание', blank=True)
    description = models.TextField('статья', blank=True)
    image = models.ImageField('изображение', upload_to='actions', blank=True,
                              width_field='image_width', height_field='image_height')
    image_width = models.IntegerField(null=True, blank=True)
    image_height = models.IntegerField(null=True, blank=True)
    order = models.PositiveIntegerField()

    class Meta:
        verbose_name = 'акция'
        verbose_name_plural = 'акции'
        ordering = ['order']

    def get_absolute_url(self):
        return reverse('sales_action', args=[self.slug])

    def __str__(self):
        return self.name
