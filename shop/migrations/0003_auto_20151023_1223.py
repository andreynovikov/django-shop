# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0002_auto_20151022_1047'),
    ]

    operations = [
        migrations.RenameField(
            model_name='orderitem',
            old_name='discount',
            new_name='val_discount',
        ),
        migrations.AddField(
            model_name='orderitem',
            name='pct_discount',
            field=models.PositiveSmallIntegerField(verbose_name='скидка, %', default=0),
        ),
        #migrations.AddField(
        #    model_name='orderitem',
        #    name='val_discount',
        #    field=models.PositiveIntegerField(verbose_name='скидка, руб', default=0),
        #),
        migrations.AlterField(
            model_name='product',
            name='cur_code',
            field=models.SmallIntegerField(verbose_name='валюта', choices=[(810, 'рубль'), (978, 'евро'), (840, 'доллар')], default=810),
        ),
    ]
