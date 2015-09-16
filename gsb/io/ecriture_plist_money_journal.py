# -*- coding: utf-8 -*-
import os
from django.conf import settings
from gsb import models
import time

from gsb import utils
from django.utils.encoding import smart_unicode
import collections
import codecs
import datetime
from django.contrib import messages
from dateutil.relativedelta import relativedelta


def filename_for_moneyjournal():
    """cree au besoin les repertoire et renvoit un nom de fichier de la forme """
    ref_temp = utils.datetotimestamp(utils.now())
    directory = os.path.join(settings.DIR_DROPBOX, 'Applications', 'Money Journal', 'log', str(ref_temp)[:3],
                             str(ref_temp)[3:4], str(ref_temp)[4:5])
    name = os.path.join(directory, "%d.log" % (ref_temp * 1000))
    if not os.path.exists(directory):
        os.makedirs(directory)
    if os.path.isfile(name):
        time.sleep(1)
        ref_temp = int(utils.datetotimestamp(utils.now()))
        directory = os.path.join(settings.DIR_DROPBOX, 'Applications', 'Money Journal', 'log', str(ref_temp)[:3],
                                 str(ref_temp)[3:4], str(ref_temp)[4:5])
        name = os.path.join(directory, "{0:d}.log".format(ref_temp * 1000))
        if not os.path.exists(directory):
            os.makedirs(directory)
    return name


class List_element_base(dict):
    """classe abstraite pour list dictionnaire"""
    def add(self,obj,status):
        raise NotImplemented('this is not implemented')
    def set_deleted(self,id,lastupdate):
        raise NotImplemented('this is not implemented')
    def sorted(self):
        keys=self.keys()
        keys.sort()
        return keys

class List_ope(List_element_base):
    """Classe qui gere les operations"""
    def add(self,obj,status):
        self[obj.id] = {'id':obj.id,
                            'tiers':getattr(obj.tiers,"nom",u"Probleme export"),
                            'cat_id':obj.cat_id,
                            'date':obj.date,
                            'type_cat':getattr(obj.cat,"type",u"d"),
                            'montant':float(unicode(obj.montant)),
                            'compte_id':obj.compte_id,
                            'status':status,
                            'lastupdate':obj.lastupdate}
        if status == "I":
            self[obj.id]['lastupdate']=0
    def set_deleted(self,id,lastupdate):
        self[id] = {'id':id,
                    'tiers':"inconnu_efface",
                    'cat_id':0,
                    'date':0,
                    'type_cat':u"d",
                    'montant':0,
                    'compte_id':0}
        self[id]['status'] = 'D'
        self[id]['lastupdate'] = lastupdate


class List_cat_compte(List_element_base):
    def add(self,obj,status):
        self[obj.id]={'id':obj.id,
                      'nom':obj.nom,
                      'type_obj':obj.type,
                      'couleur':obj.couleur,
                      'status':status,
                      'lastupdate':obj.lastupdate}
        if status == "I":
            self[obj.id]['lastupdate']=0
    def set_deleted(self,id,lastupdate):
        self[id]={'id':id,
                  'nom':"inconnu_efface",
                  'type_obj':u"r",
                  'couleur':"#00000"}
        self[id]['status'] = 'D'
        self[id]['lastupdate'] = lastupdate


class Export_icompta_plist(object):
    actions = {'I': 1, 'U': 2, 'D': 3}
    type_revenu = 1
    type_depense = 2
    type_virement = 3

    def __init__(self, request):
        self.remboursement = models.Cat.objects.get_or_create(nom="Remboursement", defaults={"nom": "Remboursement", 'type': 'r'})[0].id
        self.avance = models.Cat.objects.get_or_create(nom="Avance", defaults={"nom": "Avance", 'type': 'd'})[0].id
        self.ventile = models.Cat.objects.get_or_create(nom=u"Opération Ventilée", defaults={"nom": u"Opération Ventilée", 'type': 'd'})[0].id
        self.virement = models.Cat.objects.get_or_create(nom=u"Virement", defaults={"nom": u"Virement", 'type': 'v'})[0].id
        self.code_device = settings.CODE_DEVICE_POCKET_MONEY
        self.request = request

    def ope_unique(self, obj):
        with open(os.path.join(settings.PROJECT_PATH, 'gsb', 'templates', 'export_plist', 'modele_ope.log'))as template:
            chaine = template.read()
            # type d'action (IUD)
            chaine = chaine.replace(u"{{action}}", u"%s" % self.actions[obj['status']])
            # device code
            chaine = chaine.replace(u"{{device}}", u"%s" % self.code_device)
            # pk
            chaine = chaine.replace(u"{{pk}}", u"%s" % obj['id'])
            if obj['cat_id'] not in (self.ventile,self.virement):
                montant = obj['montant']
                if obj['montant'] > 0:
                    type_ope = 1
                    if obj['type_cat'] == 'r':
                        categorie_id = obj['cat_id']
                    else:
                        categorie_id = self.remboursement
                else:
                    montant = abs(obj['montant'])
                    type_ope = 2
                    if obj['type_cat'] == 'd':
                        categorie_id = obj['cat_id']
                    else:
                        categorie_id = self.avance
            else:
                # si virement ou ope ventile
                type_ope = 2
                categorie_id = obj['cat_id']
                montant = 0
            chaine = chaine.replace(u"{{amount}}", u"%s" % montant)
            chaine = chaine.replace(u"{{cat_id}}", u"%s" % categorie_id)
            chaine = chaine.replace(u"{{type_ope}}", u"%s" % type_ope)
            # date_ope
            if obj['date'] != 0:
                chaine = chaine.replace(u"{{jour}}", u"%s" % obj['date'].day)
                chaine = chaine.replace(u"{{mois}}", u"%s" % obj['date'].month)
                chaine = chaine.replace(u"{{annee}}", u"%s" % obj['date'].year)
            else:
                chaine = chaine.replace(u"{{jour}}", u"%s" % '0')
                chaine = chaine.replace(u"{{mois}}", u"%s" % '0')
                chaine = chaine.replace(u"{{annee}}", u"%s" % '0')
            chaine = chaine.replace(u"{{tiers}}", u"%s" % obj['tiers'])
            # last update timestamp
            chaine = chaine.replace(u"{{last_update}}", u"%s" % int(utils.datetotimestamp(obj['lastupdate'])))
            # compte
            chaine = chaine.replace(u"{{compte_id}}", u"%s" % obj['compte_id'])
            file_name = filename_for_moneyjournal()
            with codecs.open(os.path.join(file_name), 'w', "utf-8") as f:
                f.write(smart_unicode(chaine))

    def compte_unique(self, obj):
        with open(os.path.join(settings.PROJECT_PATH, 'gsb', 'templates', 'export_plist', 'modele_compte.log'))as template:
            chaine = template.read()
            # type d'action (IUD)
            chaine = chaine.replace(u"{{action}}", u"%s" % self.actions[obj['status']])
            # device code
            chaine = chaine.replace(u"{{device}}", u"%s" % self.code_device)
            # couleur
            color_hexa = obj['couleur'][1:]
            if color_hexa == u'' or color_hexa == '':
                color_hexa = "0"
            color = int(color_hexa, 16)
            chaine = chaine.replace(u"{{color}}", u"%s" % color)
            # last update timestamp
            chaine = chaine.replace(u"{{last_update}}", u"%s" % int(utils.datetotimestamp(obj['lastupdate'])))
            # pk
            chaine = chaine.replace(u"{{pk}}", u"%s" % obj['id'])
            # symbol
            if obj['status'] != "D":
                symbol = list(models.Compte.objects.order_by('id').values_list('id', flat=True)).index(obj['id'])
            else:
                symbol = 0
            chaine = chaine.replace(u"{{symbol}}", u"%s" % (symbol % 9))
            # place
            if obj['status'] != "D":
                place = list(models.Compte.objects.order_by('id').values_list('id', flat=True)).index(obj['id'])
            else:
                place = 0
            chaine = chaine.replace(u"{{place}}", u"%s" % place)
            # nom compte
            chaine = chaine.replace(u"{{nom_compte}}", u"%s" % obj['nom'])
            filename = filename_for_moneyjournal()
            messages.success(self.request, "dans chaine %s" % filename)
            with codecs.open(os.path.join(filename), 'w', "utf-8") as f:
                f.write(smart_unicode(chaine))

    def cat_unique(self, obj):
        with open(os.path.join(settings.PROJECT_PATH, 'gsb', 'templates', 'export_plist', 'modele_cat.log'))as template:
            chaine = template.read()
            # type d'action (IUD)
            chaine = chaine.replace(u"{{action}}", u"%s" % self.actions[obj['status']])
            # device code
            chaine = chaine.replace(u"{{device}}", u"%s" % self.code_device)
            # couleur
            color_hexa = obj['couleur'][1:]
            if color_hexa == u'' or color_hexa == '':
                color_hexa = "0"
            color = int(color_hexa, 16)
            chaine = chaine.replace(u"{{color}}", u"%s" % color)
            # last update timestamp
            chaine = chaine.replace(u"{{last_update}}", u"%s" % int(utils.datetotimestamp(obj['lastupdate'])))
            # pk
            chaine = chaine.replace(u"{{pk}}", u"%s" % obj['id'])
            # place
            if obj['status'] != "D":
                place = list(models.Cat.objects.order_by('id').values_list('id', flat=True)).index(obj['id'])
            else:
                place = 0
            chaine = chaine.replace(u"{{place}}", u"%s" % place)
            # type cat (rd)
            if obj['type_obj'] == 'r':
                type_cat = self.type_revenu
            else:
                type_cat = self.type_depense
            chaine = chaine.replace(u"{{type_cat}}", u"%s" % type_cat)
            # nom cat
            chaine = chaine.replace(u"{{nom_cat}}", u"%s" % obj['nom'])
            filename = filename_for_moneyjournal()
            messages.success(self.request, "dans fichier %s" % filename)
            with codecs.open(os.path.join(filename), 'w', "utf-8") as f:
                f.write(smart_unicode(chaine))

    def all_since_date(self, lastmaj):
        nb = collections.Counter()
        ope_list = List_ope()
        cat_list = List_cat_compte()
        cpt_list = List_cat_compte()
        # par defaut on parcours les operation modfie max il y a trois mois
        date_min = utils.today() - relativedelta(month=3)
        objs_a_parcourir = models.Db_log.objects.filter(date_time_action__gte=lastmaj, datamodel__in=['ope', 'cat', 'compte'], date_ref__gte=date_min).order_by('id')
        opes = dict((ob.pk, ob) for ob in models.Ope.objects.select_related('compte', 'tiers').filter(id__in=objs_a_parcourir.filter(datamodel="ope").values_list('id_model', flat=True)))
        cats = dict((ob.pk, ob) for ob in models.Cat.objects.order_by('id').all())
        cpts = dict((ob.pk, ob) for ob in models.Compte.objects.order_by('id').all())
        for element in objs_a_parcourir:
            if element.datamodel == "ope":
                obj_list=ope_list
                obj=opes
            if element.datamodel == "compte":
                obj_list=cpt_list
                obj=cpts
            if element.datamodel == "cat":
                obj_list=cat_list
                obj=cats
            if element.type_action == "I" :
                try:
                    nb[element.datamodel] += 1
                    nb['global'] +=1
                    obj_list.add(obj=obj[element.id_model],status=element.type_action)
                except KeyError:
                    # ca veut dire que l'operation a ate efface depuis donc on ne s'y interresse pas
                    nb[element.datamodel] -= 1
                    nb['global'] -=1
                    continue
            if element.type_action == "U":
                try:
                    if element.id_model not in obj_list:
                        
                        nb[element.datamodel] += 1
                        nb['global'] +=1
                    obj_list.add(obj=obj[element.id_model],status=element.type_action)
                except KeyError:
                    # ca veut dire que l'operation a ate efface depuis donc on ne s'y interresse pas
                    nb[element.datamodel] -= 1
                    nb['global'] -=1
                    continue
            if element.type_action == "D":
                if element.id_model not in obj_list:
                    nb[element.datamodel] += 1
                    nb['global'] +=1
                obj_list.set_deleted(element.id_model,element.date_time_action)
        for cat in cat_list.sorted():
            self.cat_unique(cat_list[cat])
        for cpt in cpt_list.sorted():
            self.compte_unique(cpt_list[cpt])
        for ope in ope_list.sorted():
            self.ope_unique(ope_list[ope])
        return nb

