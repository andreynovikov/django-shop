import datetime

from django import template
from django.utils.formats import date_format
from django.utils.safestring import mark_safe

DAY_FORMAT = 'd'
SINGLE_DATE_FORMAT = 'd E'
SINGLE_DATE_FORMAT_WITH_YEAR = 'd E Y'
RANGE_FORMAT = '{}&thinsp;&ndash;&thinsp;{}'

register=template.Library()

@register.filter
def daterange(dates):
    """
    Takes a one or two dates and prints them
    in human friendly range format.
    """
    today = datetime.datetime.today()
    till_date = None
    if isinstance(dates, list):
        from_date = dates[0]
        if len(dates) > 1:
            till_date = dates[1]
    else:
        from_date = dates
    if isinstance(from_date, str):
        from_date = datetime.datetime.strptime(from_date, '%Y-%m-%d')
    if till_date is not None and isinstance(till_date, str):
        till_date = datetime.datetime.strptime(till_date, '%Y-%m-%d')

    base_format = SINGLE_DATE_FORMAT if today.year == from_date.year else SINGLE_DATE_FORMAT_WITH_YEAR
    if till_date is None or from_date == till_date:
        return mark_safe(date_format(from_date, format=base_format))
    else:
        if from_date.year == till_date.year:
            if from_date.month == till_date.month:
                return mark_safe(RANGE_FORMAT.format(
                    date_format(from_date, format=DAY_FORMAT),
                    date_format(till_date, format=base_format)
                ))
            else:
                return mark_safe(RANGE_FORMAT.format(
                    date_format(from_date, format=SINGLE_DAY_FORMAT),
                    date_format(till_date, format=base_format)
                ))
        else:
            return mark_safe(RANGE_FORMAT.format(
                date_format(from_date, format=base_format),
                date_format(till_date, format=SINGLE_DATE_FORMAT_WITH_YEAR)
            ))
