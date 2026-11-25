from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0269_alter_category_product_order'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='basket_checkout_key',
            field=models.CharField(max_length=40, unique=True, null=True, blank=True, editable=False),
        ),
    ]
