from django.apps import AppConfig
from django.contrib import admin
from django.contrib.admin.apps import AdminConfig

from lock_tokens.apps import LockTokensConfig


class SWAppConfig(AppConfig):
    name = 'sewingworld'
    verbose_name = 'Швейный Мир'

    def ready(self):
        import djconfig
        from .forms import SWConfigForm
        djconfig.register(SWConfigForm)

        from .admin import configure_admin
        configure_admin()


class SWAdminConfig(AdminConfig):
    default_site = 'sewingworld.admin.SWAdminSite'


class SWLockTokensConfig(LockTokensConfig):
    verbose_name = "Блокировки"
