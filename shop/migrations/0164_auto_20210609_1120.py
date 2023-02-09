# Generated by Django 2.1.7 on 2021-06-09 08:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0163_product_mdbs'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='sber',
            field=models.BooleanField(db_index=True, default=False, verbose_name='выгружать в СберМаркет'),
        ),
        migrations.AddField(
            model_name='product',
            name='sber_price',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='цена СберМаркет, руб'),
        ),
    ]