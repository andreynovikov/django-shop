# Generated by Django 3.2.12 on 2023-02-02 09:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0197_auto_20221211_1126'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.PositiveIntegerField(choices=[(0, 'новый'), (1, 'принят в работу'), (2, 'ожидает подтверждения'), (4, 'комплектуется'), (8, 'отменен'), (16, 'заморожен'), (32, 'передан в другой магазин'), (64, 'собран'), (128, 'сервис'), (1024, 'доставляется'), (2048, 'доставлен'), (256, 'доставлен в магазин'), (512, 'передан в службу доставки'), (4096, 'консультация'), (8192, 'проблема'), (33554432, 'возвращается'), (67108864, 'не востребован'), (16384, 'завершён'), (251658240, 'выполнен')], db_index=True, default=0, verbose_name='статус'),
        ),
    ]
