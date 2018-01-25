# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0035_auto_20161203_2010'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='num_correction',
            field=models.SmallIntegerField(verbose_name='Корректировка наличия', default=0),
        ),
        migrations.AlterField(
            model_name='order',
            name='delivery',
            field=models.SmallIntegerField(db_index=True, choices=[(99, 'уточняется'), (1, 'курьер'), (2, 'консультант'), (3, 'получу сам в магазине'), (4, 'транспортная компания'), (5, 'PickPoint'), (6, 'Яндекс.Доставка')], verbose_name='доставка', default=99),
        ),
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.PositiveIntegerField(db_index=True, choices=[(0, 'новый заказ'), (1, 'принят в работу'), (4, 'комплектуется'), (8, 'отменен'), (16, 'заморожен'), (32, 'передан в другой магазин'), (64, 'собран'), (1024, 'доставляется'), (2048, 'доставлен'), (256, 'доставлен в магазин'), (512, 'передан в службу доставки'), (4096, 'консультация'), (8192, 'проблема'), (16384, 'завершён'), (251658240, 'выполнен')], verbose_name='статус', default=0),
        ),
    ]
