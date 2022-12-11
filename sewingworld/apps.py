from django.apps import AppConfig
from django.contrib.admin.apps import AdminConfig


class SWAppConfig(AppConfig):
    name = 'sewingworld'
    verbose_name = 'Швейный Мир'

    def ready(self):
        import sewingworld.tasks  # noqa: F401
        import sewingworld.signals  # noqa: F401

        import djconfig
        from .forms import SWConfigForm
        djconfig.register(SWConfigForm)

        from .admin import configure_admin
        configure_admin()


class SWAdminConfig(AdminConfig):
    default_site = 'sewingworld.admin.SWAdminSite'
