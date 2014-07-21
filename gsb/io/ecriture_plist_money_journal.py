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

class export_icompta_plist(object):
    actions={'I':1,'U':2,'D':3}
    type_revenu = 1
    type_depense = 2
    type_virement = 3

    def __init__(self, remboursement_id, avance_id ,request , carte_bancaire_id=None):
        self.remboursement = remboursement_id
        self.avance = avance_id
        self.carte_bancaire = carte_bancaire_id
        self.code_device = settings.CODE_DEVICE_POCKET_MONEY
        self.request=request
    def ope_unique(self, obj,action_type):
        action=self.actions[action_type]
        with open(os.path.join(settings.PROJECT_PATH,'gsb','templates','export_plist','modele_ope.log'))as template:
            fichier=template.read()
            #type d'action (IUD)
            fichier=fichier.replace(u"{{action}}",u"%s"%action)
            #device code
            fichier=fichier.replace(u"{{device}}",u"%s"%self.code_device)
            #pk
            fichier=fichier.replace(u"{{pk}}",u"%s"%obj.pk)
            if utils.idtostr(obj.cat, membre="nom",defaut=0) not in (u"Opération Ventilée",u"Virement"):
                montant=float(utils.idtostr(obj, membre="montant",defaut=0))
                type_cat=utils.idtostr(obj.cat, membre="type",defaut="d")
                if obj.montant > 0:
                    type_ope = 1
                    if type_cat == 'r':
                        categorie_id = obj.cat_id
                    else:
                        categorie_id = self.remboursement
                else:
                    montant=abs(montant)
                    type_ope = 2
                    if type_cat == 'd':
                        categorie_id = obj.cat_id
                    else:
                        categorie_id = self.avance
            else:
                type_ope = 2
                categorie_id = obj.cat_id
                montant = 0
            fichier=fichier.replace(u"{{amount}}",u"%s"%montant)
            fichier=fichier.replace(u"{{cat_id}}",u"%s"%categorie_id)
            fichier=fichier.replace(u"{{type_ope}}",u"%s"%type_ope)

            #date_ope
            fichier=fichier.replace(u"{{jour}}",u"%s"%obj.date.day)
            fichier=fichier.replace(u"{{mois}}",u"%s"%obj.date.month)
            fichier=fichier.replace(u"{{annee}}",u"%s"%obj.date.year)

            tiers=utils.idtostr(obj.tiers, membre="nom", defaut="rien")
            fichier=fichier.replace(u"{{tiers}}",u"%s"%tiers)
            #last update timestamp
            if action_type=='I':
                fichier=fichier.replace(u"{{last_update}}",u"%s"%0)
            else:
                fichier=fichier.replace(u"{{last_update}}",u"%s"%utils.datetotimestamp(obj.lastupdate))
            #compte
            fichier=fichier.replace(u"{{compte_id}}",u"%s"%obj.compte_id)
            filename=self.filename
            messages.success(self.request,"dans fichier %s"%filename)
            with codecs.open(os.path.join(filename), 'w', "utf-8") as f:
                f.write(smart_unicode(fichier))

    def compte_unique(self, obj,action_type):
        action=self.actions[action_type]
        with open(os.path.join(settings.PROJECT_PATH,'gsb','templates','export_plist','modele_compte.log'))as template:
            fichier=template.read()
            #type d'action (IUD)
            fichier=fichier.replace(u"{{action}}",u"%s"%action)
            #device code
            fichier=fichier.replace(u"{{device}}",u"%s"%self.code_device)
            #couleur
            color_hexa=utils.idtostr(obj, membre="couleur", defaut="#FFFFFF")[1:]
            if color_hexa==u'' or color_hexa=='':
                color_hexa="0"
            color=int(color_hexa, 16)
            fichier=fichier.replace(u"{{color}}",u"%s"%color)
            #last update timestamp
            if action_type=='I':
                fichier=fichier.replace(u"{{last_update}}",u"%s"%0)
            else:
                fichier=fichier.replace(u"{{last_update}}",u"%s"%utils.datetotimestamp(obj.lastupdate))
            #pk
            fichier=fichier.replace(u"{{pk}}",u"%s"%obj.pk)
            #symbol
            if action_type  != "D":
                symbol=list(models.Compte.objects.order_by('id').values_list('id',flat=True)).index(obj.pk)
            else:
                symbol=0
            fichier=fichier.replace(u"{{symbol}}",u"%s"%(symbol%9))
            #place
            if action_type  != "D":
                place=list(models.Compte.objects.order_by('id').values_list('id',flat=True)).index(obj.pk)
            else:
                place=0
            fichier=fichier.replace(u"{{place}}",u"%s"%(place%9))
            #nom compte
            fichier=fichier.replace(u"{{nom_compte}}",u"%s"%obj.nom)
            filename=self.filename
            messages.success(self.request,"dans fichier %s"%filename)
            with codecs.open(os.path.join(filename), 'w', "utf-8") as f:
                f.write(smart_unicode(fichier))

    def cat_unique(self, obj,action_type):
        action=self.actions[action_type]
        with open(os.path.join(settings.PROJECT_PATH,'gsb','templates','export_plist','modele_cat.log'))as template:
            fichier=template.read()
            #type d'action (IUD)
            fichier=fichier.replace(u"{{action}}",u"%s"%action)
            #device code
            fichier=fichier.replace(u"{{device}}",u"%s"%self.code_device)
            #couleur
            color_hexa=utils.idtostr(obj, membre="couleur", defaut="#FFFFFF")[1:]
            if color_hexa==u'' or color_hexa=='':
                color_hexa="0"
            color=int(color_hexa, 16)
            fichier=fichier.replace(u"{{color}}",u"%s"%color)
            #last update timestamp
            if action_type=='I':
                fichier=fichier.replace(u"{{last_update}}",u"%s"%0)
            else:
                fichier=fichier.replace(u"{{last_update}}",u"%s"%utils.datetotimestamp(obj.lastupdate))
            #pk
            fichier=fichier.replace(u"{{pk}}",u"%s"%obj.pk)
            #place
            if action_type  != "D":
                place=list(models.Cat.objects.order_by('id').values_list('id',flat=True)).index(obj.pk)
            else:
                place=0
            fichier=fichier.replace(u"{{place}}",u"%s"%(place%9))
            #type cat (rd)
            if obj.type == 'r':
                type_cat = self.type_revenu
            else:
                type_cat = self.type_depense
            fichier=fichier.replace(u"{{type_cat}}",u"%s"%type_cat)
            #nom cat
            fichier=fichier.replace(u"{{nom_cat}}",u"%s"%obj.nom)
            filename=self.filename
            messages.success(self.request,"dans fichier %s"%filename)
            with codecs.open(os.path.join(filename), 'w', "utf-8") as f:
                f.write(smart_unicode(fichier))
        return None

    @property
    def filename(self):
        ref_temp = int(utils.datetotimestamp(utils.now()))
        directory = os.path.join(settings.DIR_DROPBOX, 'Applications', 'Money Journal', 'log', str(ref_temp)[:3], str(ref_temp)[3:4],
                                 str(ref_temp)[4:5])
        filename = os.path.join(directory, "{0:d}.log".format(ref_temp * 1000))
        if not os.path.exists(directory):
            os.makedirs(directory)
        if os.path.isfile(filename):
            time.sleep(2)
            ref_temp = int(utils.datetotimestamp(utils.now()))
            directory = os.path.join(settings.DIR_DROPBOX, 'Applications', 'Money Journal', 'log', str(ref_temp)[:3],
                                     str(ref_temp)[3:4], str(ref_temp)[4:5])
            filename = os.path.join(directory, "{0:d}.log".format(ref_temp * 1000))
            if not os.path.exists(directory):
                os.makedirs(directory)
        return filename
    def all_since_date(self, lastmaj):
        nb=collections.Counter()
        dict_do={u"ope":list(),u"cat":list(),u'compte':list()}
        for element in models.Db_log.objects.filter(date_time_created__gte=lastmaj,datamodel__in=['ope','cat','compte']).order_by('id'):
            messages.success(self.request, u"%s"%element)
            nb[element.datamodel]+=1
            if element.datamodel == "ope":
                try:
                    self.ope_unique(models.Ope.objects.get(id=element.id_model),action_type=element.memo,)
                    if element.memo=="I":
                        dict_do[element.datamodel].append(element.id_model)
                    else:
                        if element.id_model in dict_do[element.datamodel]:
                            nb[element.datamodel]-=1
                        else:
                            dict_do[element.datamodel].append(element.id_model)
                except models.Ope.DoesNotExist:
                    obj=utils.AttrDict()
                    obj.pk=element.id_model
                    obj.cat=0
                    obj.cat_id=0
                    obj.montant=0
                    obj.moyen=0
                    obj.lastupdate=0
                    obj.compte_id=0
                    obj.date=datetime.datetime(2000,1,1)
                    obj.tiers="rien"
                    self.ope_unique(obj,action_type=element.memo)
            if element.datamodel == "cat":
                try:
                    self.cat_unique(models.Cat.objects.get(id=element.id_model),action_type=element.memo)
                    if element.memo=="I":
                        dict_do[element.datamodel].append(element.id_model)
                    else:
                        if element.id_model in dict_do[element.datamodel]:
                            nb[element.datamodel]-=1
                        else:
                            dict_do[element.datamodel].append(element.id_model)
                except models.Cat.DoesNotExist:
                        obj=utils.AttrDict()
                        obj.couleur="#FFFFFF"
                        obj.lastupdate=lastmaj
                        obj.pk=element.id_model
                        obj.type='r'
                        obj.nom=''
                        self.cat_unique(obj,action_type=element.memo)
            if element.datamodel == "compte":
                try:
                    obj=models.Compte.objects.get(id=element.id_model)
                    self.compte_unique(obj,action_type=element.memo)
                    if element.memo=="I":
                        dict_do[element.datamodel].append(element.id_model)
                    else:
                        if element.id_model in dict_do[element.datamodel]:
                            nb[element.datamodel]-=1
                        else:
                            dict_do[element.datamodel].append(element.id_model)
                except models.Compte.DoesNotExist:
                    obj=utils.AttrDict()
                    obj.couleur="#FFFFFF"
                    obj.lastupdate=lastmaj
                    obj.pk=element.id_model
                    obj.type='e'
                    obj.nom=''
                    self.compte_unique(obj,action_type=element.memo)
        return nb
