# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2018-08-01 18:41
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0095_auto_20180801_2118'),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='filters',
            field=models.CharField(blank=True, max_length=255, verbose_name='фильтры'),
        ),
    ]
