"""
Check what the integrations' tasks can't report themselves, see shop/integration_health.py: scheduled operations that
stopped succeeding, and Wildberries API tokens about to expire. Raised problems are mailed to the managers and posted
to the staff channel, and so are problems of expiring tokens that are gone.

The systemd timer integration_check@<site>.timer runs it every 10 minutes, outside Celery, so that it works when
Celery, its broker or beat is down; for the same reason it sends the notices itself. When neither mail nor Telegram
takes them, it fails and leaves the problems unraised for the next run.
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from shop import integration_health
from shop.models import Integration


class Command(BaseCommand):
    help = 'Raises stale integration operations and expiring Wildberries tokens, and tells the managers'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='report the state only, change and send nothing')

    def handle(self, *args, dry_run=False, **options):
        now = timezone.now()
        if dry_run:
            self.report(now)
            return

        with transaction.atomic():
            raised = integration_health.raise_stale(now)
            token_raised, restored = integration_health.check_tokens(now)
            raised += token_raised
            if raised and not integration_health.deliver(raised, raised=True):
                raise CommandError('Neither mail nor Telegram took the notice of raised problems')
        if restored:
            integration_health.deliver(restored, raised=False)
        self.stdout.write(f'Raised: {len(raised)}, restored: {len(restored)}')

    def report(self, now):
        status = integration_health.summary(now)
        for item in status['problems']:
            self.stdout.write(f"{item['level']}: {item['integration']}, {item['operation']}: {item['error']}")
        for integration in Integration.objects.filter(source_site__domain='wildberries.ru', enabled=True):
            expiry = integration_health.token_expiry((integration.settings or {}).get('api_key', ''))
            if expiry is not None:
                self.stdout.write(f'{integration}: token expires {timezone.localtime(expiry):%Y-%m-%d %H:%M}')
        self.stdout.write(f"Level: {status['level']}")
