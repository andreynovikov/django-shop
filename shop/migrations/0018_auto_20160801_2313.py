# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0017_product_market'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='delivery_pickpoint_reception',
            field=models.CharField(choices=[('CUR', 'вызов курьера'), ('WIN', 'самопривоз')], verbose_name='вид приема', default='CUR', max_length=5),
        ),
        migrations.AddField(
            model_name='order',
            name='delivery_pickpoint_service',
            field=models.CharField(choices=[('STD', 'предоплаченный товар'), ('STDCOD', 'наложенный платеж')], verbose_name='тип сдачи', default='STD', max_length=5),
        ),
        migrations.AddField(
            model_name='order',
            name='delivery_pickpoint_terminal',
            field=models.CharField(verbose_name='терминал', max_length=10, blank=True),
        ),
        migrations.AlterField(
            model_name='order',
            name='payment',
            field=models.SmallIntegerField(choices=[(99, 'уточняется'), (1, 'наличные'), (2, 'банковская карта'), (3, 'банковский перевод'), (4, 'наложенный платёж'), (5, 'платёжный терминал')], verbose_name='оплата', default=99),
        ),
        migrations.AlterField(
            model_name='product',
            name='market',
            field=models.BooleanField(verbose_name='Выгружать в маркет', default=False),
        ),
    ]
