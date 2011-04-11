# -*- coding: utf-8 -*-

from django.core.management import setup_environ
import sys, os, time
sys.path.append(r"G:\django")
from mysite import settings
setup_environ(settings)
from django.db import connection, transaction
from django.core.exceptions import ObjectDoesNotExist

import datetime, time
from django.http import HttpResponse
from django.db.models import Max

from mysite.gsb.models import *
liste_type_cat=Cat.typesdep
liste_type_signe=Moyen.typesdep
liste_type_compte=Compte.typescpt
liste_type_pointage=Ope.typespointage
try:
    from lxml import etree as et
except:
        from xml.etree import cElementTree as et

class LOG(object):
    def __init__(self,niv_actuel,filename,niv_min_pour_apparaitre_dans_le_fichier=125):
        super( LOG, self).__init__()
        self.niv_actuel=niv_actuel
        self.filename=filename
        self.niv_min_pour_apparaitre_dans_le_fichier=niv_min_pour_apparaitre_dans_le_fichier
    def log(self,s,niv_min_pour_apparaitre=2):
        if type(s)!=unicode:
            s=unicode(s)
        if niv_min_pour_apparaitre>=self.niv_actuel:
            print s
        if niv_min_pour_apparaitre>=self.niv_min_pour_apparaitre_dans_le_fichier:
            s=u"%s\n"%s
            f=codecs.open( self.filename, 'a', 'utf-8')
            f.write(s.encode('utf-8'))
            f.close()
    def set(self,niv_actuel):
        self.niv_actuel=niv_actuel
def datefr2time(s):
    try:
        t=time.strptime(str(s),"%d/%m/%Y")
        return "{annee}-{mois}-{jour}".format(annee=t[0],mois=t[1],jour=t[2])
    except ValueError :
        return None
def fr2uk(s):
    if s != None:
        return float(str(s).replace(',' , '.'))
    else:
        return None

log = LOG(1 , 'import_gsb.log')

#for table in ('generalite', 'ope', 'echeance', 'rapp', 'moyen', 'compte', 'scat', 'cat', 'exercice', 'sib', 'ib', 'banque', 'titre', 'devise', 'tiers'):
for table in ( 'ope',):
    connection.cursor().execute("delete from {};".format(table))
    log.log(u'table {} effacée'.format(table))
log.log(u"debut du chargement")
t = time.clock()
xml_tree = et.ElementTree(file = r"test_original.gsb")
root = xml_tree.getroot()

for xml_element in xml_tree.findall( 'Comptes/Compte' ):
    element=Compte.objects.get(id=int(xml_element.find( 'Details/No_de_compte' ).text))
    for xml_sous in xml_element.find('Detail_des_operations'):
        sous,created=element.ope_set.get_or_create(id = int(xml_sous.get('No')), defaults= {'devise':Generalite.objects.get(id=1).devise_generale,'compte':element})
        if created == False:
            if sous.montant != 0 or sous.date != datetime.date.today or sous.moyen != None:
                raise Exception(u'probleme avec les operations')
        sous.date = datefr2time(xml_sous.get('D')),
        sous.save()
        sys.exit()
        sous.date_val = datefr2time(xml_sous.get('Db')),
        sous.montant = fr2uk(xml_sous.get('M')),
        sous.num_cheque=xml_sous.get('Ct'),
        sous.pointe=liste_type_pointage[int(xml_sous.get('P'))][0]
        sous.ismere=bool(int(xml_sous.get('Va')))

        try:
            sous.devise = Devise.objects.get(id=int(xml_sous.get('De')))
        except (ObjectDoesNotExist,TypeError):
            pass

        try:
            sous.tiers = Tiers.objects.get(id=int(xml_sous.get('T')))
        except (ObjectDoesNotExist,TypeError):
            pass
        try:
            sous.cat = Cat.objects.get(id=int(xml_sous.get('C')))
        except (ObjectDoesNotExist,TypeError):
            pass
        else:
            try:
                sous.scat = sous.cat.scat_set.get(grisbi_id=int(xml_sous.get('Sc')))
            except (ObjectDoesNotExist,TypeError):
                pass
        try:
            sous.ib = Ib.objects.get(id=int(xml_sous.get('I')))
        except (ObjectDoesNotExist,TypeError):
            pass
        else:
            try:
                sous.sib = sous.ib.sib_set.get(grisbi_id=int(xml_sous.get('Si')))
            except (ObjectDoesNotExist,TypeError):
                pass
        try:
            sous.moyen= sous.compte.moyen_set.get(grisbi_id=int(xml_sous.get('Ty')))
        except (ObjectDoesNotExist,TypeError):
            pass
        try:
            sous.rapp= Rapp.objects.get(id=int(xml_sous.get('R')))
            if sous.rapp.date > sous.date:
                sous.rapp.date=sous.date
                sous.rapp.save()
        except (ObjectDoesNotExist,TypeError):
            pass
        try:
            sous.exercice= Exercice.objects.get(id=int(xml_sous.get('E')))
        except (ObjectDoesNotExist,TypeError):
            pass
        try:
            sous.jumelle,created=Ope.objects.get_or_create(id = int(xml_sous.get('Ro')), defaults= {'devise':Generalite.objects.get(id=1).devise_generale,'compte':Compte.objects.get(id=int(xml_sous.get('Rc')))})
        except (ObjectDoesNotExist,TypeError):
            pass
        try:
            sous.mere,created=Ope.objects.get_or_create(id = int(xml_sous.get('Va')), defaults= {'devise':Generalite.objects.get(id=1).devise_generale,'compte':element})
        except (ObjectDoesNotExist,TypeError):
            pass
