# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0012_product_supplier'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='country',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='shop.Country', default=1, verbose_name='Страна-производитель'),
            preserve_default=False,
        ),
    ]
