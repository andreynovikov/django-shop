# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0018_auto_20160801_2313'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='delivery_pickpoint_reception',
            field=models.CharField(default='CUR', choices=[('CUR', 'вызов курьера'), ('WIN', 'самопривоз')], verbose_name='вид приема', max_length=10),
        ),
        migrations.AlterField(
            model_name='order',
            name='delivery_pickpoint_service',
            field=models.CharField(default='STD', choices=[('STD', 'предоплаченный товар'), ('STDCOD', 'наложенный платеж')], verbose_name='тип сдачи', max_length=10),
        ),
        migrations.AlterField(
            model_name='order',
            name='delivery_pickpoint_terminal',
            field=models.CharField(blank=True, verbose_name='ПикПоинт терминал', max_length=10),
        ),
    ]
