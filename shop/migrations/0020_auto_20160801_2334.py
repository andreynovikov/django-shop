# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0019_auto_20160801_2317'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='delivery_size_height',
            field=models.SmallIntegerField(default=0, verbose_name='высота'),
        ),
        migrations.AddField(
            model_name='order',
            name='delivery_size_length',
            field=models.SmallIntegerField(default=0, verbose_name='длина'),
        ),
        migrations.AddField(
            model_name='order',
            name='delivery_size_width',
            field=models.SmallIntegerField(default=0, verbose_name='ширина'),
        ),
    ]
