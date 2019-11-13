# Generated by Django 2.1.7 on 2019-10-17 14:03

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0142_auto_20191017_1641'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='box',
            options={'verbose_name': 'коробка', 'verbose_name_plural': 'коробки'},
        ),
        migrations.AlterField(
            model_name='box',
            name='product',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='shop.Product', verbose_name='товар'),
        ),
    ]