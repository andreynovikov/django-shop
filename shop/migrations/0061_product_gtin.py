# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-12-21 18:55
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0060_auto_20170814_2304'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='gtin',
            field=models.BigIntegerField(blank=True, db_index=True, default=0, max_length=20, verbose_name='GTIN'),
            preserve_default=False,
        ),
    ]