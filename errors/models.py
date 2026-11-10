from datetime import timedelta

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext, gettext_lazy as _


class Error(models.Model):
    """
    Server errors of one kind: the same exception raised at the same place of the code for the same view or task.
    Messages, parameters and the rest of the stack may differ, see recorder.
    """
    class Kind(models.TextChoices):
        REQUEST = 'request', _('Request')
        TASK = 'task', _('Celery task')

    class Severity(models.IntegerChoices):
        LOW = 10, _('Low')
        MEDIUM = 20, _('Medium')
        HIGH = 30, _('High')
        CRITICAL = 40, _('Critical')

    fingerprint = models.CharField(_('fingerprint'), max_length=64, unique=True, editable=False)
    kind = models.CharField(_('kind'), max_length=16, choices=Kind)
    name = models.CharField(_('error'), max_length=255, help_text=_('Exception class or response status'))
    message = models.TextField(_('message'), blank=True, help_text=_('The latest one'))
    source = models.CharField(_('source'), max_length=255, help_text=_('API route, Django view or Celery task'))
    location = models.CharField(_('location in code'), max_length=255, blank=True)
    first_seen = models.DateTimeField(_('first seen'), default=timezone.now)
    last_seen = models.DateTimeField(_('last seen'), default=timezone.now, db_index=True)
    count = models.PositiveIntegerField(_('count'), default=1)
    severity = models.PositiveSmallIntegerField(_('severity'), choices=Severity, default=Severity.MEDIUM)

    class Meta:
        verbose_name = _('error')
        verbose_name_plural = _('errors')
        ordering = ['-last_seen']

    def __str__(self):
        return gettext('%(name)s in %(source)s') % {'name': self.name, 'source': self.source}

    @property
    def frequency(self):
        """ Occurrences per day since the first one, counting at least a day """
        days = max((timezone.now() - self.first_seen) / timedelta(days=1), 1)
        return self.count / days


class ErrorTrace(models.Model):
    """ One occurrence of an error, only the latest ones are kept """
    error = models.ForeignKey(Error, on_delete=models.CASCADE, related_name='traces', verbose_name=_('error'))
    created = models.DateTimeField(_('time'), default=timezone.now)
    message = models.TextField(_('message'), blank=True)
    traceback = models.TextField(_('traceback'), blank=True)
    # [{file, function, lineno, in_app, lines: [[number, text]], vars: [[name, repr]], cause, cause_explicit}]
    frames = models.JSONField(_('stack'), default=list, blank=True)
    context = models.JSONField(_('context'), default=dict, blank=True)

    class Meta:
        verbose_name = _('occurrence')
        verbose_name_plural = _('occurrences')
        ordering = ['-created']

    def __str__(self):
        return timezone.localtime(self.created).strftime('%Y-%m-%d %H:%M:%S')
