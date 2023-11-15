# Generated by Django 2.1.7 on 2019-10-28 13:50

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0144_auto_20191018_1518'),
    ]

    operations = [
        migrations.CreateModel(
            name='Act',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateField(default=django.utils.timezone.now, verbose_name='дата формирования')),
            ],
            options={
                'verbose_name': 'акт',
                'verbose_name_plural': 'акты',
            },
        ),
        migrations.CreateModel(
            name='ActOrder',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('act', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='shop.Act', verbose_name='акт')),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='shop.Order', verbose_name='заказ')),
            ],
            options={
                'verbose_name': 'актированный заказ',
                'verbose_name_plural': 'актированные заказы',
            },
        ),
        migrations.AddField(
            model_name='act',
            name='orders',
            field=models.ManyToManyField(db_index=True, through='shop.ActOrder', to='shop.Order', verbose_name='заказы'),
        ),
    ]