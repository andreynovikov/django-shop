# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0041_order_wiring_date'),
    ]

    operations = [
        migrations.CreateModel(
            name='Courier',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='имя')),
            ],
            options={
                'verbose_name_plural': 'курьеры',
                'verbose_name': 'курьер',
            },
        ),
        migrations.CreateModel(
            name='Manager',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='имя')),
            ],
            options={
                'verbose_name_plural': 'менеджеры',
                'verbose_name': 'менеджер',
            },
        ),
        migrations.AddField(
            model_name='order',
            name='courier',
            field=models.ForeignKey(null=True, to='shop.Courier', blank=True, on_delete=models.SET_NULL),
        ),
        migrations.AddField(
            model_name='order',
            name='manafer',
            field=models.ForeignKey(null=True, to='shop.Manager', blank=True, on_delete=models.SET_NULL),
        ),
    ]
