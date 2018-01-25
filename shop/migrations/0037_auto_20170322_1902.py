# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0036_auto_20170119_1809'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.PositiveIntegerField(choices=[(0, 'новый заказ'), (1, 'принят в работу'), (4, 'комплектуется'), (8, 'отменен'), (16, 'заморожен'), (32, 'передан в другой магазин'), (64, 'собран'), (128, 'сервис'), (1024, 'доставляется'), (2048, 'доставлен'), (256, 'доставлен в магазин'), (512, 'передан в службу доставки'), (4096, 'консультация'), (8192, 'проблема'), (16384, 'завершён'), (251658240, 'выполнен')], default=0, verbose_name='статус', db_index=True),
        ),
        migrations.AlterField(
            model_name='product',
            name='code',
            field=models.CharField(verbose_name='идентификатор', db_index=True, max_length=20),
        ),
        migrations.AlterField(
            model_name='product',
            name='num',
            field=models.SmallIntegerField(default=-1, verbose_name='В наличии'),
        ),
    ]
