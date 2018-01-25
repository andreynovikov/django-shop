# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0028_order_delivery_yd_order'),
    ]

    operations = [
        migrations.AddField(
            model_name='supplier',
            name='code',
            field=models.CharField(max_length=10, verbose_name='код', default=''),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='category',
            name='order',
            field=models.PositiveIntegerField(),
        ),
    ]
