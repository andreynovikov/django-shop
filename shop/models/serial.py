from django.db import models

from . import Product, Order, ShopUser

__all__ = [
    'Serial'
]


class Serial(models.Model):
    number = models.CharField('SN', max_length=30, unique=True)
    user = models.ForeignKey(ShopUser, verbose_name='пользователь', related_name='serials', on_delete=models.PROTECT)
    purchase_date = models.DateField('дата покупки', blank=True, null=True)
    product = models.ForeignKey(Product, related_name='+', verbose_name='товар', blank=True, null=True, on_delete=models.PROTECT)
    order = models.ForeignKey(Order, related_name='+', verbose_name='заказ', blank=True, null=True, on_delete=models.PROTECT)
    approved = models.BooleanField('проверен', default=False)
    comment = models.TextField('комментарий менеджера', blank=True)

    class Meta:
        verbose_name = 'гарантийный талон'
        verbose_name_plural = 'гарантийные талоны'
        ordering = ['-purchase_date', 'number']

    def __str__(self):
        return self.number
