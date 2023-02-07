# Generated by Django 3.2.12 on 2023-02-06 16:58

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0199_alter_stock_product'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='wirehouse',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='orders', to='shop.supplier', verbose_name='склад отгрузки'),
        ),
    ]
