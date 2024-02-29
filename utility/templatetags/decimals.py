import math
import decimal

from django import template


register=template.Library()

@register.filter
def percentage(value, percent=100):
    """
    Calculates percentage of a number and rounds it up.
    """
    return int(math.ceil(value * percent / 100))

@register.filter
def round_up(value, decimals=0):
    """
    Takes a number and rounds it up to a specified
    number of digits.

    Examples (assuming value="12.345"):
    {% value|round_up %} -> 13
    {% value|round_up:1 %} -> 12.35
    {% value|round_up:-1 %} -> 20
    """
    multiplier = 10 ** decimals
    if decimals > 0:
        return math.ceil(value * multiplier) / multiplier
    else:
        return int(math.ceil(value * multiplier) / multiplier)

@register.filter
def round_down(value, decimals=0):
    """
    Takes a number and rounds it down to a specified
    number of digits.

    Examples (assuming value="12.345"):
    {% value|round_up %} -> 12
    {% value|round_up:1 %} -> 12.34
    {% value|round_up:-1 %} -> 10
    """
    multiplier = 10 ** decimals
    if decimals > 0:
        return math.floor(value * multiplier) / multiplier
    else:
        return int(math.floor(value * multiplier) / multiplier)

@register.filter
def quantize(value, arg=None):
    """
    Takes a float number (23.456) and uses the
    decimal.quantize to round it to a fixed
    exponent. This allows you to specify the
    exponent precision, along with the
    rounding method.

    Examples (assuming value="7.325"):
    {% value|quantize %} -> 7.33
    {% value|quantize:".01,ru" %} -> 7.33 (this is the same as the default behavior)
    {% value|quantize:".01,rd" %} -> 7.32

    Available rounding options (taken from the decimal module):
    ROUND_CEILING (rc), ROUND_DOWN (rd), ROUND_FLOOR (rf), ROUND_HALF_DOWN (rhd),
    ROUND_HALF_EVEN (rhe), ROUND_HALF_UP (rhu), and ROUND_UP (ru)

    Arguments cannot have spaces in them.

    See the decimal module for more info:
    http://docs.python.org/library/decimal.html
    """
    if not isinstance(value, decimal.Decimal):
        value = decimal.Decimal(str(value))
    options=["ru","rf","rd","rhd","rhe","rhu"]
    precision=None;rounding=None
    if arg:
        args=arg.split(",")
        precision=args[0]
        if len(args) > 1:
            rounding=str(args[1])
    if not precision: precision=".01"
    if not rounding or rounding not in options: rounding=decimal.ROUND_UP
    if rounding=="ru":rounding=decimal.ROUND_UP
    elif rounding=="rf": rounding=decimal.ROUND_FLOOR
    elif rounding=="rd": rounding=decimal.ROUND_DOWN
    elif rounding=="rhd": rounding=decimal.ROUND_HALF_DOWN
    elif rounding=="rhe": rounding=decimal.ROUND_HALF_EVEN
    elif rounding=="rhu": rounding=decimal.ROUND_HALF_UP
    return value.quantize(decimal.Decimal(precision),rounding=rounding)
