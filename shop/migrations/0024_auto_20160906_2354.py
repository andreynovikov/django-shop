# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import mptt.fields


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0023_product_categories'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='forbid_price_import',
            field=models.BooleanField(default=False, verbose_name='не импортировать цену'),
        ),
        migrations.AddField(
            model_name='product',
            name='number_inet',
            field=models.DecimalField(default=0, max_digits=10, verbose_name='наличие в интернет-магазине', decimal_places=2),
        ),
        migrations.AddField(
            model_name='product',
            name='number_prol',
            field=models.DecimalField(default=0, max_digits=10, verbose_name='наличие на пролетарке', decimal_places=2),
        ),
        migrations.AlterField(
            model_name='product',
            name='categories',
            field=mptt.fields.TreeManyToManyField(to='shop.Category', blank=True, verbose_name='категории'),
        ),
    ]
