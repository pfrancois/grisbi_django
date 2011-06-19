# -*- coding: utf-8 -*-
from django import template
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from django.utils import formats
from django.utils.encoding import force_unicode
from django.utils.safestring import mark_safe
from django.template.loader import render_to_string
import logging

register = template.Library()


@register.filter()
def cur(value, symbol="&#8364;"):
    if symbol=='EUR':
        symbol="&#8364;"
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
    return mark_safe("%s %s" % (formats.number_format(d, abs(p)), symbol))
cur.is_safe = True

@register.filter()
def centimes(value):
    return str(Decimal(str(value))*Decimal(100))
centimes.is_safe = True

@register.simple_tag
def bouton_form(id_form, url, param=None ):
    if param:
        return render_to_string('gsb/bouton_validation_formulaires.django.html',{'id_form':id_form,'url_annul':url,'url_param':param})
    else:
        return render_to_string('gsb/bouton_validation_formulaires.django.html',{'id_form':id_form,'url_annul':url})
