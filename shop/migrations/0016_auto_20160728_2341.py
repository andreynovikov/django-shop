# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0015_auto_20160727_1827'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.PositiveIntegerField(default=0, verbose_name='статус', choices=[(0, 'новый заказ'), (1, 'принят в работу'), (4, 'комплектуется'), (8, 'отменен'), (16, 'заморожен'), (32, 'передан в другой магазин'), (64, 'собран'), (1024, 'доставляется'), (2048, 'доставлен'), (256, 'доставлен в магазин'), (512, 'доставлен в ТК'), (4096, 'консультация'), (8192, 'проблема'), (16384, 'завершён'), (251658240, 'выполнен')]),
        ),
    ]
