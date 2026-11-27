"""
Tabler icons in place of Django's admin ones (sewingworld/management/commands/admin_icons.py). They must keep up with
Django: a new icon, another size or a moved sprite icon calls for running the command again.
"""
import re

from django.contrib.staticfiles import finders
from django.test import SimpleTestCase

from sewingworld.management.commands.admin_icons import DJANGO_ICONS, ICONS


def svg(path):
    source = path.read_text()
    tag = re.search(r'<svg\b[^>]*>', source, re.S).group(0)
    size = tuple(re.search(rf'\b{name}="([^"]*)"', tag).group(1) for name in ('width', 'height'))
    view_box = re.search(r'\bviewBox="([^"]*)"', tag).group(1)
    uses = [tuple(re.search(rf'\b{name}="([^"]*)"', use).group(1) for name in ('xlink:href', 'x', 'y'))
            for use in re.findall(r'<use\b[^>]*?/>', source, re.S)]
    return size, view_box, uses


class AdminIconTests(SimpleTestCase):
    def test_every_django_icon_is_replaced(self):
        self.assertEqual(sorted(path.name for path in ICONS.glob('*.svg')),
                         sorted(path.name for path in DJANGO_ICONS.glob('*.svg')))

    def test_icons_keep_django_sizes_and_sprites(self):
        for path in ICONS.glob('*.svg'):
            with self.subTest(path.name):
                size, view_box, uses = svg(path)
                django_size, django_view_box, django_uses = svg(DJANGO_ICONS / path.name)
                self.assertEqual(size, django_size)
                self.assertEqual(uses, django_uses)
                if uses:  # CSS shows a sprite's icons by their place in its viewBox
                    self.assertEqual(view_box, django_view_box)

    def test_they_are_served(self):
        self.assertEqual(finders.find('admin/img/icon-yes.svg'), str(ICONS / 'icon-yes.svg'))
