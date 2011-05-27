# -*- coding: utf-8 -*-
if __name__ == "__main__":
    from django.core.management import setup_environ
    import sys, os

    sys.path.append(os.path.realpath(os.path.join(os.path.dirname(__file__), '../..')))
    from mysite import settings

    setup_environ(settings)

import logging
from django.conf import settings
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
    tabl_correspondance_ib={}
    xml_tree = et.parse("%s/test_files/test_original.gsb"%(os.path.dirname(os.path.abspath(__file__))))
    root = xml_tree.getroot()
    connection.cursor().execute("delete from %s;"%'ib')
    nb_ib=0
    nb_nx=0
    for xml_element in xml_tree.find('//Detail_des_imputations'):
        logger.debug("ib %s"%xml_element.get('No'))
        nb_ib += 1
        query={'nom':"%s:"%(xml_element.get('Nom'),),'type':liste_type_cat[int(xml_element.get('Type'))][0]}
        element,created=Ib.objects.get_or_create(nom=query['nom'],defaults=query)
        tabl_correspondance_ib[xml_element.get('No')]={'0':element.id}
        if created:
            nb_nx += 1
            logger.debug('ib %s cree au numero %s'%(int(xml_element.get('No')),element.id))
        for xml_sous in xml_element:
            logger.debug("ib %s: sib %s"%(xml_element.get('No'),xml_sous.get('No')))
            nb_ib += 1
            query={'nom':"%s:%s"%(xml_element.get('Nom'),xml_sous.get('Nom')),'type':liste_type_cat[int(xml_element.get('Type'))][0]}
            element,created=Ib.objects.get_or_create(nom=query['nom'],defaults=query)
            tabl_correspondance_ib[xml_element.get('No')][xml_sous.get('No')]=element.id
            if created:
                logger.debug('sib %s:%s cree au numero %s'%(int(xml_element.get('No')),int(xml_sous.get('No')),element.id))
    logger.debug(u"%s imputations dont %s nouveaux"%(nb_ib,nb_nx))
    return tabl_correspondance_ib

if __name__ == "__main__":
    t=toto()
#    logger.debug(creation(),indent=4)
    print t