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
def creation():
    list_cats={}
    nb_cat=0
    for cat_en_cours in Cat.objects.all().order_by('id'):
        try:
            cat_nom,scat_nom=cat_en_cours.nom.split(":")
            if scat_nom:
                list_cats[cat_en_cours.id]={'cat':{'id':cat_en_cours.id,'nom':cat_nom,'type':cat_en_cours.type},'scat':{'id':cat_en_cours.id,'nom':scat_nom}}
            else:
                list_cats[cat_en_cours.id]={'cat':{'id':cat_en_cours.id,'nom':cat_en_cours.nom},'scat':None}
        except ValueError:
             list_cats[cat_en_cours.id]={'cat':{'id':cat_en_cours.id,'nom':cat_en_cours.nom},'scat':None}
    return list_cats
def toto():

    xml_root = et.Element("Grisbi")
    xml_cat_root = et.SubElement(xml_root, "Categories")
    xml_detail = et.SubElement(xml_cat_root, 'Detail_des_categories')
    xml_cate = et.SubElement(xml_detail, 'Categorie')
    old_cat=''
    l=creation()
    for c in l.values():
        if old_cat != c['cat']['nom']:

            if old_cat == '':
                xml_cate.set('No', str(c['cat']['id']))
                xml_cate.set('Nom', c['cat']['nom'])
            else:
                xml_cate.set('No_derniere_sous_cagegorie', str(c['cat']['id']-1))
                xml_cate = et.SubElement(xml_detail, 'Categorie')
                xml_cate.set('No', str(c['cat']['id']))
                xml_cate.set('Nom', unicode(c['cat']['nom']))
            old_cat=c['cat']['nom']
        if c['scat']:
            xml_sub = et.SubElement(xml_cate, 'Sous-categorie')
            xml_sub.set('No', str(c['cat']['id']))
            xml_sub.set('Nom', unicode(c['scat']['nom']))
    xml_cate.set('No_derniere_sous_cagegorie', str(c['cat']['id']))
    return et.tostring(xml_root, method="xml", xml_declaration=True, pretty_print=True)

if __name__ == "__main__":
    t=toto()
#    pprint.pprint(creation(),indent=4)
    print t