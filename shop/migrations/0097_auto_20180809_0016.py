# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2018-08-08 21:16
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0096_category_filters'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='gtin',
            field=models.CharField(blank=True, db_index=True, max_length=17, verbose_name='GTIN'),
        ),
    ]
