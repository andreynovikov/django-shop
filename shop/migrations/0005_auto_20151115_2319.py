# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0004_auto_20151106_0054'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='extended_warranty',
            field=models.CharField(blank=True, verbose_name='расширенная гарантия', max_length=20),
        ),
        migrations.AddField(
            model_name='product',
            name='manufacturer_warranty',
            field=models.BooleanField(default=False, verbose_name='официальная гарантия'),
        ),
        migrations.AddField(
            model_name='product',
            name='warranty',
            field=models.CharField(blank=True, verbose_name='гарантия', max_length=20),
        ),
        migrations.AlterField(
            model_name='order',
            name='delivery_time_from',
            field=models.TimeField(blank=True, null=True, verbose_name='от'),
        ),
        migrations.AlterField(
            model_name='order',
            name='delivery_time_till',
            field=models.TimeField(blank=True, null=True, verbose_name='до'),
        ),
    ]
