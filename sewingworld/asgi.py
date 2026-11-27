"""
ASGI entry of the admin's instant notices, which nginx passes /admin/events/ to (sewingworld/admin_events.py). The
rest of the site runs under uWSGI, see sewingworld/wsgi.py.
"""
import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sewingworld.settings")

application = get_asgi_application()
