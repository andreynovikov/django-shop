# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0026_auto_20160910_0055'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='delivery_tracking_number',
            field=models.CharField(verbose_name='трек-код', blank=True, max_length=30),
        ),
        migrations.AlterField(
            model_name='order',
            name='delivery',
            field=models.SmallIntegerField(verbose_name='доставка', default=99, choices=[(99, 'уточняется'), (1, 'курьер'), (2, 'консультант'), (3, 'получу сам в магазине'), (4, 'транспортная компания'), (5, 'PickPoint'), (6, 'Яндекс.Доставка')]),
        ),
        migrations.AlterField(
            model_name='product',
            name='cur_code',
            field=models.ForeignKey(to='shop.Currency', on_delete=django.db.models.deletion.PROTECT, verbose_name='валюта', default=810),
        ),
    ]
