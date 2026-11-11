from django.db import models

__all__ = ['Supplier']


class Supplier(models.Model):
    COUNT_STOCK = 1
    COUNT_DEFER = 2
    COUNT_NONE = 99
    COUNT_CHOICES = (
        (COUNT_NONE, 'не учитывать'),
        (COUNT_STOCK, 'наличие'),
        (COUNT_DEFER, 'под заказ'),
    )
    code = models.CharField('код', max_length=10)
    code1c = models.CharField('код 1С', max_length=50)
    name = models.CharField('название', max_length=100)
    show_in_order = models.BooleanField('показывать в заказе', default=False, db_index=True)
    show_in_list = models.BooleanField('показывать в списках', default=False, db_index=True)
    count_in_stock = models.SmallIntegerField('учитывать в наличии', choices=COUNT_CHOICES, default=COUNT_NONE)
    express_count_in_stock = models.SmallIntegerField('учитывать в наличии Экспресс', choices=COUNT_CHOICES, default=COUNT_NONE)
    order = models.PositiveIntegerField()

    class Meta:
        verbose_name = 'поставщик'
        verbose_name_plural = 'поставщики'
        ordering = ['order']

    @staticmethod
    def autocomplete_search_fields():
        return ['code__startswith', 'name__icontains']

    def __str__(self):
        return self.name
