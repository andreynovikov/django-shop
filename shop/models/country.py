from django.db import models

__all__ = ['Country', 'Region', 'City']


class Country(models.Model):
    name = models.CharField('название', max_length=100)
    ename = models.CharField('англ. название', max_length=100)
    enabled = models.BooleanField('включена', default=True)

    class Meta:
        verbose_name = 'страна'
        verbose_name_plural = 'страны'

    @staticmethod
    def autocomplete_search_fields():
        return ['name__icontains']

    def __str__(self):
        return self.name


class Region(models.Model):
    name = models.CharField('название', max_length=100)
    country = models.ForeignKey(Country, verbose_name='страна', on_delete=models.PROTECT)

    class Meta:
        verbose_name = 'регион'
        verbose_name_plural = 'регионы'

    @staticmethod
    def autocomplete_search_fields():
        return ['name__icontains']

    def __str__(self):
        return str(self.country) + ', ' + self.name


class City(models.Model):
    country = models.ForeignKey(Country, verbose_name='страна', on_delete=models.PROTECT)
    region = models.ForeignKey(Region, verbose_name='регион', blank=True, null=True, on_delete=models.PROTECT)
    name = models.CharField('название', max_length=100)
    ename = models.CharField('англ. название', max_length=100, blank=True)
    latitude = models.FloatField('широта', default=0, blank=True, null=True)
    longitude = models.FloatField('долгота', default=0, blank=True, null=True)
    code = models.CharField('код', max_length=20, blank=True)

    class Meta:
        verbose_name = 'город'
        verbose_name_plural = 'города'
        ordering = ('country', 'name')

    @staticmethod
    def autocomplete_search_fields():
        return ['name__icontains']

    def __str__(self):
        return str(self.country) + ', ' + self.name
