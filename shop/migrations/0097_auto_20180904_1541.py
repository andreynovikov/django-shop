# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2018-09-04 12:41
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0096_category_filters'),
    ]

    operations = [
        migrations.AddField(
            model_name='basket',
            name='utm_source',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name='order',
            name='utm_source',
            field=models.CharField(blank=True, max_length=20),
        ),
    ]
