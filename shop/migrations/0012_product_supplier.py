# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0011_auto_20160607_1347'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='supplier',
            field=models.ForeignKey(default=1, verbose_name='Поставщик', to='shop.Supplier', on_delete=django.db.models.deletion.PROTECT),
            preserve_default=False,
        ),
    ]
