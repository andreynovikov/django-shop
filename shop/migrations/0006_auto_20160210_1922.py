# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0005_auto_20151115_2319'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='postcode',
            field=models.CharField(verbose_name='индекс', max_length=10, blank=True),
        ),
        migrations.AddField(
            model_name='shopuser',
            name='postcode',
            field=models.CharField(verbose_name='индекс', max_length=10, blank=True),
        ),
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.SmallIntegerField(verbose_name='статус', choices=[(0, 'новый заказ'), (1, 'принят в работу'), (2, 'консультация'), (4, 'комплектуется'), (8, 'отменен'), (16, 'заморожен'), (32, 'передан в другой магазин'), (64, 'собран'), (1024, 'доставляется'), (2048, 'доставлен'), (16384, 'завершен')], default=0),
        ),
    ]
