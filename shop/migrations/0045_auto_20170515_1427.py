# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0044_auto_20170511_2027'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='order',
            name='courier',
        ),
        migrations.AlterField(
            model_name='order',
            name='seller',
            field=models.ForeignKey(to='shop.Contractor', null=True, related_name='продавец', verbose_name='продавец 1С', blank=True, on_delete=models.SET_NULL),
        ),
        migrations.DeleteModel(
            name='Courier',
        ),
    ]
