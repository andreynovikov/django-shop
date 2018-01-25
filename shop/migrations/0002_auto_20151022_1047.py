# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='cur_code',
            field=models.PositiveSmallIntegerField(default=810, verbose_name='валюта'),
        ),
        migrations.AddField(
            model_name='product',
            name='cur_price',
            field=models.PositiveIntegerField(default=0, verbose_name='цена, вал'),
        ),
    ]
