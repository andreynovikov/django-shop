import os

from django_prometheus.utils import PowersOf


def _port_range(ports):  # private: settings/__init__.py star-imports this module
    """ The ports of "9110-9115" or of "9130", None for none """
    if not ports:
        return None
    first, _, last = ports.partition('-')
    return range(int(first), int(last or first) + 1)


PROMETHEUS_EXPORT_MIGRATIONS = False
PROMETHEUS_METRICS_EXPORT_ADDRESS = '127.0.0.1'
# Each worker of a uWSGI app exports /metrics/ on the first free port of the app's own range, PROMETHEUS_METRICS_PORTS
# from its ini file (metrics_ports of server_uwsgi_apps in deploy/ansible), so that Prometheus tells the apps apart.
# An app without it exports nothing, as do Celery, the ASGI app and debug runs (settings/__init__.py).
PROMETHEUS_METRICS_EXPORT_PORT_RANGE = _port_range(os.environ.get('PROMETHEUS_METRICS_PORTS'))
PROMETHEUS_LATENCY_BUCKETS = (.01, .025, .05, .075, .1, .25, .5, .75, 1.0, 2.5, 5.0, 7.5, 10.0, 25.0, float("inf"))
PROMETHEUS_BYTES_BUCKETS = PowersOf(2, 26)
