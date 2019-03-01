# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import colorfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0045_auto_20170515_1427'),
    ]

    operations = [
        migrations.CreateModel(
            name='Courier',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, primary_key=True, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='имя')),
                ('color', colorfield.fields.ColorField(default='#000000', max_length=10)),
            ],
            options={
                'verbose_name_plural': 'курьеры',
                'verbose_name': 'курьер',
            },
        ),
        migrations.AddField(
            model_name='order',
            name='courier',
            field=models.ForeignKey(to='shop.Courier', blank=True, null=True, verbose_name='курьер', on_delete=models.SET_NULL),
        ),
    ]
