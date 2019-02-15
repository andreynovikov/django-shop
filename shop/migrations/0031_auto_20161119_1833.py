# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0030_supplier_order'),
    ]

    operations = [
        migrations.CreateModel(
            name='Stock',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
                ('quantity', models.FloatField(verbose_name='кол-во', default=0)),
            ],
        ),
        migrations.RemoveField(
            model_name='product',
            name='supplier',
        ),
        migrations.AddField(
            model_name='stock',
            name='product',
            field=models.ForeignKey(to='shop.Product', related_name='item', on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='stock',
            name='supplier',
            field=models.ForeignKey(to='shop.Supplier', on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='product',
            name='stock',
            field=models.ManyToManyField(to='shop.Supplier', through='shop.Stock'),
        ),
    ]
