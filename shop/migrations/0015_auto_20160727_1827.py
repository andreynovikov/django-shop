# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0014_product_developer_country'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='delivery',
            field=models.SmallIntegerField(choices=[(99, 'уточняется'), (1, 'курьер'), (2, 'консультант'), (3, 'получу сам в магазине'), (4, 'транспортная компания')], verbose_name='доставка', default=99),
        ),
        migrations.AlterField(
            model_name='order',
            name='payment',
            field=models.SmallIntegerField(choices=[(99, 'уточняется'), (1, 'наличные'), (2, 'банковская карта'), (3, 'банковский перевод'), (4, 'наложенный платёж')], verbose_name='оплата', default=99),
        ),
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.SmallIntegerField(choices=[(0, 'новый заказ'), (1, 'принят в работу'), (4, 'комплектуется'), (8, 'отменен'), (16, 'заморожен'), (32, 'передан в другой магазин'), (64, 'собран'), (1024, 'доставляется'), (2048, 'доставлен'), (256, 'доставлен в магазин'), (512, 'доставлен в ТК'), (4096, 'консультация'), (8192, 'проблема'), (16384, 'завершен')], verbose_name='статус', default=0),
        ),
        migrations.AlterField(
            model_name='product',
            name='article',
            field=models.CharField(blank=True, verbose_name='код 1С', max_length=20),
        ),
        migrations.AlterField(
            model_name='product',
            name='code',
            field=models.CharField(verbose_name='идентификатор', max_length=20),
        ),
        migrations.AlterField(
            model_name='product',
            name='country',
            field=models.ForeignKey(verbose_name='Страна-производитель', default=1, to='shop.Country', on_delete=django.db.models.deletion.PROTECT),
        ),
        migrations.AlterField(
            model_name='product',
            name='developer_country',
            field=models.ForeignKey(related_name='developed_product', verbose_name='Страна-разработчик', default=1, to='shop.Country', on_delete=django.db.models.deletion.PROTECT),
        ),
        migrations.AlterField(
            model_name='product',
            name='manufacturer',
            field=models.ForeignKey(verbose_name='Производитель', default=49, to='shop.Manufacturer', on_delete=django.db.models.deletion.PROTECT),
        ),
        migrations.AlterField(
            model_name='product',
            name='max_discount',
            field=models.PositiveSmallIntegerField(verbose_name='макс. скидка, %', default=10),
        ),
        migrations.AlterField(
            model_name='product',
            name='supplier',
            field=models.ForeignKey(verbose_name='Поставщик', default=4, to='shop.Supplier', on_delete=django.db.models.deletion.PROTECT),
        ),
    ]
