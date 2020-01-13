# Generated by Django 2.1.7 on 2020-01-13 13:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0150_auto_20191122_1319'),
    ]

    operations = [
        migrations.AddField(
            model_name='supplier',
            name='beru_count_in_stock',
            field=models.SmallIntegerField(choices=[(99, 'не учитывать'), (1, 'наличие'), (2, 'под заказ')], default=99, verbose_name='учитывать в наличии Беру'),
        ),
    ]
