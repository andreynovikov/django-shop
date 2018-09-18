# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2018-06-07 05:20
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0092_auto_20180522_2027'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='spb_market',
            field=models.BooleanField(db_index=True, default=False, verbose_name='маркет СПб'),
        ),
        migrations.AddField(
            model_name='product',
            name='spb_show_in_catalog',
            field=models.BooleanField(db_index=True, default=True, verbose_name='витрина СПб'),
        ),
        migrations.AlterField(
            model_name='product',
            name='market',
            field=models.BooleanField(db_column='market', db_index=True, default=False, verbose_name='маркет'),
        ),
        migrations.AlterField(
            model_name='product',
            name='show_on_sw',
            field=models.BooleanField(db_column='show_on_sw', db_index=True, default=True, verbose_name='витрина'),
        ),
    ]
