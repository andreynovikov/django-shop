from django.db import models

from . import City

__all__ = ['ServiceCenter']


class ServiceCenter(models.Model):
    city = models.ForeignKey(City, verbose_name='город', on_delete=models.PROTECT)
    address = models.CharField('адрес', max_length=255)
    phone = models.CharField('телефон', max_length=100, blank=True)
    enabled = models.BooleanField('включён', default=True)
    latitude = models.FloatField('широта', default=0, blank=True, null=True)
    longitude = models.FloatField('долгота', default=0, blank=True, null=True)

    class Meta:
        verbose_name = 'сервис-центр'
        verbose_name_plural = 'сервис-центры'
        ordering = ('city', 'address')

    def phones_as_list(self):
        return [x.strip() for x in self.phone.split(',')]

    @staticmethod
    def autocomplete_search_fields():
        return ['address__icontains', 'city__name__icontains']

    def __str__(self):
        return str(self.city) + ', ' + self.address
