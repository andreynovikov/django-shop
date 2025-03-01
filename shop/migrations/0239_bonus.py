# Generated by Django 3.2.12 on 2025-01-30 08:56

import datetime
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0238_auto_20250130_1155'),
    ]

    operations = [
        migrations.CreateModel(
            name='Bonus',
            fields=[
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to='shop.shopuser', verbose_name='покупатель')),
                ('value', models.PositiveSmallIntegerField(default=0, verbose_name='баланс')),
                ('status', models.PositiveIntegerField(choices=[(0, ''), (1, 'нет данных'), (2, 'обновляется')], default=1, verbose_name='статус')),
                ('updated', models.DateTimeField(default=datetime.datetime.now, verbose_name='дата обновления')),
            ],
            options={
                'verbose_name': 'бонус',
                'verbose_name_plural': 'бонусы',
            },
        ),
    ]
