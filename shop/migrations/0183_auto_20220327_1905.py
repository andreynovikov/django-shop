# Generated by Django 2.2.27 on 2022-03-27 16:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0182_auto_20220327_1737'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='supplier',
            name='beru_count_in_stock',
        ),
        migrations.RemoveField(
            model_name='supplier',
            name='tax2_count_in_stock',
        ),
        migrations.RemoveField(
            model_name='supplier',
            name='tax3_count_in_stock',
        ),
        migrations.RemoveField(
            model_name='supplier',
            name='taxi_count_in_stock',
        ),
        migrations.AlterField(
            model_name='integration',
            name='suppliers',
            field=models.ManyToManyField(blank=True, related_name='integrations', related_query_name='integration', to='shop.Supplier', verbose_name='поставщики'),
        ),
    ]
