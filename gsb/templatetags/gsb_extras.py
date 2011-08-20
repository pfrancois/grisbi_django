# -*- coding: utf-8 -*-
from django import template
from decimal import Decimal, InvalidOperation

from django.utils import formats
from django.utils.encoding import force_unicode
from django.utils.safestring import mark_safe
from django.template.loader import render_to_string
from django.utils.encoding import iri_to_uri
#from django.utils.http import urlquote
from django.conf import settings
#import logging

register = template.Library()


@register.filter()
def cur(value,symbol=None):
    '''
    affiche le montant evc son symbole monetaire et comme il faut pour les virgules 
    @param symbol: symbole monetaire
    @type symbol: string
    '''
    if symbol == None:
        symbol = settings.DEVISE_GENERALE  
    if symbol == 'EUR':
        symbol = "&#8364;"
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
    '''
    renvoie un montant en centine
    @param value:le montant a renvoyer
    @type value:comme on veut
    '''
    return str(Decimal(force_unicode(value)) * Decimal(100))
centimes.is_safe = True

@register.simple_tag()
def dev(symbol=None):
    if symbol == None:
        symbol = settings.DEVISE_GENERALE  
    if symbol == 'EUR':
        symbol = "&#8364;"
    return symbol
dev.is_safe = True

@register.simple_tag
def bouton_form(id_form, url, param=None):
    '''
    renvoie les boutons pour valider un formulaire
    @param id_form:
    @type id_form:
    @param url:
    @type url:chaine
    @param param:
    @type param:
    '''
    url=iri_to_uri(url)
    if param:
        return render_to_string('gsb/bouton_validation_formulaires.django.html', {'id_form':id_form, 'url_annul':url, 'url_param':param})
    else:
        return render_to_string('gsb/bouton_validation_formulaires.django.html', {'id_form':id_form, 'url_annul':url})
