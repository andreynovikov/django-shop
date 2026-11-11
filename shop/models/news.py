from django.contrib.sites.models import Site
from django.db import models
from django.utils import timezone

__all__ = ['News']


class News(models.Model):
    title = models.CharField('заголовок', max_length=255)
    image = models.ImageField('изображение', upload_to='news', blank=True,
                              width_field='image_width', height_field='image_height')
    image_width = models.IntegerField(null=True, blank=True)
    image_height = models.IntegerField(null=True, blank=True)
    content = models.TextField('содержимое')
    sites = models.ManyToManyField(Site, verbose_name='сайты', db_index=True)
    active = models.BooleanField('активная', db_index=True)
    publish_date = models.DateTimeField('дата публикации', default=timezone.now)

    class Meta:
        verbose_name = 'новость'
        verbose_name_plural = 'новости'
        ordering = ['-publish_date']

    def __str__(self):
        return self.title
