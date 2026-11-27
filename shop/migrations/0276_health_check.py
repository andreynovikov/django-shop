"""
IntegrationCheck becomes HealthCheck, which also holds the checks without an integration (SMS, Celery's queues,
broker and beat), keeping its rows: one check per integration and operation, and per operation for those without.
"""
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0275_product_gtin_like_index'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='integrationcheck',
            name='shop_integrationcheck_unique',
        ),
        migrations.RenameModel(
            old_name='IntegrationCheck',
            new_name='HealthCheck',
        ),
        migrations.AlterModelOptions(
            name='healthcheck',
            options={'ordering': ['integration__name', 'operation'], 'verbose_name': 'проверка состояния', 'verbose_name_plural': 'состояние'},
        ),
        migrations.AlterField(
            model_name='healthcheck',
            name='integration',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='checks', to='shop.integration', verbose_name='интеграция'),
        ),
        migrations.AddConstraint(
            model_name='healthcheck',
            constraint=models.UniqueConstraint(fields=('integration', 'operation'), name='shop_healthcheck_unique', nulls_distinct=False),
        ),
    ]
