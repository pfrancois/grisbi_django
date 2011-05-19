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
def toto():

    for table in ('cat',):
        connection.cursor().execute("delete from %s;"%table)
        logger.info(u'table %s effacée'%table)
    logger.info(u"debut du chargement")
    time.clock()
    xml_tree = et.parse("%s/test_files/test_original.gsb"%(os.path.dirname(os.path.abspath(__file__))))
    root = xml_tree.getroot()
    nb_cat = 0
    cat_dic={}
    for xml_element in xml_tree.find('//Detail_des_categories'):
        nb_cat += 1
        cat_dic[int(xml_element.get('No'))]={0:{'cat':nb_cat}}
        cat=Cat.objects.create(id=nb_cat,nom="%s:"%xml_element.get('Nom'),type=liste_type_cat[int(xml_element.get('Type'))][0])
        print cat
        for xml_sous in xml_element:
            nb_cat += 1
            cat_dic[int(xml_element.get('No'))][int(xml_sous.get('No'))]={'cat':nb_cat}
            query={'id':nb_cat,'nom':"%s:%s"%(xml_element.get('Nom'),xml_sous.get('Nom')),'type':liste_type_cat[int(xml_element.get('Type'))][0]}
            cat=Cat.objects.create(**query)
            print cat
        logger.debug(nb_cat)
    logger.debug(time.clock())
    logger.info(u"%s catégories"%nb_cat)
    return cat_dic

if __name__ == "__main__":
    t=toto()
    print t