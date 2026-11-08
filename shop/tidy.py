import re

from tidylib import tidy_fragment

from django.core.exceptions import ValidationError


def tidy_html5(value):
    """
    Returns the HTML with every tag closed. The storefronts insert it into their pages as it is, and a tag left open
    there spills over into the page's own markup, so the page fails to hydrate. HTML5 rules keep links around blocks
    (whole banners are links), and empty elements stay, they may be styled.
    """
    if not value:
        return value
    fragment, errors = tidy_fragment(value, options={'indent': 0, 'doctype': 'html5', 'drop-empty-elements': 0})
    # tidy drops comments in front of the content, so commented-out HTML alone comes back empty
    if not fragment and re.sub(r'<!--.*?-->', '', value, flags=re.DOTALL).strip():
        raise ValidationError("Ошибка очистки HTML")
    return fragment
