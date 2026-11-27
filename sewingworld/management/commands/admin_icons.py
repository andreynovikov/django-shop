"""
Write Tabler versions of Django's admin icons into staticfiles/admin/img, where they take the place of Django's own
(STATICFILES_DIRS come before the apps' static files).

Each file keeps the name, size and colours of Django's, and a sprite keeps its viewBox and the positions of its
icons, which Django's CSS relies on; only the shapes change. Run it with the directory of the @tabler/icons npm
package after a Django upgrade that tests/test_admin_icons.py fails on, or to update the icons:

    python manage.py admin_icons ~/Workspace/cartzilla/node_modules/@tabler/icons
"""
import json
import re
from pathlib import Path

import django.contrib.admin
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

DJANGO_ICONS = Path(django.contrib.admin.__file__).parent / 'static' / 'admin' / 'img'
ICONS = Path(settings.BASE_DIR) / 'staticfiles' / 'admin' / 'img'

# Django's icon → Tabler outline icon
SINGLE = {
    'icon-addlink': 'plus',
    'icon-changelink': 'pencil',
    'icon-deletelink': 'x',
    'icon-viewlink': 'eye',
    'icon-hidelink': 'eye-off',
    'icon-yes': 'circle-check',
    'icon-yes-dark': 'circle-check',
    'icon-no': 'circle-x',
    'icon-no-dark': 'circle-x',
    'icon-unknown': 'help-circle',
    'icon-unknown-alt': 'help-circle',
    'icon-alert': 'alert-triangle',
    'icon-alert-dark': 'alert-triangle',
    'icon-info': 'info-circle',
    'icon-info-dark': 'info-circle',
    'icon-debug': 'bug',
    'icon-debug-dark': 'bug',
    'inline-delete': 'circle-x',
    'search': 'search',
    'tooltag-add': 'plus',
    'tooltag-arrowright': 'external-link',
}
# Status icons, of booleans and messages, are filled to read at 13px, as Django's solid circles do
FILLED = {'icon-yes', 'icon-yes-dark', 'icon-no', 'icon-no-dark', 'icon-unknown', 'icon-unknown-alt'}
# Django's sprite → its icon ids → Tabler outline icons
SPRITES = {
    'icon-calendar': {'icon': 'calendar'},
    'icon-clock': {'icon': 'clock'},
    'calendar-icons': {'previous': 'circle-chevron-left', 'next': 'circle-chevron-right'},
    'selector-icons': {'up': 'circle-arrow-up', 'down': 'circle-arrow-down',
                       'left': 'circle-arrow-left', 'right': 'circle-arrow-right'},
    'sorting-icons': {'sort': 'selector', 'ascending': 'chevron-up', 'descending': 'chevron-down'},
}
STROKE = 'fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"'
CELL = 512  # Django's sprites put their icons one under another, 512 units apart


def attr(tag, name):
    return re.search(rf'\b{name}="([^"]*)"', tag).group(1)


def svg_tag(source):
    return re.search(r'<svg\b[^>]*>', source, re.S).group(0)


class Command(BaseCommand):
    help = "Write Tabler versions of Django's admin icons into staticfiles/admin/img"

    def add_arguments(self, parser):
        parser.add_argument('tabler', type=Path, help='directory of the @tabler/icons npm package')

    def handle(self, tabler, **options):
        try:
            self.version = json.loads((tabler / 'package.json').read_text())['version']
        except (OSError, ValueError, KeyError) as e:
            raise CommandError(f'{tabler} is not the @tabler/icons package: {e}')
        self.tabler = tabler / 'icons'
        missing = {path.stem for path in DJANGO_ICONS.glob('*.svg')} - set(SINGLE) - set(SPRITES)
        if missing:
            raise CommandError(f'No Tabler icon for {", ".join(sorted(missing))}: add them to SINGLE or SPRITES')

        ICONS.mkdir(parents=True, exist_ok=True)
        for name, icon in SINGLE.items():
            (ICONS / f'{name}.svg').write_text(self.single(name, icon))
        for name, icons in SPRITES.items():
            (ICONS / f'{name}.svg').write_text(self.sprite(name, icons))
        self.stdout.write(f'{len(SINGLE) + len(SPRITES)} icons of Tabler Icons {self.version} written to {ICONS}')

    def shapes(self, name, style='outline'):
        """ The drawing elements of a Tabler icon, without its invisible bounding box """
        try:
            svg = (self.tabler / style / f'{name}.svg').read_text()
        except OSError as e:
            raise CommandError(f'No Tabler icon {style}/{name}: {e}')
        inner = svg[svg.index('>', svg.index('<svg')) + 1:svg.rindex('</svg>')]
        inner = re.sub(r'<path stroke="none" d="M0 0h24v24H0z" fill="none"\s*/>', '', inner)
        return ' '.join(line.strip() for line in inner.splitlines() if line.strip())

    def note(self, name, icons):
        return f'<!-- Tabler Icons {self.version} ({icons}), MIT License, in place of Django\'s {name}.svg -->'

    def single(self, name, icon):
        source = (DJANGO_ICONS / f'{name}.svg').read_text()
        svg = svg_tag(source)
        colors = set(re.findall(r'fill="(#[0-9a-fA-F]+)"', source))
        if len(colors) != 1:
            raise CommandError(f"Django's {name}.svg has {len(colors)} colours, not one")
        color = colors.pop()
        size = f'width="{attr(svg, "width")}" height="{attr(svg, "height")}" viewBox="0 0 24 24"'
        if name in FILLED:
            paint, icons, shapes = f'fill="{color}"', f'{icon}, filled', self.shapes(icon, 'filled')
        else:
            paint, icons, shapes = f'stroke="{color}" {STROKE}', icon, self.shapes(icon)
        return (f'<svg xmlns="http://www.w3.org/2000/svg" {size} {paint}>\n'
                f'  {self.note(name, icons)}\n  {shapes}\n</svg>\n')

    def sprite(self, name, icons):
        source = (DJANGO_ICONS / f'{name}.svg').read_text()
        svg = svg_tag(source)
        view_box = attr(svg, 'viewBox')
        view_width = float(view_box.split()[2])
        cell = min(view_width, CELL)
        scale = cell / 24
        dx, dy = (view_width - cell) / 2, (CELL - cell) / 2
        groups = '\n'.join(
            f'    <g id="{gid}" transform="translate({dx:g} {dy:g}) scale({scale:.4f})" stroke="currentColor" {STROKE}>'
            f'{self.shapes(icon)}</g>' for gid, icon in icons.items())
        uses = []
        for use in re.findall(r'<use\b[^>]*?/>', source, re.S):
            gid = attr(use, 'xlink:href').lstrip('#')
            if gid not in icons:
                raise CommandError(f"Django's {name}.svg uses #{gid}, which SPRITES lacks")
            # The Tabler icons draw in currentColor, the colour Django's fill gave
            uses.append(f'  <use xlink:href="#{gid}" x="{attr(use, "x")}" y="{attr(use, "y")}" color="{attr(use, "fill")}"/>')
        return (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
                f'width="{attr(svg, "width")}" height="{attr(svg, "height")}" viewBox="{view_box}">\n'
                f'  {self.note(name, ", ".join(sorted(set(icons.values()))))}\n  <defs>\n{groups}\n  </defs>\n'
                + '\n'.join(uses) + '\n</svg>\n')
