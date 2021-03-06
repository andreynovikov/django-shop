# Generated by Django 2.1.7 on 2019-06-18 19:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0134_product_forbid_ws_price_import'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='product',
            name='dimensions',
        ),
        migrations.AddField(
            model_name='product',
            name='height',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=5, verbose_name='высота'),
        ),
        migrations.AddField(
            model_name='product',
            name='length',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=5, verbose_name='длина'),
        ),
        migrations.AddField(
            model_name='product',
            name='width',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=5, verbose_name='ширина'),
        ),
    ]
