# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0013_product_country'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='developer_country',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='shop.Country', default=1, related_name='developed_product', verbose_name='Страна-разработчик'),
            preserve_default=False,
        ),
    ]
