# -*- coding: utf-8 -*-
import gsb.io.bplist as bplist
import os
import datetime
import decimal
import collections
from django.db import transaction
from django.conf import settings
from .. import models
from .. import utils
import pytz

#gestion des vues
from django.contrib import messages
from django.shortcuts import render_to_response
from django.template import RequestContext
#from . import import_base

#class Gestion_maj_money_journal(import_base):
#   pass
class Lecture_plist_exception(utils.utils_Exception):
    pass

class Element(object):
    actions={1:'c', 2:'m', 3:'d'}
    sens={1:"r",2:"d","3":"v"}
    types={'Record':'ope','Payment':"compte", 'Category':"categorie", 'Budget':"budget"}

    def __init__(self,fichier):
        self.ligne = 0
        self.datemaj = pytz.timezone(settings.TIME_ZONE).localize(datetime.datetime.fromtimestamp(int(os.path.splitext(os.path.basename(fichier))[0]) / 1000))
        self.plistdict = bplist.readPlist(fichier)
        root=self.plistdict['$objects'][self.plistdict['$top']['$0']['CF$UID']]
        reponse = simp_NSKeyedArchiver(objects=self.plistdict, top=root, level=1,filtre=True)
        self.device=reponse['device']
        self.action=self.actions[reponse['action']]
        self.obj = reponse['object0']
        self.type = self.types[self.obj['$class']]
        self.is_ope = self.type == "ope"
        self.is_cat = self.type == "categorie"
        self.is_compte = self.type == "compte"
        self.is_budget = self.type == "budget"
        self.is_budget=False
        self.lastup = pytz.timezone(settings.TIME_ZONE).localize(datetime.datetime.fromtimestamp(self.obj['lastUpdate'])) if self.obj['lastUpdate'] != 0 else self.datemaj
        self.id = self.obj['pk']
        if self.is_ope:
            self.sens_element = self.sens[self.obj['type']]
            self.cat = self.obj['category']
            self.automatique = False #ameliorer la gestion du truc
            self.cpt = self.obj['payment']
            self.date = self.obj['day']
            if self.sens_element == 'r':
                self.montant = decimal.Decimal(self.obj['amount'])
            else:
                self.montant = decimal.Decimal(self.obj['amount'])*-1
            try:
                self.tiers = self.obj['memo']['NS.string']
            except TypeError:
                self.tiers = self.obj['memo']
        if self.is_cat or self.is_compte:
            self.couleur = self.obj['color']
            try:
                self.nom = self.obj['name']['NS.string']
            except TypeError:
                self.nom = self.obj['name']
            self.place = self.obj['place']
        if self.is_cat:
            self.type_cat=self.sens[self.obj['type']]
        if self.is_compte:
            self.symbol = self.obj['symbol']
    def __unicode__(self):
        if self.is_ope:
            return u"OPE (%s) le %s : %s %s a %s cpt: %s" % (
                self.id,
                self.date.strftime('%d/%m/%Y'),
                self.montant,
                settings.DEVISE_GENERALE,
                self.tiers,
                self.cpt
            )
        if self.is_compte:
            return u"COMPTE (%s) '%s'" % (self.id,self.nom)
        if self.is_cat:
            return u"CAT (%s) '%s' type:%s" % (self.id, self.nom, self.type_cat)
        if self.is_budget:
            return u"BUDGET %s" % self.id
    def __str__(self):
        return unicode(self).encode('utf-8')
    def __repr__(self):
        return self.__str__()

def gestion_maj(request):
    """vue qui gere les maj"""
    try:
        with transaction.atomic():
            config = models.Config.objects.get_or_create(id=1, defaults={'id': 1})[0]
            lastmaj = pytz.utc.localize(config.derniere_import_money_journal)
            nb_import = import_items(lastmaj, request)
            msg_list=list()
            if nb_import['ope']>0:
                msg_list.append(u"opérations importées: {nb['ope']}".format(nb=nb_import))
            if nb_import['compte']>0:
                msg_list.append(u"comptes importés: {nb['compte']}".format(nb=nb_import))
            if nb_import['cat']>0:
                msg_list.append(u"catégories importées: {nb['cat']}".format(nb=nb_import))
            nb_export =  export(lastmaj, request)
            if nb_export['ope']>0:
                msg_list.append(u"opérations exportées: {nb['ope']}".format(nb=nb_export))
            if nb_export['compte']>0:
                msg_list.append(u"comptes exportés: {nb['compte']}".format(nb=nb_export))
            if nb_export['cat']>0:
                msg_list.append(u"catégories exportées: {nb['cat']}".format(nb=nb_export))
            #on gere ceux qu'on elimine car deja pris en en compte

            config.derniere_import_money_journal = utils.now()
            config.save()

            messages.success(request, u", ".join(msg_list))
    except Lecture_plist_exception as exc:
        messages.error(request,exc.msg)
    return render_to_response('generic.djhtm', {'titre': u'intégration des maj recues', }, context_instance=RequestContext(request))





def simp_NSKeyedArchiver(top,objects, level, filtre=False):
    """fonction recursive de simplification des plist
    @param top: niveau a partir duquel on part a cette recursion
    @param objects: object plist initial
    level: level of recursivite
    obj: object plist final"""
    __tab = None
    if isinstance(top, dict):  # dico
        __tab = {}
        if "CF$UID" in top and len(top) == 1:
            return simp_NSKeyedArchiver(objects['$objects'][top["CF$UID"]], objects, level + 1, filtre)
        for cle,element in top.items():
            if cle == "$class" and filtre:
                temp = objects['$objects'][element['CF$UID']]['$classname']
            elif cle == "CF$UID":
                temp = objects['$objects'][element['CF$UID']]
            else:
                temp = element
            if hasattr(temp, '__iter__'):#c'est soir une liste soit un dict
                temp = simp_NSKeyedArchiver(temp, objects, level + 1, filtre)
            if isinstance(temp, dict) and "$class" in temp and temp["$class"]=="Day":
               temp=datetime.date(temp['year'],temp['month'],temp['day'])
            if temp=="$null":
                temp=''
            __tab[cle] = temp
        return __tab
    if isinstance(__tab, list):  # list
        __tab = list()
        for element in __tab:
            __tab.append(simp_NSKeyedArchiver(element, objects, level + 1))
        return __tab
    if __tab is None:
        __tab = top
    return __tab


def check():
    """verifie si des nouvelles opes ont arrives
    renvoi true or false"""
    config = models.Config.objects.get_or_create(id=1, defaults={'id': 1})[0]
    lastmaj = pytz.utc.localize(config.derniere_import_money_journal)
    #verif si des operations sont a importer
    for fichier in utils.find_files(os.path.join(settings.DIR_DROPBOX, 'Applications', 'Money Journal', 'log')):
        ele = Element(fichier)
        if ele.device == 'tototototo':#c'est une operation provenant de ce pc
            continue
        if ele.lastup > lastmaj and ele.sens_element != "d":
            return True
        if ele.datemaj > lastmaj and ele.sens_element == "d":
            return True
    #verif si des operations sont a exporter
    if models.Ope.objects.filter(lastupdate__gte=lastmaj).order_by('lastupdate').count() > 0:
        return True
    return False

def import_items(lastmaj, request=None):
    nb=collections.Counter()
    decimal.getcontext().prec = 6
    list_ele=dict()
    list_ele['ope']=dict()
    list_ele['compte']=dict()
    list_ele['categorie']=dict()
    list_ele['budget']=dict()
    for fichier in utils.find_files(os.path.join(settings.DIR_DROPBOX, 'Applications', 'Money Journal', 'log')):
        ele=Element(fichier)
        messages.info(request,u"fichier: %s" %  os.path.basename(fichier))
        if ele.device == settings.CODE_DEVICE_POCKET_MONEY: #c'est une operation provenant de ce pc
            continue
        if ele.lastup < lastmaj:
            nb['deja'] += 1
            continue
        if ele.action =='c':
            nb[ele.type] += 1
            if not settings.TESTING:
                print "ajout %s (%s) dans le fichier %s" % (ele.type,ele.id,os.path.basename(fichier))
            list_ele[ele.type][ele.id]=ele
        if ele.action=="m":#modif
            if not settings.TESTING:
                print "modif %s (%s) dans le fichier %s" % (ele.type,ele.id,os.path.basename(fichier))
            if ele.id in list_ele[ele.type].keys():
                if list_ele[ele.type][ele.id].action=='c':
                    list_ele[ele.type][ele.id]=ele
                    list_ele[ele.type][ele.id].action='c'
                else:
                    list_ele[ele.type][ele.id]=ele
            else:
                nb[ele.type] += 1
                list_ele[ele.type][ele.id]=ele
        if ele.action =="d":
            if not settings.TESTING:
                print "suppr %s (%s) dans le fichier %s" % (ele.type,ele.id,os.path.basename(fichier))
            if ele.id in list_ele[ele.type].keys():
                if list_ele[ele.type][ele.id].action=='c':
                    del list_ele[ele.type][ele.id]
                    nb[ele.type] -= 1
                else:
                    list_ele[ele.type][ele.id].action="d"
            else:
                nb[ele.type] += 1
                list_ele[ele.type][ele.id]=ele
    #import pprint
    #pprint.pprint(list_ele)
    for ele in list_ele['categorie'].values():
        diff=dict()
        texte=""
        if ele.action =='c':
            if not models.Cat.objects.filter(id=ele.id).exists():
                cat=models.Cat.objects.create(
                    pk=ele.id,
                    nom=ele.nom,
                    type=ele.type_cat,
                    couleur=ele.couleur)
                messages.success(request,u"catégorie (%s) '%s' créée" % (cat.pk,cat))
            else:
                raise Lecture_plist_exception(u"attention la catégorie (%s) existait déja alors qu'on demande de la créer" % ele.id)
        if ele.action=="m":#modif
            try:
                cat = models.Cat.objects.get(id=ele.id)
            except models.Cat.DoesNotExist:
                raise Lecture_plist_exception(u"attention la catégorie (%s) n'existait pas alors qu'on demande de la modifier" % ele.id)
            if not cat.is_editable:
                raise  Lecture_plist_exception(u"impossible de modifier la cat (%s) car elle est par defaut"%cat.id)
            if cat.nom != ele.nom:
                diff['nom']=u"nom: %s => %s" % (cat.nom, ele.nom)
                cat.nom = ele.nom
                texte=diff['nom']
            cat.lastupdate = ele.lastup
            if  cat.couleur != ele.couleur:
                diff['couleur']=u"couleur: %s => %s" % (cat.couleur, ele.couleur)
                cat.couleur = ele.couleur
                texte="%s, %s"%(texte,diff['couleur'])
            if  cat.type != ele.type_cat:
                diff['type']=u"type: %s => %s" % (cat.type, ele.type_cat)
                cat.type = ele.type_cat
                texte="%s, %s"%(texte,diff['type'])
            if diff != dict():
                if texte[0]==u",":
                    texte=texte[2:]
                cat.save()
                messages.success(request,u"catégorie (%s) modifiée comme ca: %s" % (cat.id,texte))
        if ele.action == 'd':
            #on regarde si la cat existe
            try:
                gsb = models.Cat.objects.get(id=ele.id,nom=ele.nom)
            except models.Cat.DoesNotExist:
                raise Lecture_plist_exception(u"attention la catégorie (%s) n'existait pas alors qu'on demande de la supprimer" % ele.id)
            #on regarde si la cat a des opes
            if (models.Echeance.objects.filter(cat=gsb).count() + models.Ope.objects.filter(cat=gsb).count()) >0:
                raise Lecture_plist_exception(u"cat non supprimable '%s' car elle a des ope rattaches" % ele.__unicode__())
            #on regarde si la cat ne fait partie des cat reserves
            if not gsb.is_editable:
                raise  Lecture_plist_exception(u"impossible de supprimer la catégorie (%s) car elle est par défaut"%gsb.id)
            texte = u"catégorie (%s) #%s supprimée" % (gsb.nom,gsb.pk)
            gsb.delete()
            messages.success(request,texte)
    for ele in list_ele['compte'].values():
        diff=dict()
        texte=""
        if ele.action =='c':
            if not models.Compte.objects.filter(id=ele.id).exists():
                gsb=models.Compte.objects.create(
                    pk=ele.id,
                    nom=ele.nom,
                    couleur=ele.couleur)
                messages.success(request,u"compte (%s) '%s' créé" % (gsb.pk, gsb))
            else:
                raise Lecture_plist_exception(u"attention le compte(%s) existait déja alors qu'on demande de le créer" % ele.id)
        if ele.action=="m":#modif
            #on regarde si l'ope existe
            try:
                gsb = models.Compte.objects.get(id=ele.id)
            except models.Compte.DoesNotExist:
                raise Lecture_plist_exception(u"attention le compte '%s' n'existait pas alors qu'on demande de le modifier" % ele.id)
            if gsb.nom != ele.nom:
                diff['nom']=u"nom: %s => %s" % (gsb.nom, ele.nom)
                gsb.nom = ele.nom
                texte=diff['nom']
            gsb.lastupdate = ele.lastup
            if  gsb.couleur != ele.couleur:
                diff['couleur']=u"couleur: %s => %s" % (gsb.couleur, ele.couleur)
                gsb.couleur = ele.couleur
                texte="%s, %s"%(texte,diff['couleur'])
            if diff != dict():
                if texte[0]==u",":
                    texte=texte[2:]
                gsb.save()
                messages.success(request,u"compte (%s) modifié comme ca: %s" % (gsb.id,texte))
        if ele.action == 'd':
            #on regarde si le cpt existe
            try:
                gsb = models.Compte.objects.get(id=ele.id,nom=ele.nom)
            except models.Compte.DoesNotExist:
                raise Lecture_plist_exception(u"attention le compte '%s' n'existe pas pour ce nom (%s) alors qu'on demande de le supprimer" % (ele.id, ele.nom))
            #on regarde si le cpt a des opes
            if sum((models.Echeance.objects.filter(compte=gsb).count(),
                    models.Echeance.objects.filter(compte_virement=gsb).count(),
                    models.Ope.objects.filter(compte=gsb).count())) >0:
                raise Lecture_plist_exception(u"compte non supprimable '%s' # %s car il a des opérations ou des écheances rattachées" % (ele.nom,ele.id))
            texte = u"compte '%s' #%s supprimé" % (gsb.nom,gsb.pk)
            gsb.delete()
            messages.success(request,texte)
    for ele in list_ele['ope'].values():
        texte=""
        if ele.cpt in list_ele['compte'] and list_ele['compte'][ele.cpt].action=='c':
            compte = ele.cpt
        else:
            try:
                compte = models.Compte.objects.get(id=ele.cpt).id
            except models.Compte.DoesNotExist:
                raise Lecture_plist_exception(u"attention le compte (%s) n'existait pas alors qu'on le demande pour l'ope #%s" % (ele.cpt,ele.id))
        if ele.cat in list_ele['categorie'] and list_ele['categorie'][ele.cat].action=='c':
            cat=ele.cat
        else:
            try:
                cat = models.Cat.objects.get(id=ele.cat).id
            except models.Cat.DoesNotExist:
                raise Lecture_plist_exception(u"attention la catégorie (%s) n'existait pas alors qu'on le demande pour l'ope #%s" % (ele.cat,ele.id))
        tiers,created=models.Tiers.objects.get_or_create(nom=ele.tiers,defaults={'nom':ele.tiers})
        if created:
            messages.success(request,u"tiers '%s' crée" % tiers)
        if ele.action =='c':
            if not models.Ope.objects.filter(id=ele.id).exists():
                ope = models.Ope.objects.create(
                        pk=ele.id,
                        compte_id=compte,
                        cat_id = cat,
                        date = ele.date,
                        tiers = tiers,
                        montant=ele.montant,
                        lastupdate=ele.lastup
                    )
                messages.success(request,u"opération '%s' créée" % ope)
            else:
                raise Lecture_plist_exception(u"attention l'opération (%s) existe déja alors qu'on demande de le créer" % ele.id)

        if ele.action=="m":#modif
            try:
                gsb = models.Ope.objects.get(id=ele.id)
            except models.Ope.DoesNotExist:
                raise Lecture_plist_exception(u"attention cette opé '%s' n'existait pas alors qu'on demande de le modifier" % ele.id)
            if gsb.is_mere:
                raise Lecture_plist_exception(u"impossible de modifier cette opé '%s' car elle est mère"%gsb)
            if gsb.is_fille:
                raise Lecture_plist_exception(u"impossible de modifier cette opé '%s' car elle est fille"%gsb)
            if gsb.rapp is not None:
                raise Lecture_plist_exception(u"impossible de modifier cette opé '%s' car elle est rapprochée"%gsb)
            if gsb.compte.ouvert is False:
                raise Lecture_plist_exception(u"impossible de modifier cette opé '%s' car son compte est fermé"%gsb)
            if gsb.jumelle:
                raise Lecture_plist_exception(u"impossible de modifier cette opé '%s' car elle est jumellée"%gsb)
            if gsb.ope_titre_ost is not None or gsb.ope_titre_pmv is not None: # pragma: no cover because trop chiant a tester
                raise Lecture_plist_exception(u"impossible de modifier cette opé '%s' car elle est support d'une opé titre"%gsb)
            if gsb.pointe:
                raise Lecture_plist_exception(u"impossible de modifier cette opé '%s' car elle est pointée"%gsb)
            if gsb.compte_id != compte:
                texte=u"compte: %s => %s\n" % (gsb.compte_id, compte)
                gsb.compte_id = compte
            if gsb.cat_id != cat:
                texte=u"%s, cat: %s => %s\n" % (texte, gsb.cat_id, cat)
                gsb.cat_id = cat
            if gsb.date != ele.date:
                texte=u"%s, date: %s => %s\n" % (texte, gsb.date, ele.date)
                gsb.date = ele.date
            if gsb.montant != ele.montant:
                texte=u"%s, montant: %s => %s\n" % (texte, gsb.montant, ele.montant)
                gsb.montant = ele.montant
            if gsb.tiers != tiers:
                texte=u"%s, tiers: %s => %s\n" % (texte, gsb.tiers, tiers)
                gsb.tiers = tiers
            if texte != u"":
                gsb.save()
                if texte[0]==u",":
                    texte=texte[2:]
                if texte[-1]==u"\n":
                    texte=texte[:-1]
                messages.success(request,u"opération (%s) modifiée comme ca: %s" % (gsb.id,texte))
        if ele.action == 'd':
            try:
                gsb = models.Ope.objects.get(id=ele.id)
            except models.Ope.DoesNotExist:
                raise Lecture_plist_exception(u"attention cette opé '%s' n'existait pas alors qu'on demande de le supprimer" % ele.id)
            if gsb.is_mere:
                raise Lecture_plist_exception(u"impossible de supprimer cette opé '%s' car elle est mère"%gsb)
            if gsb.is_fille:
                raise Lecture_plist_exception(u"impossible de supprimer cette opé '%s' car elle est fille"%gsb)
            if gsb.rapp is not None:
                raise Lecture_plist_exception(u"impossible de supprimer cette opé '%s' car elle est rapprochée"%gsb)
            if gsb.compte.ouvert is False:
                raise Lecture_plist_exception(u"impossible de supprimer cette opé '%s' car son compte est fermé"%gsb)
            if gsb.jumelle:
                raise Lecture_plist_exception(u"impossible de supprimer cette opé '%s' car elle est jumellée"%gsb)
            if gsb.ope_titre_ost is not None or gsb.ope_titre_pmv is not None:
                raise Lecture_plist_exception(u"impossible de supprimer cette opé '%s' car elle est support d'une opé titre"%gsb)
            if gsb.pointe:
                raise Lecture_plist_exception(u"impossible de supprimer cette opé '%s' car elle est pointée"%gsb)
            if  gsb.compte_id != ele.cpt or gsb.date != ele.date or gsb.montant != ele.montant or gsb.tiers.nom != ele.tiers or gsb.cat_id != ele.cat:
                diff=u""
                for d,value in zip(((gsb.compte_id , ele.cpt), (gsb.date ,ele.date), (gsb.montant , ele.montant) ,(gsb.tiers.nom , ele.tiers) , (gsb.cat_id , ele.cat)),('CPT','DATE','montant','tiers','cat')):
                    if d[0]==d[1]:
                        diff=u"%s\n%s"%(diff,u"%s:\t%s==%s"%(value,d[0],d[1]))
                    else:
                        diff=u"%s\n%s"%(diff,u"%s:\t%s!=%s"%(value,d[0],d[1]))
                raise Lecture_plist_exception(u"attention cette opé '%s' existe alors qu'on demande de le supprimer mais elle est différente :%s" % (ele.id,diff))
            texte = u"opération %s supprimée" % gsb
            gsb.delete()
            messages.success(request,texte)
    return nb


def export(lastmaj, request):
    nb=collections.Counter()
    with transaction.atomic():
        return nb

