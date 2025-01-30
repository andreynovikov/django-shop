from datetime import timedelta
from django.db import models
from django.utils import timezone

from . import ShopUser

__all__ = [
    'Bonus'
]


class Bonus(models.Model):
    STATUS_OK = 0x0
    STATUS_UNDEFINED = 0x00000001
    STATUS_PENDING = 0x00000002
    STATUS_CHOICES = (
        (STATUS_OK, ''),
        (STATUS_UNDEFINED, 'нет данных'),
        (STATUS_PENDING, 'обновляется'),
    )
    user = models.OneToOneField(ShopUser, verbose_name='покупатель', on_delete=models.CASCADE, primary_key=True)
    value = models.PositiveSmallIntegerField('баланс', default=0)
    status = models.PositiveIntegerField('статус', choices=STATUS_CHOICES, default=STATUS_UNDEFINED)
    updated = models.DateTimeField('дата обновления', default=timezone.now)

    def __str__(self):
        if self.is_undefined:
            return '-'
        else:
            return str(self.value)

    @property
    def is_fresh(self):
        fresh = timezone.now() - timedelta(hours=1)
        return bool(self.status == self.STATUS_OK and self.updated > fresh)

    @property
    def is_undefined(self):
        return bool(self.status & self.STATUS_UNDEFINED)

    @property
    def is_updating(self):
        return bool(self.status & self.STATUS_PENDING)

    class Meta:
        verbose_name = 'бонус'
        verbose_name_plural = 'бонусы'
