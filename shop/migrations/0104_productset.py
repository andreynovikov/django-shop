# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2018-09-12 14:31
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0103_product_tags'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProductSet',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('recalculate_price', models.BooleanField(default=True, verbose_name='пересчитывать цену')),
                ('discount', models.PositiveSmallIntegerField(default=0, verbose_name='скидка, %')),
                ('constituent', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='constituents', to='shop.Product', verbose_name='составляющая')),
                ('declaration', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='declarations', to='shop.Product', verbose_name='определение')),
            ],
            options={
                'verbose_name_plural': 'комплекты',
                'verbose_name': 'комплект',
            },
        ),
    ]