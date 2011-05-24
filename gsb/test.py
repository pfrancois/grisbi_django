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

def toto():
    tabl_correspondance_banque={}
    xml_tree = et.parse('20040701.gsb')
    root = xml_tree.getroot()
    connection.cursor().execute("delete from %s;"%'banque')
    nb = 0
    for xml_element in xml_tree.find('Banques/Detail_des_banques'):
        nb += 1
        element,created=Banque.objects.get_or_create(nom=xml_element.get('Nom'),defaults={'cib':xml_element.get('Code'), 'notes':xml_element.get('Remarques')})
        tabl_correspondance_banque[xml_element.get('No')]=element.id
    return tabl_correspondance_banque

if __name__ == "__main__":
    t=toto()
#    pprint.pprint(creation(),indent=4)
    print t