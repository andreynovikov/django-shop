# Generated by Django 3.2.12 on 2024-04-16 09:12

from django.db import migrations, models
import django.db.models.deletion
import shop.models.product


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0226_alter_product_gtins'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProductImage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(max_length=255, upload_to=shop.models.product.product_extra_image_path, verbose_name='изображение')),
                ('order', models.PositiveIntegerField()),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='images', to='shop.product')),
            ],
            options={
                'verbose_name': 'изображение товара',
                'verbose_name_plural': 'изображения товара',
                'ordering': ['order'],
            },
        ),
    ]
