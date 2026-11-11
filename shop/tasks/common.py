from django.contrib.sites.models import Site

# Dates in SMS: '5 марта', and '5 марта 2027' when not this year
SINGLE_DATE_FORMAT = 'j E'
SINGLE_DATE_FORMAT_WITH_YEAR = 'j E Y'


_default_site = None


def get_default_site():
    global _default_site
    if _default_site is None:
        _default_site = Site.objects.get(domain='www.sewing-world.ru')
    return _default_site
