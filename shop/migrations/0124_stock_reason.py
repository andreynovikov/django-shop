# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2019-02-28 10:52
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0123_auto_20190227_1658'),
    ]

    operations = [
        migrations.AddField(
            model_name='stock',
            name='reason',
            field=models.CharField(blank=True, max_length=100, verbose_name='причина'),
        ),
    ]
