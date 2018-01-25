# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0003_auto_20151023_1223'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='orderitem',
            options={'verbose_name': 'товар', 'verbose_name_plural': 'товары'},
        ),
        migrations.AddField(
            model_name='order',
            name='delivery_date',
            field=models.DateField(verbose_name='дата доставки', blank=True, null=True),
        ),
        migrations.AddField(
            model_name='order',
            name='delivery_time_from',
            field=models.TimeField(verbose_name='время доставки от', blank=True, null=True),
        ),
        migrations.AddField(
            model_name='order',
            name='delivery_time_till',
            field=models.TimeField(verbose_name='время доставки до', blank=True, null=True),
        ),
        migrations.AddField(
            model_name='order',
            name='manager_comment',
            field=models.TextField(verbose_name='комментарий менеджера', blank=True),
        ),
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.SmallIntegerField(verbose_name='статус', default=0, choices=[(0, 'новый заказ'), (1, 'принят в работу'), (4, 'комплектуется'), (8, 'отменен'), (16, 'заморожен'), (32, 'передан в другой магазин'), (64, 'собран'), (1024, 'доставляется'), (2048, 'доставлен'), (16384, 'завершен')]),
        ),
        migrations.AlterField(
            model_name='orderitem',
            name='val_discount',
            field=models.PositiveIntegerField(verbose_name='скидка, руб', default=0),
        ),
    ]
