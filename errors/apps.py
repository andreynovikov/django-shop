from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ErrorsConfig(AppConfig):
    name = 'errors'
    verbose_name = _('Server errors')
    default_auto_field = 'django.db.models.BigAutoField'

    def ready(self):
        from . import signals  # noqa: F401
