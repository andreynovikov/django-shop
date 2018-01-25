# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import mptt.fields


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0020_auto_20160801_2334'),
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('name', models.CharField(max_length=100)),
                ('active', models.BooleanField()),
                ('order', models.IntegerField()),
                ('lft', models.PositiveIntegerField(db_index=True, editable=False)),
                ('rght', models.PositiveIntegerField(db_index=True, editable=False)),
                ('tree_id', models.PositiveIntegerField(db_index=True, editable=False)),
                ('level', models.PositiveIntegerField(db_index=True, editable=False)),
                ('parent', mptt.fields.TreeForeignKey(null=True, blank=True, related_name='children', to='shop.Category')),
            ],
            options={
                'verbose_name': 'категория',
                'verbose_name_plural': 'категории',
            },
        ),
        migrations.AlterField(
            model_name='order',
            name='delivery',
            field=models.SmallIntegerField(choices=[(99, 'уточняется'), (1, 'курьер'), (2, 'консультант'), (3, 'получу сам в магазине'), (4, 'транспортная компания'), (5, 'PickPoint')], verbose_name='доставка', default=99),
        ),
        migrations.AlterField(
            model_name='order',
            name='delivery_pickpoint_terminal',
            field=models.CharField(verbose_name='терминал', blank=True, max_length=10),
        ),
    ]
