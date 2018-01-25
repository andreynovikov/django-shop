# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0025_currency'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='cur_code',
            field=models.ForeignKey(default=810, to='shop.Currency', on_delete=django.db.models.deletion.PROTECT),
        ),
    ]
