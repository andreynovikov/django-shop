# Generated by Django 2.1.7 on 2019-10-28 13:51

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0145_auto_20191028_1650'),
    ]

    operations = [
        migrations.AlterField(
            model_name='orderitem',
            name='box',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='products', related_query_name='box', to='shop.Box', verbose_name='коробка'),
        ),
    ]
