# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-12-21 18:55
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0061_product_gtin'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='enabled',
            field=models.BooleanField(db_index=True, default=False, verbose_name='включён'),
        ),
    ]
