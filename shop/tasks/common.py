from django.contrib.sites.models import Site

# Include the year in SMS dates only when it differs from the current year.
SINGLE_DATE_FORMAT = 'j E'
SINGLE_DATE_FORMAT_WITH_YEAR = 'j E Y'


_default_site = None


def get_default_site():
    global _default_site
    if _default_site is None:
        _default_site = Site.objects.get(domain='www.sewing-world.ru')
    return _default_site
