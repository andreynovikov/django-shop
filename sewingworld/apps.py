from lock_tokens.apps import LockTokensConfig
from django.contrib.admin.apps import AdminConfig


class SWAdminConfig(AdminConfig):
    default_site = 'sewingworld.admin.SWAdminSite'

    
class SWLockTokensConfig(LockTokensConfig):
    verbose_name = "Блокировки"
