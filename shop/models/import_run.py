from datetime import datetime, timedelta

from django.db import IntegrityError, models, transaction
from django.utils import timezone
from django.utils.formats import date_format

__all__ = [
    'ImportRun'
]

MAX_ERROR = 4000


class ImportRun(models.Model):
    """
    A run of the 1C stock and price import (shop/tasks/stocks.py), its stage and result. active is True while it runs
    and unique, so that one runs at a time. A run whose worker died, killed at TIME_LIMIT, stays active until STALE
    after its start: it no longer counts as running, and the next run takes over and marks it failed. While a run
    runs, products can't be saved (ProductAdminForm.clean()). The admin's top bar shows status().
    """
    RUNNING, COPYING, DONE, FAILED = 'running', 'copying', 'done', 'failed'
    STAGES = [(RUNNING, 'идёт'), (COPYING, 'замена остатков'), (DONE, 'завершён'), (FAILED, 'не удался')]
    TIME_LIMIT = timedelta(hours=2)  # the task's time_limit
    STALE = TIME_LIMIT + timedelta(minutes=5)
    # The colours of the top bar's indicator, see templates/admin/base_site.html
    COLORS = {RUNNING: 'gold', COPYING: 'darkorange', FAILED: 'red', DONE: 'limegreen'}

    file = models.CharField('файл', max_length=255)
    file_date = models.DateTimeField('дата выгрузки', null=True, blank=True)
    stage = models.CharField('этап', max_length=10, choices=STAGES, default=RUNNING)
    active = models.BooleanField(null=True, unique=True, editable=False)
    started_at = models.DateTimeField('начат', default=timezone.now, db_index=True)
    finished_at = models.DateTimeField('закончен', null=True, blank=True)
    imported = models.PositiveIntegerField('строк', null=True, blank=True)
    updated = models.PositiveIntegerField('обновлено цен', null=True, blank=True)
    errors = models.PositiveIntegerField('ошибок в файле', null=True, blank=True)
    error = models.TextField('ошибка', blank=True)

    class Meta:
        verbose_name = 'импорт 1С'
        verbose_name_plural = 'импорты 1С'
        ordering = ['-started_at']

    def __str__(self):
        return f'{self.file} {date_format(timezone.localtime(self.started_at), "d.m.Y H:i")}'

    @classmethod
    def running(cls):
        """ The run in progress, if a live one is """
        return cls.objects.filter(active=True, started_at__gt=timezone.now() - cls.STALE).first()

    @classmethod
    def start(cls, file):
        """ A new run of the file, or None while another one runs; a stale one is marked failed """
        now = timezone.now()
        with transaction.atomic():
            cls.objects.filter(active=True, started_at__lte=now - cls.STALE).update(
                active=None, stage=cls.FAILED, finished_at=now,
                error='Импорт не закончился: обработчик Celery остановлен или прерван по времени')
            try:
                with transaction.atomic():
                    return cls.objects.create(file=file, active=True, started_at=now)
            except IntegrityError:
                return None

    def set_stage(self, stage):
        self.stage = stage
        self.save(update_fields=['stage'])

    def finish(self, file_date, imported, updated, errors):
        self.file_date = parse_file_date(file_date)
        self.imported, self.updated, self.errors = imported, updated, errors
        self._end(self.DONE)

    def fail(self, error):
        self.error = error if len(error) <= MAX_ERROR else error[:MAX_ERROR - 1] + '…'
        self._end(self.FAILED)

    def _end(self, stage):
        self.stage = stage
        self.active = None
        self.finished_at = timezone.now()
        self.save()

    @classmethod
    def status(cls):
        """ The state of the import for the top bar: its stage, colour, title and the date of the file imported last """
        latest = cls.objects.first()
        done = cls.objects.filter(stage=cls.DONE).first()
        last = date_format(timezone.localtime(done.file_date or done.finished_at), 'd.m.Y H:i') if done else None
        if latest is None:
            return {'stage': None, 'color': cls.COLORS[cls.DONE], 'title': 'Импортов 1С ещё не было', 'last': last}
        stage = latest.stage
        since = date_format(timezone.localtime(latest.started_at), 'd.m.Y H:i')
        if latest.active and latest.started_at <= timezone.now() - cls.STALE:
            stage, title = cls.FAILED, f'Импорт 1С с {since} не закончился: обработчик Celery остановлен'
        elif stage == cls.RUNNING:
            title = f'Импорт 1С идёт с {since}, товары не сохраняются'
        elif stage == cls.COPYING:
            title = f'Импорт 1С с {since} заменяет остатки, товары не сохраняются'
        elif stage == cls.FAILED:
            lines = latest.error.splitlines()
            title = f'Импорт 1С с {since} не удался: {lines[0] if lines else "ошибка"}'
        else:
            title = f'Последний импорт 1С: выгрузка от {last}'
        return {'stage': stage, 'color': cls.COLORS[stage], 'title': title, 'last': last}


def parse_file_date(text):
    """ The export's date from the file's first line, such as 27.11.2026 10:00:00, local time """
    if not text:
        return None
    try:
        return timezone.make_aware(datetime.strptime(text, '%d.%m.%Y %H:%M:%S'))
    except ValueError:
        return None
