# Generated by Django 3.2.12 on 2024-03-18 13:54

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0224_auto_20240318_1648'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='gtin',
            field=models.CharField(blank=True, db_index=True, max_length=17, verbose_name='штрих-код'),
        ),
        migrations.AlterField(
            model_name='product',
            name='gtins',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(blank=True, max_length=255), db_index=True, size=None, verbose_name='дополнительные штих-коды'),
        ),
    ]
