from django.db import models
from django.utils.translation import gettext_lazy as _


class File(models.Model):
    """
    No table: the model gives the file browser its place in the admin and its permissions. View is browsing,
    add is uploading new files and making folders, change is replacing, renaming and moving, delete is deleting.
    """
    class Meta:
        managed = False
        verbose_name = _('file')
        verbose_name_plural = _('files')
