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
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP #@UnusedImport
from mysite.gsb.models import * #@UnusedWildImport
from django.utils import formats#@UnusedImport
from django.utils.encoding import smart_unicode #@UnusedImport
from django.utils.safestring import mark_safe #@UnusedImport
logger = logging.getLogger('gsb.test')

def test(request):
    logger = logging.getLogger('gsb.test')
    logger.debug('test')
    logger.info(3)
    logger.critical('attention ce est un test critique')

    return render_to_response('gsb/test.djhtm',
                                            {'titre':"TEST",
                                                'test':'test'},
                                            context_instance = RequestContext(request))

liste_type_cat = Cat.typesdep
liste_type_moyen = Moyen.typesdep
liste_type_compte = Compte.typescpt
liste_type_period = Echeance.typesperiod
liste_type_period_perso = Echeance.typesperiodperso
try:
    from lxml import etree as et
except ImportError:
    from xml.etree import cElementTree as et #@UnusedImport
from django.db import connection #@UnusedImport
import time #@UnusedImport
import pprint #@UnusedImport


if __name__ == "__main__":
    nomfich = "%s/20040701.gsb" % (os.path.dirname(os.path.abspath(__file__)))
    #nomfich = "%s/test_files/test_original.gsb" % (os.path.dirname(os.path.abspath(__file__)))
    nomfich = os.path.normpath(nomfich)
    logger.setLevel(40)#change le niveau de log (10 = debug, 20=info)
    xml_tree = et.parse(nomfich)
    xml_tree.getroot()
    list_ope = xml_tree.findall('//Operation')
    nb_ope_final = len(list_ope)
    percent = 1
    for xml_ope in list_ope:
        if xml_ope.get('N'):
            print smart_unicode(xml_ope.get('N'))
            print xml_ope.get('N')


