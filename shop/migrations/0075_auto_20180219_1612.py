# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2018-02-19 13:12
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0074_store'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='city',
            options={'verbose_name': 'город', 'verbose_name_plural': 'города'},
        ),
        migrations.AlterModelOptions(
            name='store',
            options={'verbose_name': 'магазин', 'verbose_name_plural': 'магазины'},
        ),
        migrations.AddField(
            model_name='order',
            name='store',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='shop.Store', verbose_name='магазин самовывоза'),
        ),
        migrations.AlterField(
            model_name='city',
            name='country',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='shop.Country', verbose_name='страна'),
        ),
        migrations.AlterField(
            model_name='city',
            name='region',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='shop.Region', verbose_name='регион'),
        ),
        migrations.AlterField(
            model_name='region',
            name='country',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='shop.Country', verbose_name='страна'),
        ),
        migrations.AlterField(
            model_name='store',
            name='city',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='shop.City', verbose_name='город'),
        ),
    ]
