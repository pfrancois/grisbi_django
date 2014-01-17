# -*- coding: utf-8 -*-
from __future__ import absolute_import
from django import template
from decimal import Decimal, InvalidOperation

from django.utils import formats
from django.utils.encoding import force_unicode
from django.utils.safestring import mark_safe
# from django.utils.http import urlquote
from django.conf import settings
# import logging
from django.template import Library, Node, TemplateSyntaxError

register = template.Library()


@register.filter(is_safe=True)
def cur(value, symbol=None):
    """
    affiche le montant evc son symbole monetaire et comme il faut pour les virgules
    @param symbol: symbole monetaire
    @type symbol: string
    """
    if symbol is None:
        symbol = settings.DEVISE_GENERALE
    if symbol == 'EUR':
        symbol = "&#8364;"
    pos_inf = 1e200 * 1e200
    neg_inf = -1e200 * 1e200
    nan = (1e200 * 1e200) / (1e200 * 1e200)
    special_floats = [str(pos_inf), str(neg_inf), str(nan)]
    input_val = force_unicode(value)
    try:
        if input_val in special_floats:
            val_decim = Decimal(0)
        else:
            val_decim = Decimal(input_val)
#   except UnicodeEncodeError:
#       val_decim = Decimal(0)
    except InvalidOperation:
        try:
            val_decim = Decimal(force_unicode(float(value)))
        except (ValueError, InvalidOperation, TypeError, UnicodeEncodeError):
            val_decim = Decimal(0)
    if Decimal('0.0000001') > val_decim > Decimal('-0.0000001'):
        val_decim = 0
    return mark_safe("%s %s" % (formats.number_format(val_decim, 2), symbol))


@register.filter(is_safe=True)
def somme(value, arg):
    return Decimal(force_unicode(value)) + Decimal(force_unicode(arg))


@register.filter(is_safe=True)
def centimes(value):
    """
    renvoie un montant en centine
    @param value:le montant a renvoyer
    @type value:comme on veut
    """
    return unicode(Decimal(force_unicode(value)) * Decimal(100))

