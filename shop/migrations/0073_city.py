# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2018-02-19 12:16
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0072_region'),
    ]

    operations = [
        migrations.CreateModel(
            name='City',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='название')),
                ('ename', models.CharField(blank=True, max_length=100, verbose_name='англ. название')),
                ('latitude', models.FloatField(blank=True, default=0, null=True, verbose_name='широта')),
                ('longitude', models.FloatField(blank=True, default=0, null=True, verbose_name='долгота')),
                ('code', models.CharField(blank=True, max_length=20, verbose_name='код')),
                ('country', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='shop.Country')),
                ('region', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='shop.Region')),
            ],
        ),
    ]
