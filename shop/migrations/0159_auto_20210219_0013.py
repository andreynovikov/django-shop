# Generated by Django 2.1.7 on 2021-02-18 21:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0158_auto_20210121_1950'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='avito',
            field=models.BooleanField(db_index=True, default=False, verbose_name='выгружать в Авито'),
        ),
        migrations.AddField(
            model_name='product',
            name='avito_price',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='цена Авито, руб'),
        ),
    ]
