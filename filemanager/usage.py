"""
Records that link to a file or a folder from their text, such as <img src> in HTML.

The text fields of every model registered in the admin site are searched for '/' and the path, raw or as in a
URL. That finds '/media/a/b.jpg', 'https://host/media/a/b.jpg' and aliases such as '/a/b.jpg' alike. Searches
are made only on demand, so they may scan whole tables.
"""
from dataclasses import dataclass, field

from django.conf import settings
from django.contrib.admin.utils import quote
from django.db import models
from django.db.models import Q
from django.urls import NoReverseMatch, reverse
from django.utils.encoding import filepath_to_uri
from django.utils.text import Truncator

LIMIT = 20  # records shown per model


@dataclass
class Found:
    name: str
    records: list = field(default_factory=list)  # (text, admin url or None, field names)
    more: bool = False


def needles(path, is_dir):
    suffix = '/' if is_dir else ''
    return {'/' + path + suffix, '/' + filepath_to_uri(path) + suffix}


def searched_models(admin_site):
    excluded = {label.lower() for label in getattr(settings, 'FILEMANAGER_USAGE_EXCLUDE', ())}
    registered = [
        model for model in admin_site._registry
        if isinstance(model, type) and issubclass(model, models.Model)  # django-constance registers a stand-in
    ]
    seen = set()
    for model in sorted(registered, key=lambda model: model._meta.proxy):  # a table once, by its own admin if it has one
        opts = model._meta
        concrete = opts.concrete_model
        if concrete in seen or not opts.managed or opts.app_label in excluded or opts.label_lower in excluded:
            continue
        seen.add(concrete)
        fields = [f.name for f in opts.concrete_fields if isinstance(f, models.TextField)]
        if fields:
            yield model, fields


def find_usage(path, is_dir, admin_site):
    """Lists, per model, the records whose text holds the path."""
    found = []
    searched = needles(path, is_dir)
    for model, fields in searched_models(admin_site):
        condition = Q()
        for name in fields:
            for needle in searched:
                condition |= Q(**{f'{name}__contains': needle})
        rows = list(model._default_manager.filter(condition).order_by('pk')[:LIMIT + 1])
        if not rows:
            continue
        group = Found(str(model._meta.verbose_name_plural), more=len(rows) > LIMIT)
        for obj in rows[:LIMIT]:
            matched = [
                str(model._meta.get_field(name).verbose_name) for name in fields
                if any(needle in (getattr(obj, name) or '') for needle in searched)
            ]
            try:
                url = reverse(
                    f'{admin_site.name}:{model._meta.app_label}_{model._meta.model_name}_change', args=[quote(obj.pk)]
                )
            except NoReverseMatch:
                url = None
            group.records.append((Truncator(str(obj)).chars(100), url, matched))
        found.append(group)
    return found
