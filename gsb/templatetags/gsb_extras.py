# -*- coding: utf-8 -*-
from django import template
from decimal import Decimal

from django.utils.encoding import force_unicode
from django.utils.safestring import mark_safe
from django.template.loader import render_to_string
from django.utils.encoding import iri_to_uri
from django.utils.http import urlquote
from django.conf import settings
#import logging

register = template.Library()


@register.filter()
def cur(value,symbol=None):
    '''
    affiche le symbole monetaire 
    @param symbol: symbole monetaire
    @type symbol: string
    '''
    if symbol == None:
        symbol = settings.DEVISE_GENERALE  
    if symbol == 'EUR':
        symbol = "&#8364;"
    return mark_safe("%s %s" % (value , symbol))
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
