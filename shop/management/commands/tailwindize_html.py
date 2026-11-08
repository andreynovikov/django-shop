import difflib

from django.apps import apps
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from shop.tailwind_html import FIELDS, Report, classes_in, convert, group_report, read_safelist, safelist_css, site_class


class Command(BaseCommand):
    help = ('Convert Bootstrap and Cartzilla classes in the HTML stored in the database to Tailwind classes. '
            'Runs dry by default; see shop/tailwind_html.py for the rules and the end-of-migration steps.')

    def add_arguments(self, parser):
        parser.add_argument('--write', action='store_true', help='save the converted HTML (default: dry run)')
        parser.add_argument('--model', action='append', help='only this model, e.g. shop.Product (repeatable)')
        parser.add_argument('--field', action='append', help='only this field, e.g. spec (repeatable)')
        parser.add_argument('--diff', action='store_true', help='print a unified diff of every changed value')
        parser.add_argument('--limit', type=int, default=0, help='print at most this many diffs')
        parser.add_argument('--safelist', action='store_true',
                            help="print the frontends' src/backend-safelist.css for the converted HTML and exit")
        parser.add_argument('--check', metavar='SAFELIST',
                            help="list classes of the (converted) HTML that this backend-safelist.css doesn't have")
        parser.add_argument('--force', action='store_true',
                            help='write even though some values are converted already (those are skipped anyway)')

    def selected_fields(self, options):
        models = options['model']
        fields = options['field']
        for label, names in FIELDS.items():
            if models and label not in models:
                continue
            model = apps.get_model(label)
            for name in names:
                if fields and name not in fields:
                    continue
                yield label, model, name

    def handle(self, *args, **options):
        if options['model']:
            unknown = set(options['model']) - set(FIELDS)
            if unknown:
                raise CommandError(f'Unknown models: {", ".join(sorted(unknown))}. Known: {", ".join(FIELDS)}')

        reports = []
        changes = []
        final_classes = {}  # class -> where it is used in the HTML as it will be
        safelist = set()  # Tailwind classes of the converted HTML
        diffs = 0
        for label, model, name in self.selected_fields(options):
            field_report = Report()
            changed = 0
            rows = model.objects.filter(**{f'{name}__contains': 'class'}).values_list('pk', name)
            for pk, value in rows.iterator():
                converted, report = convert(value)
                field_report.update(report)
                for cls in classes_in(converted):
                    final_classes.setdefault(cls, []).append(f'{label}:{pk}:{name}')
                # converted values (after the migration) have only their own classes, which an editor wrote
                safelist.update(classes_in(value) if report.converted else report.emitted)
                if converted == value:
                    continue
                changed += 1
                changes.append((model, pk, name, converted))
                if options['diff'] and (not options['limit'] or diffs < options['limit']):
                    diffs += 1
                    self.stdout.write(''.join(difflib.unified_diff(
                        value.splitlines(keepends=True), converted.splitlines(keepends=True),
                        f'{label}:{pk}:{name}', f'{label}:{pk}:{name} (tailwind)')))
            reports.append(field_report)
            if not options['safelist']:
                notes = [f'{count} {kind}-column rows' for kind, count in sorted(field_report.rows.items())]
                if field_report.converted:
                    notes.append(f'{field_report.converted} converted already')
                self.stdout.write(f'{label}.{name}: {changed} changed' + (f' ({", ".join(notes)})' if notes else ''))

        total, by_old = group_report(reports)
        if options['safelist']:
            self.stdout.write(safelist_css(safelist), ending='')
            return
        if options['check']:
            with open(options['check']) as file:
                allowed = read_safelist(file.read())
            missing = {cls: where for cls, where in final_classes.items() if cls not in allowed and not site_class(cls)}
            for cls, where in sorted(missing.items()):
                self.stdout.write(f'{cls}: {", ".join(where[:5])}{" …" if len(where) > 5 else ""}')
            self.stdout.write(f'{len(missing)} classes are not in {options["check"]}.')
            return

        self.stdout.write('\nMapped:')
        for old, news in sorted(by_old.items(), key=lambda item: -sum(item[1].values())):
            for new, count in news.most_common():
                self.stdout.write(f'  {count:6}  {old} → {new}')
        self.stdout.write('\nKept:')
        for name, count in total.kept.most_common():
            self.stdout.write(f'  {count:6}  {name}')
        self.stdout.write('\nDropped:')
        for name, count in total.dropped.most_common():
            self.stdout.write(f'  {count:6}  {name}')

        if total.converted:
            self.stdout.write(f'\n{total.converted} values have Tailwind classes already and were skipped.')
        if not options['write']:
            self.stdout.write(f'\nDry run: {len(changes)} values would change. Run with --write to save them.')
            return

        if total.converted and not options['force']:
            raise CommandError('Some values are converted already, so the migration may have run before. '
                               'Check them, then use --force to convert the others.')
        # QuerySet.update() skips save(): no price recalculation, Celery tasks or revalidation signals
        with transaction.atomic():
            for model, pk, name, converted in changes:
                model.objects.filter(pk=pk).update(**{name: converted})
        self.stdout.write(self.style.SUCCESS(f'\nSaved {len(changes)} values.'))
