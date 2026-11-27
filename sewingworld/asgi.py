"""
ASGI entry of the admin's instant notices, which nginx passes /admin/events/ to (sewingworld/admin_events.py). The
rest of the site runs under uWSGI, see sewingworld/wsgi.py.
"""
import os

from django.conf import settings
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sewingworld.settings")

# The process serves event streams only. Like the Celery workers (sewingworld/celery.py) it starts no django_prometheus
# exporter, whose ports (PROMETHEUS_METRICS_EXPORT_PORT_RANGE) are for the uWSGI workers: taking one on a restart would
# leave a worker without one, and Prometheus would scrape this process in its place.
settings.PROMETHEUS_METRICS_EXPORT_PORT = None
settings.PROMETHEUS_METRICS_EXPORT_PORT_RANGE = None

application = get_asgi_application()
