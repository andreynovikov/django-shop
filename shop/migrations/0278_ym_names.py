"""
The beru package became ym: its tasks in the beat schedule and its constance setting take the new names.
"""
from django.db import migrations
from django.utils import timezone

TASKS = {
    'beru.tasks.get_orders': 'ym.tasks.get_orders',
    'beru.tasks.get_integration_orders': 'ym.tasks.get_integration_orders',
    'beru.tasks.sync_integration_order': 'ym.tasks.sync_integration_order',
    'beru.tasks.notify_beru_order_status': 'ym.tasks.notify_order_status',
    'beru.tasks.notify_beru_product_stocks': 'ym.tasks.notify_product_stocks',
    'beru.tasks.notify_beru_marked_stocks': 'ym.tasks.notify_marked_stocks',
    'beru.tasks.notify_beru_integration_stocks': 'ym.tasks.notify_integration_stocks',
}
SETTINGS = {'sw_beru_delivery': 'sw_ym_delivery'}


def rename(apps, tasks, settings):
    PeriodicTask = apps.get_model('django_celery_beat', 'PeriodicTask')
    PeriodicTasks = apps.get_model('django_celery_beat', 'PeriodicTasks')
    Constance = apps.get_model('constance', 'Constance')
    changed = 0
    for old, new in tasks.items():
        changed += PeriodicTask.objects.filter(task=old).update(task=new)
    if changed:
        # beat reloads its schedule when this changes, as django_celery_beat's own saves do
        PeriodicTasks.objects.update_or_create(ident=1, defaults={'last_update': timezone.now()})
    for old, new in settings.items():
        if not Constance.objects.filter(key=new).exists():
            Constance.objects.filter(key=old).update(key=new)


def forwards(apps, schema_editor):
    rename(apps, TASKS, SETTINGS)


def backwards(apps, schema_editor):
    rename(apps, {new: old for old, new in TASKS.items()}, {new: old for old, new in SETTINGS.items()})


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0277_import_run'),
        ('django_celery_beat', '0019_alter_periodictasks_options'),
        ('constance', '0003_drop_pickle'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
