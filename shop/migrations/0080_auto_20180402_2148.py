# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2018-04-02 18:48
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0079_salesaction_order'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='productrelation',
            options={'verbose_name': 'связанный товар', 'verbose_name_plural': 'связанные товары'},
        ),
        migrations.AddField(
            model_name='product',
            name='max_val_discount',
            field=models.DecimalField(decimal_places=2, max_digits=10, null=True, verbose_name='макс. скидка, руб'),
        ),
        migrations.AlterField(
            model_name='product',
            name='related',
            field=models.ManyToManyField(blank=True, through='shop.ProductRelation', to='shop.Product'),
        ),
        migrations.AlterField(
            model_name='product',
            name='sales_actions',
            field=models.ManyToManyField(blank=True, related_name='products', related_query_name='product', to='shop.SalesAction', verbose_name='акции'),
        ),
        migrations.AlterField(
            model_name='productrelation',
            name='child_product',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='child_products', to='shop.Product', verbose_name='связанный товар'),
        ),
        migrations.AlterField(
            model_name='productrelation',
            name='parent_product',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='parent_products', to='shop.Product', verbose_name='товар'),
        ),
        migrations.AlterField(
            model_name='store',
            name='address2',
            field=models.CharField(blank=True, max_length=255, verbose_name='доп.адрес'),
        ),
        migrations.AlterField(
            model_name='store',
            name='phone2',
            field=models.CharField(blank=True, max_length=100, verbose_name='доп.телефон'),
        ),
    ]
