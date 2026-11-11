from django.db import models

__all__ = ['Currency']


class Currency(models.Model):
    code = models.PositiveSmallIntegerField('код', primary_key=True)
    name = models.CharField('название', max_length=20)
    rate = models.DecimalField('курс', max_digits=5, decimal_places=2, default=1)

    class Meta:
        verbose_name = 'валюта'
        verbose_name_plural = 'валюты'

    def __str__(self):
        return self.name
