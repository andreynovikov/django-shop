import django.db.models.deletion
from django.db import migrations, models


def set_existing_target_sites(apps, schema_editor):
    alias = schema_editor.connection.alias
    Integration = apps.get_model('shop', 'Integration')
    integrations = Integration.objects.using(alias).filter(target_site__isnull=True)
    # On a fresh database, Django creates the current Site after migrations run.
    if not integrations.exists():
        return

    Site = apps.get_model('sites', 'Site')
    sites = Site.objects.db_manager(alias)
    sites.clear_cache()
    try:
        integrations.update(target_site_id=sites.get_current().pk)
    finally:
        sites.clear_cache()


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0270_order_basket_checkout_key'),
        ('sites', '0002_alter_domain_unique'),
    ]

    operations = [
        migrations.RenameField(model_name='integration', old_name='site', new_name='source_site'),
        migrations.AlterField(
            model_name='integration',
            name='source_site',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='source_integrations',
                related_query_name='source_integration',
                to='sites.site',
                verbose_name='сайт-источник',
            ),
        ),
        # Add the foreign key constraint after the backfill to avoid deferred trigger events.
        migrations.AddField(
            model_name='integration',
            name='target_site',
            field=models.ForeignKey(
                db_constraint=False,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='integrations',
                related_query_name='integration',
                to='sites.site',
                verbose_name='сайт-витрина',
            ),
        ),
        migrations.RunPython(set_existing_target_sites, migrations.RunPython.noop, elidable=True),
        migrations.AlterField(
            model_name='integration',
            name='target_site',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='integrations',
                related_query_name='integration',
                to='sites.site',
                verbose_name='сайт-витрина',
            ),
        ),
        migrations.AlterField(
            model_name='integration',
            name='output_template',
            field=models.CharField(blank=True, max_length=20, verbose_name='шаблон выгрузки'),
        ),
        migrations.AddConstraint(
            model_name='integration',
            constraint=models.UniqueConstraint(fields=('target_site', 'utm_source'), name='shop_integration_target_utm_unique'),
        ),
        migrations.AlterField(
            model_name='integration',
            name='utm_source',
            field=models.CharField(max_length=20, verbose_name='источник'),
        ),
    ]
