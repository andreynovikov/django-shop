# Generated by Django 3.2.12 on 2022-09-02 08:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0190_alter_order_delivery'),
    ]

    operations = [
        migrations.AddField(
            model_name='supplier',
            name='express_count_in_stock',
            field=models.SmallIntegerField(choices=[(99, 'не учитывать'), (1, 'наличие'), (2, 'под заказ')], default=99, verbose_name='учитывать в наличии Эксп'),
        ),
        migrations.AlterField(
            model_name='order',
            name='delivery',
            field=models.SmallIntegerField(choices=[(99, 'уточняется'), (1, 'курьер'), (2, 'консультант'), (3, 'получу сам в магазине'), (4, 'транспортная компания'), (8, 'почта России'), (9, 'OZON'), (5, 'PickPoint'), (10, 'Интеграл'), (11, 'Boxberry'), (6, 'Яндекс.Доставка'), (7, 'транзит')], db_index=True, default=99, verbose_name='доставка'),
        ),
    ]
