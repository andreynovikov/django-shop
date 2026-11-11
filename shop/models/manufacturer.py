from django.db import models

__all__ = ['Manufacturer']


class Manufacturer(models.Model):
    code = models.CharField('код', max_length=30)
    name = models.CharField('название', max_length=150)
    machinemaker = models.BooleanField('машины делает', default=False)
    accessorymaker = models.BooleanField('аксессуары делает', default=False)
    logo = models.FileField('логотип', upload_to='logos', blank=True)
    logo_width = models.IntegerField(null=True, blank=True)
    logo_height = models.IntegerField(null=True, blank=True)

    class Meta:
        verbose_name = 'производитель'
        verbose_name_plural = 'производители'
        ordering = ['name']

    @staticmethod
    def autocomplete_search_fields():
        return ['name__icontains']

    def __str__(self):
        return self.name
