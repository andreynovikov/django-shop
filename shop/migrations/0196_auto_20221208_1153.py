# Generated by Django 3.2.12 on 2022-12-08 08:53

from django.db import migrations, models
import shop.models.other


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0195_news'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='basketitem',
            options={'ordering': ['id']},
        ),
        migrations.AlterModelOptions(
            name='news',
            options={'ordering': ['-publish_date'], 'verbose_name': 'новость', 'verbose_name_plural': 'новости'},
        ),
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.PositiveIntegerField(choices=[(0, 'новый заказ'), (1, 'принят в работу'), (2, 'ожидает подтверждения'), (4, 'комплектуется'), (8, 'отменен'), (16, 'заморожен'), (32, 'передан в другой магазин'), (64, 'собран'), (128, 'сервис'), (1024, 'доставляется'), (2048, 'доставлен'), (256, 'доставлен в магазин'), (512, 'передан в службу доставки'), (4096, 'консультация'), (8192, 'проблема'), (33554432, 'возвращается'), (67108864, 'не востребован'), (16384, 'завершён'), (251658240, 'выполнен')], db_index=True, default=0, verbose_name='статус'),
        ),
        migrations.AlterField(
            model_name='shopuser',
            name='username',
            field=shop.models.other.UsernameField(max_length=100, verbose_name='псевдоним'),
        ),
    ]
