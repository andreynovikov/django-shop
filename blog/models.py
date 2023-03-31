import string

from django.conf import settings
from django.contrib.sites.models import Site
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.html import linebreaks

from tagging.fields import TagField

from .preview import HTMLPreview


BASE36_ALPHABET = string.digits + string.ascii_uppercase


def base36(value):
    result = ''
    while value:
        value, i = divmod(value, 36)
        result = BASE36_ALPHABET[i] + result
    return result


class Category(models.Model):
    title = models.CharField('название', max_length=255)
    slug = models.SlugField('слаг', unique=True, max_length=255, help_text='Используется для формирования URL')
    description = models.TextField('описание', blank=True)

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'категории'
        ordering = ['title']

    def __str__(self):
        return self.title


class Entry(models.Model):
    DRAFT = 1
    HIDDEN = 2
    PUBLISHED = 99
    STATUS_CHOICES = (
        (DRAFT, 'черновик'),
        (HIDDEN, 'спрятанная'),
        (PUBLISHED, 'опубликована')
    )

    title = models.CharField('заголовок', max_length=255)
    slug = models.SlugField('слаг', max_length=255, unique_for_date='publication_date', help_text='Используется для формирования URL')
    status = models.IntegerField('статус', db_index=True, choices=STATUS_CHOICES, default=DRAFT)
    sites = models.ManyToManyField(Site, verbose_name='сайты', db_index=True)
    publication_date = models.DateTimeField('дата публикации', db_index=True, default=timezone.now, help_text='Используется для формирования URL')
    created = models.DateTimeField('дата создания', auto_now_add=True)
    modified = models.DateTimeField('дата обновления', auto_now=True)
    content = models.TextField('содержимое')
    image = models.ImageField('изображение', blank=True, upload_to='blog', width_field='image_width', height_field='image_height')
    image_width = models.IntegerField(null=True)
    image_height = models.IntegerField(null=True)
    image_caption = models.TextField('подпись', blank=True)
    related = models.ManyToManyField('self', blank=True, verbose_name='связанные записи')
    featured = models.BooleanField('популярная', default=False)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, on_delete=models.RESTRICT, verbose_name='автор')
    categories = models.ManyToManyField(Category, blank=True, related_name='entries', verbose_name='категории')
    tags = TagField('тэги')

    class Meta:
        verbose_name = 'запись'
        verbose_name_plural = 'записи'
        ordering = ['-publication_date']

    def __str__(self):
        return self.title

    @property
    def html_content(self):
        if not self.content:
            return ''
        if '</p>' not in self.content:
            return linebreaks(self.content)
        return self.content

    @property
    def html_preview(self):
        return HTMLPreview(self.html_content, '')

    @property
    def is_visible(self):
        return self.status == Entry.PUBLISHED

    @property
    def short_url(self):
        return reverse('zinnia:entry_shortlink', args=[base36(self.pk)])

    def get_absolute_url(self):
        publication_date = self.publication_date
        if timezone.is_aware(publication_date):
            publication_date = timezone.localtime(publication_date)
        return reverse('zinnia:entry_detail', kwargs={
            'year': publication_date.strftime('%Y'),
            'month': publication_date.strftime('%m'),
            'day': publication_date.strftime('%d'),
            'slug': self.slug
        })
