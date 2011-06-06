# -*- coding: utf-8 -*-
if __name__ == "__main__":
    from django.core.management import setup_environ
    import sys, os

    sys.path.append(os.path.realpath(os.path.join(os.path.dirname(__file__), '../..')))
    from mysite import settings

    setup_environ(settings)

import logging
from django.shortcuts import render_to_response
from django.template import RequestContext
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from mysite.gsb.models import *
from django.utils import formats
from django.utils.encoding import force_unicode
from django.utils.safestring import mark_safe
logger=logging.getLogger('gsb.test')

def test(request):
    logger=logging.getLogger('gsb.test')
    logger.debug('test')
    logger.info(3)
    logger.critical('attention ce est un test critique')

    return render_to_response('gsb/test.django.html',
                                            {'titre':"TEST",
                                                'test':'test'},
                                            context_instance=RequestContext(request))

liste_type_cat = Cat.typesdep
liste_type_moyen = Moyen.typesdep
liste_type_compte = Compte.typescpt
liste_type_period = Echeance.typesperiod
liste_type_period_perso = Echeance.typesperiodperso
try:
    from lxml import etree as et
except ImportError:
    from xml.etree import cElementTree as et
from django.db import connection
import time
import pprint
from django.db import models

def toto():
    devise=Titre.objects.get_or_create(nom="Euro",defaults={'nom':'Euro','isin':'EUR','type':'DEV','tiers':None})[0]
    Generalite.objects.get_or_create(id=1,defaults={'devise_generale':devise})[0]
    c=Compte_titre.objects.get_or_create(nom='test',defaults={'nom':'test','devise':devise, 'type':'a'})[0]
    tiers_sg=Tiers.objects.get_or_create(nom="titre_ test",defaults={'nom':"titre_ test", 'notes':"123456789@ACT",'is_titre':True})[0]
    titre_sg=Titre.objects.get_or_create(nom='test',defaults={'nom':"test", 'isin':"123456789", 'tiers':tiers_sg, 'type':'ACT'})[0]
    req = Ope.objects.filter(compte__id__exact=c.id, mere__exact=None).aggregate(solde=models.Sum('montant'))['solde']
    for titre in c.titres_detenus_set.all():
        print titre.valeur()
if __name__ == "__main__":
    toto()
    print Titres_detenus.objects.get(titre=Titre.objects.get(nom='test'),compte=Compte_titre.objects.get(nom='test')).nombre