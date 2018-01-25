# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0010_manufacturer'),
    ]

    operations = [
        migrations.CreateModel(
            name='Supplier',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, verbose_name='ID', serialize=False)),
                ('name', models.CharField(verbose_name='название', max_length=100)),
            ],
            options={
                'verbose_name_plural': 'поставщики',
                'verbose_name': 'поставщик',
            },
        ),
        migrations.AddField(
            model_name='product',
            name='manufacturer',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='shop.Manufacturer', verbose_name='Производитель', default=1),
            preserve_default=False,
        ),
    ]
