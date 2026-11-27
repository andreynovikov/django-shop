"""
Check what the tasks can't report themselves, see shop/health.py:

* sends a heartbeat through each Celery queue, and raises a problem when the broker doesn't take it;
* raises the queues and the scheduled operations of the integrations that stopped succeeding;
* raises a problem when beat hasn't run a periodic task for a while;
* warns before a Wildberries API token expires.

Raised problems are mailed to the managers and posted to the staff channel, and so are the end of a broker, beat or
token problem. The open admin pages get the state of both indicators on each run. The systemd timer health_check@<site>.timer runs it every two minutes, outside Celery, so that it works
when Celery, its broker or beat is down; for the same reason it sends the notices itself. When neither mail nor
Telegram takes them, it fails and leaves the problems unraised for the next run.
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from shop import health
from shop.models import Integration


class Command(BaseCommand):
    help = 'Checks Celery and the integrations, raises what stopped working, and tells the managers'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='report the state only, send and change nothing')

    def handle(self, *args, dry_run=False, **options):
        now = timezone.now()
        if dry_run:
            self.report(now)
            return

        health.record_success(None, health.MONITOR, notify=False)
        # Committed before the heartbeats, which a worker may take at once
        for queue in health.QUEUES:
            health.expect(None, f'celery.{queue}')
        with transaction.atomic():
            raised, restored = health.send_heartbeats()
            raised += health.raise_stale(now)
            for check in (health.check_beat, health.check_tokens):
                more_raised, more_restored = check(now)
                raised += more_raised
                restored += more_restored
            if raised and not health.deliver(raised, raised=True):
                raise CommandError('Neither mail nor Telegram took the notice of raised problems')
        if restored:
            health.deliver(restored, raised=False)
        # The open admin pages, which hear of nothing else when an operation goes stale with time
        for group in health.GROUPS:
            health.publish(group)
        self.stdout.write(f'Raised: {len(raised)}, restored: {len(restored)}')

    def report(self, now):
        for group, title in health.GROUPS.items():
            status = health.summary(group, now)
            self.stdout.write(f"{title}: {status['level']}")
            for item in status['problems']:
                self.stdout.write(f"  {item['level']}: {item['name']}: {item['error']}")
        for integration in Integration.objects.filter(source_site__domain='wildberries.ru', enabled=True):
            expiry = health.token_expiry((integration.settings or {}).get('api_key', ''))
            if expiry is not None:
                self.stdout.write(f'{integration}: token expires {timezone.localtime(expiry):%Y-%m-%d %H:%M}')
