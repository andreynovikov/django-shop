from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class FileManagerConfig(AppConfig):
    name = 'filemanager'
    verbose_name = _('Files')
    default_auto_field = 'django.db.models.BigAutoField'
