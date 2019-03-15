# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('sessions', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ShopUser',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('password', models.CharField(verbose_name='password', max_length=128)),
                ('last_login', models.DateTimeField(verbose_name='last login', null=True, blank=True)),
                ('phone', models.CharField(unique=True, max_length=30)),
                ('name', models.CharField(blank=True, max_length=100)),
                ('email', models.EmailField(blank=True, max_length=254)),
                ('city', models.CharField(blank=True, max_length=255)),
                ('address', models.CharField(blank=True, max_length=255)),
                ('discount', models.PositiveSmallIntegerField(default=0)),
                ('is_active', models.BooleanField(default=True)),
                ('is_admin', models.BooleanField(default=False)),
            ],
            options={
                'verbose_name': 'пользователь',
                'verbose_name_plural': 'пользователи',
            },
        ),
        migrations.CreateModel(
            name='Basket',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('phone', models.CharField(blank=True, max_length=30)),
                ('session', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='sessions.Session')),
            ],
        ),
        migrations.CreateModel(
            name='BasketItem',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('quantity', models.PositiveSmallIntegerField(default=1)),
                ('basket', models.ForeignKey(to='shop.Basket', related_query_name='item', related_name='items', on_delete=models.CASCADE)),
            ],
        ),
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('shop_name', models.CharField(verbose_name='магазин', blank=True, max_length=20)),
                ('payment', models.SmallIntegerField(verbose_name='оплата', default=1, choices=[(1, 'наличные'), (2, 'банковская карта'), (3, 'банковский перевод')])),
                ('paid', models.BooleanField(verbose_name='оплачен', default=False)),
                ('delivery', models.SmallIntegerField(verbose_name='доставка', default=1, choices=[(1, 'курьер'), (2, 'консультант'), (3, 'получу сам в магазине'), (4, 'транспортная компания')])),
                ('delivery_price', models.PositiveIntegerField(verbose_name='стоимость доставки', default=0)),
                ('delivery_info', models.TextField(verbose_name='ТК, ТТН, курьер', blank=True)),
                ('comment', models.TextField(verbose_name='комментарий', blank=True)),
                ('name', models.CharField(verbose_name='имя', blank=True, max_length=100)),
                ('city', models.CharField(verbose_name='город', blank=True, max_length=255)),
                ('address', models.CharField(verbose_name='адрес', blank=True, max_length=255)),
                ('phone', models.CharField(verbose_name='телефон', blank=True, max_length=30)),
                ('phone_aux', models.CharField(verbose_name='доп.телефон', blank=True, max_length=30)),
                ('email', models.EmailField(verbose_name='эл.почта', blank=True, max_length=254)),
                ('is_firm', models.BooleanField(verbose_name='юр.лицо', default=False)),
                ('firm_name', models.CharField(verbose_name='название организации', blank=True, max_length=255)),
                ('firm_address', models.CharField(verbose_name='Юр.адрес', blank=True, max_length=255)),
                ('firm_details', models.TextField(verbose_name='реквизиты', blank=True)),
                ('created', models.DateTimeField(verbose_name='создан', auto_now_add=True)),
                ('status', models.SmallIntegerField(verbose_name='статус', default=0, choices=[(0, 'новый заказ'), (1, 'принят в работу'), (8, 'отменен'), (16, 'заморожен'), (32, 'передан в другой магазин'), (64, 'собран'), (1024, 'доставляется'), (2048, 'доставлен'), (16384, 'завершен')])),
                ('user', models.ForeignKey(verbose_name='покупатель', to=settings.AUTH_USER_MODEL, on_delete=models.PROTECT)),
            ],
            options={
                'verbose_name': 'заказ',
                'verbose_name_plural': 'заказы',
            },
        ),
        migrations.CreateModel(
            name='OrderItem',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('product_price', models.PositiveIntegerField(verbose_name='цена товара', default=0)),
                ('discount', models.PositiveIntegerField(verbose_name='скидка', default=0)),
                ('quantity', models.PositiveSmallIntegerField(verbose_name='количество', default=1)),
                ('order', models.ForeignKey(to='shop.Order', related_query_name='item', related_name='items', on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name': 'позиция заказа',
                'verbose_name_plural': 'позиции заказа',
            },
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('code', models.CharField(verbose_name='код', max_length=20)),
                ('article', models.CharField(verbose_name='артикуль', blank=True, max_length=20)),
                ('partnumber', models.CharField(verbose_name='partnumber', blank=True, max_length=200)),
                ('title', models.CharField(verbose_name='название', max_length=200)),
                ('price', models.PositiveIntegerField(verbose_name='цена, руб', default=0)),
                ('image_prefix', models.CharField(verbose_name='префикс изображения', max_length=200)),
                ('pct_discount', models.PositiveSmallIntegerField(verbose_name='скидка, %', default=0)),
                ('val_discount', models.PositiveIntegerField(verbose_name='скидка, руб', default=0)),
                ('max_discount', models.PositiveSmallIntegerField(verbose_name='макс. скидка, %', default=100)),
            ],
            options={
                'verbose_name': 'товар',
                'verbose_name_plural': 'товары',
            },
        ),
        migrations.AddField(
            model_name='orderitem',
            name='product',
            field=models.ForeignKey(verbose_name='товар', to='shop.Product', related_name='+', on_delete=models.PROTECT),
        ),
        migrations.AddField(
            model_name='basketitem',
            name='product',
            field=models.ForeignKey(to='shop.Product', related_name='+', on_delete=models.PROTECT),
        ),
    ]
