import datetime

from django.db import models
from django.utils.formats import date_format

from . import Order

__all__ = [
    'Act', 'ActOrder'
]


class Act(models.Model):
    orders = models.ManyToManyField(Order, verbose_name='заказы', through='ActOrder', related_name='acts', db_index=True)
    created = models.DateField('дата формирования', default=datetime.date.today)

    @property
    def number(self):
        return "№{:08d}".format(self.pk)

    def __str__(self):
        return "№{:08d} от {}".format(self.pk, date_format(self.created, "DATE_FORMAT"))

    class Meta:
        verbose_name = 'акт'
        verbose_name_plural = 'акты'


class ActOrder(models.Model):
    act = models.ForeignKey(Act, on_delete=models.CASCADE, verbose_name='акт')
    order = models.ForeignKey(Order, on_delete=models.PROTECT, verbose_name='заказ')

    class Meta:
        verbose_name = 'актированный заказ'
        verbose_name_plural = 'актированные заказы'
