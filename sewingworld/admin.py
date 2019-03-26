from django.contrib import admin
from django.urls import path

from shop import views


class SWAdminSite(admin.AdminSite):
    site_header = "Швейный Мир"
    site_title = "Административный сайт Швейный Мир"

    def get_urls(self):
        urls = super().get_urls()
        urls = [
            path('goto_order/', self.admin_view(views.goto_order), name='goto_order'),
            path('import1c/', views.import_1c, name='import_1c')
        ] + urls
        return urls
