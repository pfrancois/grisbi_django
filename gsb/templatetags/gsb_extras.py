# -*- coding: utf-8 -*-
from django import template
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from django.utils import formats
from django.utils.encoding import force_unicode
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter()
def cur(value, symbol="&#8364;"):
    pos_inf = 1e200 * 1e200
    neg_inf = -1e200 * 1e200
    nan = (1e200 * 1e200) / (1e200 * 1e200)
    special_floats = [str(pos_inf), str(neg_inf), str(nan)]

    try:
        input_val = force_unicode(value)
        d = Decimal(input_val)
    except UnicodeEncodeError:
        return u''
    except InvalidOperation:
        if input_val in special_floats:
            return input_val
        try:
            d = Decimal(force_unicode(float(value)))
        except (ValueError, InvalidOperation, TypeError, UnicodeEncodeError):
            return u''
    p = int(2)
    try:
        m = int(d) - d
    except (ValueError, OverflowError, InvalidOperation):
        return input_val
    if p == 0:
        exp = Decimal(1)
    else:
        exp = Decimal(u'1.0') / (Decimal(10) ** abs(p))
    try:
        # Avoid conversion to scientific notation by accessing `sign`, `digits`
        # and `exponent` from `Decimal.as_tuple()` directly.
        sign, digits, exponent = d.quantize(exp, ROUND_HALF_UP).as_tuple()
        digits = [unicode(digit) for digit in reversed(digits)]
        while len(digits) <= abs(exponent):
            digits.append(u'0')
        digits.insert(-exponent, u'.')
        if sign:
            digits.append(u'-')
        number = u''.join(reversed(digits))
        return mark_safe("%s %s" % (formats.number_format(number, abs(p)), symbol))
    except InvalidOperation:
        return input_val

cur.is_safe = True
