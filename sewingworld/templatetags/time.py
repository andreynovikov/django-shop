"""
The MIT License (MIT)

Copyright (c) 2015 Esteban Castro Borsani <ecastroborsani@gmail.com>

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the
                                                           
'Software'), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED 'AS IS', WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

from datetime import datetime

from django.template import defaultfilters
from django.utils.translation import ugettext as _
from django.utils.timezone import is_aware, utc
from django import template


register=template.Library()

@register.filter(expects_localtime=True)
def shortnaturaltime(value):
    """
    now, 1s, 1m, 1h, 1 Ene, 1 Ene 2012
    """
    tz = utc if is_aware(value) else None
    now = datetime.now(tz)

    if value > now:  # Future
        return '%(delta)s' % {'delta': defaultfilters.date(value, 'j M \'y')}

    delta = now - value

    if delta.days:
        if defaultfilters.date(now, 'y') == defaultfilters.date(value, 'y'):
            return '%(delta)s' % {'delta': defaultfilters.date(value, 'j M')}

        return '%(delta)s' % {'delta': defaultfilters.date(value, 'j M \'y')}

    if not delta.seconds:
        return _('now')

    count = delta.seconds
    if count < 60:
        return _('%(count)ss') % {'count': count}

    count //= 60
    if count < 60:
        return _('%(count)sm') % {'count': count}

    count //= 60
    return _('%(count)sh') % {'count': count}
