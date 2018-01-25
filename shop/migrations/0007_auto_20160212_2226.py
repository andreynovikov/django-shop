# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0006_auto_20160210_1922'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.SmallIntegerField(default=0, choices=[(0, 'новый заказ'), (1, 'принят в работу'), (4, 'комплектуется'), (8, 'отменен'), (16, 'заморожен'), (32, 'передан в другой магазин'), (64, 'собран'), (1024, 'доставляется'), (2048, 'доставлен'), (4096, 'консультация'), (16384, 'завершен')], verbose_name='статус'),
        ),
    ]
