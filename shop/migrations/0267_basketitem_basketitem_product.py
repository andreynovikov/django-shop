from django.db import migrations, models
from django.db.models import Count, Max, Min


def merge_duplicates(apps, schema_editor):
    """
    Concurrent requests could put a product into a basket twice. The first row stays, with the larger quantity:
    the requests were mostly the same one sent twice, so a sum would count the product twice.
    """
    BasketItem = apps.get_model('shop', 'BasketItem')
    groups = BasketItem.objects.values('basket', 'product').annotate(rows=Count('id'), first=Min('id'), largest=Max('quantity')).filter(rows__gt=1)
    for group in groups:
        BasketItem.objects.filter(pk=group['first']).update(quantity=group['largest'])
        BasketItem.objects.filter(basket=group['basket'], product=group['product']).exclude(pk=group['first']).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0266_shopuser_email_verified_phone_verified'),
    ]

    operations = [
        migrations.RunPython(merge_duplicates, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name='basketitem',
            constraint=models.UniqueConstraint(fields=('basket', 'product'), name='basketitem_product'),
        ),
    ]
