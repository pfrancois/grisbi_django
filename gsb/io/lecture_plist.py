# -*- coding: utf-8 -*-
import os
import datetime
import decimal
import collections

from django.db import transaction
from django.conf import settings
import django.utils.timezone as tz

import gsb.io.bplist as bplist
from .. import models
from .. import utils


# cgestion des vues
from django.contrib import messages
from django.shortcuts import render_to_response
from django.template import RequestContext
from .ecriture_plist_money_journal import Export_icompta_plist


class Lecture_plist_exception(utils.utils_Exception):
    pass


class Subelement(utils.AttrDict):
    def __str__(self):
        if self.is_ope:
            return "(%s) le %s : %s %s tiers: %s cpt: %s" % (
                self.id,
                self.date.strftime('%d/%m/%Y'),
                self.montant,
                settings.DEVISE_GENERALE,
                self.tiers,
                self.cpt
            )
        if self.is_compte:
            return "(%s) '%s'" % (self.id, self.nom)
        if self.is_cat:
            return "(%s) '%s' type:%s" % (self.id, self.nom, self.type_cat)
        if self.is_budget:
            return "%s" % self.id


class collection_datas_decodes(object):
    actions = {1: 'c', 2: 'm', 3: 'd'}
    sens = {1: "r", 2: "d", 3: "v"}
    classes = {'Record': 'ope', 'Payment': "compte", 'Category': "categorie", 'Budget': "budget"}

    def __init__(self, fichier):
        self.ligne = 0
        datemaj_nonutc = tz.make_aware(datetime.datetime.fromtimestamp(int(os.path.splitext(os.path.basename(fichier))[0]) / 1000))
        self.datemaj = utils.utctime(datemaj_nonutc)
        self.plistdict = bplist.readPlist(fichier)
        root = self.plistdict['$objects'][self.plistdict['$top']['$0']['CF$UID']]
        reponse_initiale = simp_nskeyedarchiver(objects=self.plistdict, top=root, level=1, filtre=True)
        self.device = reponse_initiale['device']
        self.list_el = list()
        for key in reponse_initiale:
            if 'object' in key:
                i = Subelement()
                i.fichier = fichier
                i.device = reponse_initiale['device']
                i.action = self.actions[reponse_initiale['action']]
                i.datemaj = self.datemaj
                i.obj = reponse_initiale[key]
                i.classe = self.classes[i.obj['$class']]
                i.is_ope = i.classe == "ope"
                i.is_cat = i.classe == "categorie"
                i.is_compte = i.classe == "compte"
                i.is_budget = i.classe == "budget"
                i.lastup = utils.utctime(datetime.datetime.fromtimestamp(i.obj['lastUpdate'])) if i.obj['lastUpdate'] != 0 else self.datemaj
                i.id = i.obj['pk']
                if i.is_ope:
                    i.sens_element = self.sens[i.obj['type']]  # depense recette ou virement
                    i.cat = i.obj['category']
                    i.automatique = False  # ameliorer la gestion du truc
                    i.cpt = i.obj['payment']
                    i.date = i.obj['day']
                    if i.sens_element == 'r':
                        i.montant = decimal.Decimal(i.obj['amount'])
                    else:
                        i.montant = decimal.Decimal(i.obj['amount']) * -1
                    try:
                        i.tiers = i.obj['memo']['NS.string']
                    except TypeError:
                        i.tiers = i.obj['memo']
                if i.is_cat or i.is_compte:
                    i.couleur = "#%s" % format(i.obj['color'], '06X')
                    try:
                        i.nom = i.obj['name']['NS.string']
                    except TypeError:
                        i.nom = i.obj['name']
                    i.place = i.obj['place']
                if i.is_cat:
                    i.type_cat = self.sens[i.obj['type']]
                if i.is_compte:
                    i.symbol = i.obj['symbol']
                self.list_el.append(i)


def gestion_maj(request):
    """vue qui gere les maj"""
    messages.set_level(request, messages.INFO)
    try:
        with transaction.atomic():
            config = models.Config.objects.get_or_create(id=1, defaults={'id': 1})[0]
            lastmaj = config.derniere_import_money_journal
            if lastmaj.tzinfo is None:
                lastmaj = tz.make_aware(lastmaj, timezone=tz.utc)
            messages.info(request, "dernière mise à jour: %s" % tz.localtime(lastmaj))
            messages.info(request, "From PC to iphone")
            nb_export = export(lastmaj, request)
            if int(nb_export['ope']) > 0:
                messages.success(request, "opérations exportées: %s" % nb_export['ope'])
            if nb_export['compte'] > 0:
                messages.success(request, "comptes exportés: %s" % nb_export['compte'])
            if nb_export['cat'] > 0:
                messages.success(request, "catégories exportées: %s" % nb_export['cat'])
            if int(nb_export['ope']) == 0 and nb_export['compte'] == 0 and nb_export['cat'] == 0:
                messages.success(request, "Rien d'exporté")
            messages.info(request, "From iphone to PC")
            nb_import = import_items(lastmaj, request)
            if int(nb_import['ope']) > 0:
                messages.success(request, "opérations importées: %s" % nb_import['ope'])
            if nb_import['compte'] > 0:
                messages.success(request, "comptes importés: %s" % nb_import['compte'])
            if nb_import['cat'] > 0:
                messages.success(request, "catégories importées: %s" % nb_import['cat'])
            if int(nb_import['ope']) == 0 and nb_import['compte'] == 0 and nb_import['cat'] == 0:
                messages.success(request, "Rien d'importé")
            if nb_import["deja"] > 0:
                messages.info(request, "%s éléments du répertoire money journal déja mises à jour" % nb_import['deja'])
            #on gere ceux qu'on elimine car deja pris en en compte

            config.derniere_import_money_journal = utils.now()
            config.save()

    except Lecture_plist_exception as exc:
        messages.error(request, exc.msg)
    return render_to_response('generic.djhtm', {'titre': 'intégration des maj recues', }, context_instance=RequestContext(request))


def simp_nskeyedarchiver(top, objects, level, filtre=False):
    """fonction recursive de simplification des plist
    @param top: niveau a partir duquel on part a cette recursion
    @param objects: object plist initial
    level: level of recursivite
    obj: object plist final"""
    __tab = None
    if isinstance(top, dict):  # dico
        __tab = {}
        if "CF$UID" in top and len(top) == 1:
            return simp_nskeyedarchiver(objects['$objects'][top["CF$UID"]], objects, level + 1, filtre)
        for cle, element in list(top.items()):
            if cle == "$class" and filtre:
                temp = objects['$objects'][element['CF$UID']]['$classname']
            elif cle == "CF$UID":
                temp = objects['$objects'][element['CF$UID']]
            else:
                temp = element
            if hasattr(temp, '__iter__'):  # c'est soir une liste soit un dict
                temp = simp_nskeyedarchiver(temp, objects, level + 1, filtre)
            if isinstance(temp, dict) and "$class" in temp and temp["$class"] == "Day":
                temp = datetime.date(temp['year'], temp['month'], temp['day'])
            if temp == "$null":
                temp = ''
            __tab[cle] = temp
        return __tab
    if isinstance(__tab, list):  # list
        __tab = list()
        for element in __tab:
            __tab.append(simp_nskeyedarchiver(element, objects, level + 1))
        return __tab
    if __tab is None:
        __tab = top
    return __tab


def check():
    """verifie si des nouvelles opes ont arrives
    renvoi true or false"""
    config = models.Config.objects.get_or_create(id=1, defaults={'id': 1})[0]
    lastmaj = config.derniere_import_money_journal
    #verif si des operations sont a importer
    for fichier in utils.find_files(os.path.join(settings.DIR_DROPBOX, 'Applications', 'Money Journal', 'log')):
        datas = collection_datas_decodes(fichier)
        for el in datas.list_el:
            if el.device == 'tototototo':  # c'est une operation provenant de ce pc
                continue
            if el.lastup > lastmaj and el.sens_element != "d":
                return True
            if datas.datemaj > lastmaj and el.sens_element == "d":
                return True
    #verif si des operations sont a exporter
    if models.Ope.objects.filter(lastupdate__gte=lastmaj).order_by('lastupdate').count() > 0:
        return True
    return False


def import_items(lastmaj, request=None):
    nb = collections.Counter()
    decimal.getcontext().prec = 6
    list_ele = dict()
    list_ele['ope'] = dict()
    list_ele['compte'] = dict()
    list_ele['categorie'] = dict()
    list_ele['budget'] = dict()
    #on parcourt les fichier
    for fichier in utils.find_files(os.path.join(settings.DIR_DROPBOX, 'Applications', 'Money Journal', 'log')):
        datas = collection_datas_decodes(fichier)
        if datas.device == settings.CODE_DEVICE_POCKET_MONEY:  # c'est une operation provenant de ce pc
            nb['deja'] += 1
            continue
        for el in datas.list_el:
            if el.lastup < lastmaj:
                nb['deja'] += 1
                continue
            if hasattr(el, 'date'):
                if el.date > utils.today():
                    continue
            if el.action == 'c':
                nb[el.classe] += 1
                list_ele[el.classe][el.id] = el
            if el.action == "m":  # modif
                if el.id in list(list_ele[el.classe].keys()):
                    if list_ele[el.classe][el.id].action == 'c':
                        list_ele[el.classe][el.id] = el
                        list_ele[el.classe][el.id].action = 'c'
                    else:
                        list_ele[el.classe][el.id] = el
                else:
                    nb[el.classe] += 1
                    list_ele[el.classe][el.id] = el
            if el.action == "d":
                if el.id in list(list_ele[el.classe].keys()):
                    if list_ele[el.classe][el.id].action == 'c':
                        del list_ele[el.classe][el.id]
                        nb[el.classe] -= 1
                    else:
                        list_ele[el.classe][el.id].action = "d"
                else:
                    nb[el.classe] += 1
                    list_ele[el.classe][el.id] = el

    for element_unitaire in list(list_ele['categorie'].values()):
        ref = element_unitaire.__str__()
        diff = dict()
        texte = ""
        messages.info(request, "gestion du fichier %s" % element_unitaire.fichier)
        if element_unitaire.action == 'c':
            if not models.Cat.objects.filter(id=element_unitaire.id).exists():
                models.Cat.objects.create(
                    pk=element_unitaire.id,
                    nom=element_unitaire.nom,
                    type=element_unitaire.type_cat,
                    couleur=element_unitaire.couleur)
                messages.success(request, "catégorie %s créée" % ref)
            else:
                raise Lecture_plist_exception("attention la catégorie %s existe déja alors qu'on demande de la créer" % ref)
        if element_unitaire.action == "m":  # modif
            try:
                cat = models.Cat.objects.get(id=element_unitaire.id)
            except models.Cat.DoesNotExist:
                raise Lecture_plist_exception("attention la catégorie %s n'existe pas alors qu'on demande de la modifier" % ref)
            if not cat.is_editable and (cat.type != element_unitaire.type_cat or cat.nom != element_unitaire.nom):
                messages.error(request, "impossible de modifier la cat %s" % ref)
                continue
            if cat.nom != element_unitaire.nom:
                diff['nom'] = "nom: %s => %s" % (cat.nom, element_unitaire.nom)
                cat.nom = element_unitaire.nom
                texte = diff['nom']
            cat.lastupdate = element_unitaire.lastup
            if cat.couleur != element_unitaire.couleur:
                diff['couleur'] = "couleur: %s => %s" % (cat.couleur, element_unitaire.couleur)
                cat.couleur = element_unitaire.couleur
                texte = "%s, %s" % (texte, diff['couleur'])
            if cat.type != element_unitaire.type_cat:
                diff['type'] = "type: %s => %s" % (cat.type, element_unitaire.type_cat)
                cat.type = element_unitaire.type_cat
                texte = "%s, %s" % (texte, diff['type'])
            if diff != dict():
                if texte[0] == ",":
                    texte = texte[2:]
                cat.save()
                messages.success(request, "catégorie %s modifiée comme ca: %s" % (ref, texte))
        if element_unitaire.action == 'd':
            # on regarde si la cat existe
            try:
                gsb = models.Cat.objects.get(id=element_unitaire.id, nom=element_unitaire.nom)
            except models.Cat.DoesNotExist:
                raise Lecture_plist_exception("attention la catégorie %s n'existe pas alors qu'on demande de la supprimer" % ref)
            # on regarde si la cat a des opes
            if (models.Echeance.objects.filter(cat=gsb).count() + models.Ope.objects.filter(cat=gsb).count()) > 0:
                raise Lecture_plist_exception("catégorie non supprimable %s car elle a des opérations rattachées" % ref)
            # on regarde si la cat ne fait partie des cat reserves
            if not gsb.is_editable:
                raise Lecture_plist_exception("impossible de supprimer la catégorie (%s)" % gsb.id)
            texte = "catégorie (%s) #%s supprimée" % (gsb.nom, gsb.pk)
            gsb.delete()
            messages.success(request, texte)

    for element_unitaire in list(list_ele['compte'].values()):
        ref = element_unitaire.__str__()
        messages.info(request, "gestion du fichier %s" % element_unitaire.fichier)
        diff = dict()
        texte = ""
        if element_unitaire.action == 'c':
            if not models.Compte.objects.filter(id=element_unitaire.id).exists():
                models.Compte.objects.create(
                    pk=element_unitaire.id,
                    nom=element_unitaire.nom,
                    couleur=element_unitaire.couleur)
                messages.success(request, "compte %s créé" % ref)
            else:
                raise Lecture_plist_exception("attention le compte %s existe déja alors qu'on demande de le créer" % ref)
        if element_unitaire.action == "m":  # modif
            # on regarde si l'opération existe
            try:
                gsb = models.Compte.objects.get(id=element_unitaire.id)
            except models.Compte.DoesNotExist:
                raise Lecture_plist_exception("attention le compte %s n'existe pas alors qu'on demande de le modifier" % ref)
            if gsb.nom != element_unitaire.nom:
                diff['nom'] = "nom: %s => %s" % (gsb.nom, element_unitaire.nom)
                gsb.nom = element_unitaire.nom
                texte = diff['nom']
            gsb.lastupdate = element_unitaire.lastup
            if gsb.couleur != element_unitaire.couleur:
                diff['couleur'] = "couleur: %s => %s" % (gsb.couleur, element_unitaire.couleur)
                gsb.couleur = element_unitaire.couleur
                texte = "%s, %s" % (texte, diff['couleur'])
            if diff != dict():
                if texte[0] == ",":
                    texte = texte[2:]
                gsb.save()
                messages.success(request, "compte %s modifié comme ca: %s" % (ref, texte))
        if element_unitaire.action == 'd':
            # on regarde si le cpt existe
            try:
                gsb = models.Compte.objects.get(id=element_unitaire.id, nom=element_unitaire.nom)
            except models.Compte.DoesNotExist:
                raise Lecture_plist_exception(
                    "attention le compte %s n'existe pas pour ce nom (%s) alors qu'on demande de le supprimer" % (element_unitaire.id, element_unitaire.nom))
            # on regarde si le cpt a des opes
            if sum((models.Echeance.objects.filter(compte=gsb).count(),
                    models.Echeance.objects.filter(compte_virement=gsb).count(),
                    models.Ope.objects.filter(compte=gsb).count())) > 0:
                raise Lecture_plist_exception("compte non supprimable %s car il a des opérations ou des écheances rattachées" % ref)
            texte = "compte %s supprimé" % ref
            gsb.delete()
            messages.success(request, texte)

    for element_unitaire in list(list_ele['ope'].values()):
        ref = element_unitaire.__str__()
        messages.debug(request, "gestion du fichier %s" % element_unitaire.fichier)
        texte = ""
        if element_unitaire.cpt in list_ele['compte'] and list_ele['compte'][element_unitaire.cpt].action == 'c':
            compte = element_unitaire.cpt
        else:
            try:
                compte = models.Compte.objects.get(id=element_unitaire.cpt).id
            except models.Compte.DoesNotExist:
                raise Lecture_plist_exception(
                    "attention le compte (%s) n'existe pas alors qu'on le demande pour l'opération %s" % (element_unitaire.cpt, ref))
        if element_unitaire.cat in list_ele['categorie'] and list_ele['categorie'][element_unitaire.cat].action == 'c':
            cat = element_unitaire.cat
        else:
            try:
                cat = models.Cat.objects.get(id=element_unitaire.cat).id
            except models.Cat.DoesNotExist:
                raise Lecture_plist_exception(
                    "attention la catégorie (%s) n'existe pas alors qu'on le demande pour l'opération %s" % (element_unitaire.cat, ref))
        tiers, created = models.Tiers.objects.get_or_create(nom=element_unitaire.tiers, defaults={'nom': element_unitaire.tiers})
        if created:
            messages.success(request, "tiers '%s' créé" % tiers)
        if element_unitaire.action == 'c':
            if not models.Ope.objects.filter(id=element_unitaire.id).exists():
                models.Ope.objects.create(
                    pk=element_unitaire.id,
                    compte_id=compte,
                    cat_id=cat,
                    date=element_unitaire.date,
                    tiers=tiers,
                    montant=element_unitaire.montant,
                    lastupdate=element_unitaire.lastup
                )
                messages.debug(request, "opération %s créée" % ref)
            else:
                mesage = "attention l'opération %s existe déja alors qu'on demande de la créer" % ref
                raise Lecture_plist_exception(mesage)

        if element_unitaire.action == "m":  # modif
            try:
                gsb = models.Ope.objects.get(id=element_unitaire.id)
            except models.Ope.DoesNotExist:
                raise Lecture_plist_exception("attention cette opération %s n'existe pas alors qu'on demande de la modifier" % ref)
            if gsb.is_mere:
                messages.error(request, "impossible de modifier cette opération %s car elle est mère" % ref)
                continue
            if gsb.is_fille:
                messages.error(request, "impossible de modifier cette opération %s car elle est fille" % ref)
                continue
            if gsb.rapp is not None:
                messages.error(request, "impossible de modifier cette opération %s car elle est rapprochée" % ref)
                continue
            if gsb.compte.ouvert is False:
                messages.error(request, "impossible de modifier cette opération %s car son compte est fermé" % ref)
                continue
            if gsb.jumelle:
                messages.error(request, "impossible de modifier cette opération %s car elle est jumellée" % ref)
                continue
            if gsb.ope_titre_ost is not None or gsb.ope_titre_pmv is not None:  # pragma: no cover because trop chiant a tester
                messages.error(request, "impossible de modifier cette opération %s car elle est support d'une opération titre" % ref)
                continue
            if gsb.pointe:
                messages.error(request, "impossible de modifier cette opération %s car elle est pointée" % ref)
                continue
            if gsb.compte_id != compte:
                texte = "compte: %s => %s\n" % (gsb.compte_id, compte)
                gsb.compte_id = compte
            if gsb.cat_id != cat:
                texte = "%s, cat: %s => %s\n" % (texte, gsb.cat_id, cat)
                gsb.cat_id = cat
            if gsb.date != element_unitaire.date:
                texte = "%s, date: %s => %s\n" % (texte, gsb.date, element_unitaire.date)
                gsb.date = element_unitaire.date
            if gsb.montant != element_unitaire.montant:
                texte = "%s, montant: %s => %s\n" % (texte, gsb.montant, element_unitaire.montant)
                gsb.montant = element_unitaire.montant
            if gsb.tiers != tiers:
                texte = "%s, tiers: %s => %s\n" % (texte, gsb.tiers, tiers)
                gsb.tiers = tiers
            if texte != "":
                gsb.save()
                if texte[0] == ",":
                    texte = texte[2:]
                if texte[-1] == "\n":
                    texte = texte[:-1]
                #messages.success(request, u"opération (%s) modifiée comme ca: %s" % (gsb.id, texte))
        if element_unitaire.action == 'd':
            try:
                gsb = models.Ope.objects.get(id=element_unitaire.id)
            except models.Ope.DoesNotExist:
                raise Lecture_plist_exception("attention cette opération %s n'existe pas alors qu'on demande de la supprimer" % element_unitaire.id)
            if gsb.is_mere:
                raise Lecture_plist_exception("impossible de supprimer cette opération %s car elle est mère" % ref)
            if gsb.is_fille:
                raise Lecture_plist_exception("impossible de supprimer cette opération %s car elle est fille" % ref)
            if gsb.rapp is not None:
                raise Lecture_plist_exception("impossible de supprimer cette opération %s car elle est rapprochée" % ref)
            if gsb.compte.ouvert is False:
                raise Lecture_plist_exception("impossible de supprimer cette opération %s car son compte est fermé" % ref)
            if gsb.jumelle:
                raise Lecture_plist_exception("impossible de supprimer cette opération %s car elle est jumellée" % ref)
            if gsb.ope_titre_ost is not None or gsb.ope_titre_pmv is not None:
                raise Lecture_plist_exception(
                    "impossible de supprimer cette opération %s car elle est support d'une opération titre" % ref)
            if gsb.pointe:
                raise Lecture_plist_exception("impossible de supprimer cette opération %s car elle est pointée" % ref)
            if gsb.compte_id != element_unitaire.cpt or gsb.date != element_unitaire.date or gsb.montant != element_unitaire.montant or gsb.tiers.nom != element_unitaire.tiers or gsb.cat_id != element_unitaire.cat:
                diff = ""
                for d, value in zip(((gsb.compte_id, element_unitaire.cpt), (gsb.date, element_unitaire.date), (gsb.montant, element_unitaire.montant), (gsb.tiers.nom, element_unitaire.tiers),
                                     (gsb.cat_id, element_unitaire.cat)), ('CPT', 'DATE', 'montant', 'tiers', 'cat')):
                    if d[0] != d[1]:
                        diff = "%s\n%s" % (diff, "%s:\t%s!= %s" % (value, d[0], d[1]))
                raise Lecture_plist_exception("attention cette opération %s existe alors qu'on demande de la supprimer mais elle est différente :%s" % (element_unitaire.id, diff))
            texte = "opération %s supprimée" % ref
            gsb.delete()
            messages.success(request, texte)
    return nb


def export(lastmaj, request):
    with transaction.atomic():
        export_cls = Export_icompta_plist(request=request)
        nb = export_cls.all_since_date(lastmaj)
    return nb
