# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0031_auto_20161119_1833'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='stock',
            options={'verbose_name_plural': 'запасы', 'verbose_name': 'запас'},
        ),
        migrations.AlterField(
            model_name='product',
            name='article',
            field=models.CharField(verbose_name='код 1С', blank=True, db_index=True, max_length=20),
        ),
        migrations.AlterField(
            model_name='product',
            name='partnumber',
            field=models.CharField(verbose_name='partnumber', blank=True, db_index=True, max_length=200),
        ),
    ]
