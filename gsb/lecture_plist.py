# -*- coding: utf-8 -*-
import plistlib
import os
import datetime
import decimal
import time
import pytz
from django.db import transaction
from django.conf import settings
import django.utils
import calendar
from . import models
from . import utils

#gestion des vues
from django.contrib import messages
from django.shortcuts import render_to_response
from django.template import RequestContext
import pprint
from django.utils.encoding import smart_unicode


class Log_factory(object):
    def __init__(self, request=None, debug=False, pprint_flag=False):
        self.debug = True if debug else False
        self.request = request
        self.pprint = True if pprint_flag else False
        self.toolbar = True if settings.DJANGO_TOOLBAR else False

    def log(self, text):
        text = smart_unicode(text)
        if self.request:
            if self.debug:
                if not self.toolbar:
                    if self.pprint:
                        messages.info(self.request, u"<PRE>%s</PRE>" % pprint.pformat(text))
                    else:
                        messages.info(self.request, u"%s" % text)
                else:
                    debug(text, console=False)
            else:
                if not self.toolbar:
                    messages.info(self.request, u"%s" % text)
                else:
                    debug(text, console=False)
        else:
            if self.pprint:
                pprint.pprint(u"%s" % text)
            else:
                print u"%s" % text


def gestion_maj(request):
    """vue qui gere les maj"""
    with transaction.atomic():
        config = models.config.objects.get_or_create(id=1, defaults={'id': 1})[0]
        lastmaj = config.derniere_import_money_journal
        nb_export = export(lastmaj, request)
        retour = import_items(lastmaj, request)
        #on gere ceux qu'on elimine car deja pris en en compte
        config.derniere_import_money_journal = utils.now()
        config.save()
    messages.success(request,
                     "{nb_ajout} opérations ajoutés,{nb_modif} opérations modifiés, {nb_suppr} opérations supprimés".format(**retour))
    messages.success(request, "%s opérations crées ou modifiés vers iphones" % nb_export)
    return render_to_response('generic.djhtm', {'titre': u'integration des maj recues', },
                              context_instance=RequestContext(request))


# noinspection PyTypeChecker
def affiche_plist(request):
    reponses = []
    decimal.getcontext().prec = 6
    for fichier in utils.find_files(os.walk(os.path.join(settings.DIR_DROPBOX, 'Applications', 'Money Journal', 'log')), "*.log"):
        plistdict = plistlib.readPlist(fichier)
        objects = plistdict['$objects']
        liste_obj = objects[plistdict['$top']['$0']['CF$UID']]
        #on transforme en un truc lisible
        reponse = simplification(liste_obj, objects, 1)
        datemaj = datetime.datetime.utcfromtimestamp(int(os.path.splitext(os.path.basename(fichier))[0]) / 1000)
        typeaction = ['ajout', 'modif', 'delete']
        data = {'action': typeaction[reponse['action'] - 1],
                'device': reponse['device'],
                'objet': reponse['object0']}
        type_obj = data['objet']["$class"]["$classname"]
        ensemble_obj = Objets()
        obj = getattr(ensemble_obj, type_obj.lower())(data['objet'])
        if len(reponse) > 4:
            for k, v in reponse.items():
                if k not in ('action', 'device', 'class', '$class'):
                    data['k'] = v
            messages.info(request, "attention plus d'un objet")
        reponses.append({'filename': os.path.realpath(fichier),
                         'date': datemaj.strftime('%d/%m/%Y %H:%M:%S'),
                         'data_plist': data,
                         'data_gsb': obj})
    return render_to_response('gsb/plist.djhtm', {'titre': 'lecture pliste', 'reponses': reponses},
                                    context_instance=RequestContext(request))


class Objets(object):
    def record(self, obj):
        if obj['type'] == 1:#recette
            retour = {'montant': decimal.Decimal(obj['amount'])}
        else:
            retour = {'montant': decimal.Decimal(obj['amount'])*-1}
        try:
            retour['tiers'] = obj['memo']['NS.string']
        except TypeError:
            retour['tiers'] = obj['memo']
            if retour['tiers'] == "":
                retour['tiers'] = "inconnu"
        retour['tiers'] = models.Tiers.objects.get_or_create(nom=retour['tiers'], defaults={'nom': retour['tiers']})[0]
        retour['date'] = datetime.date(obj['day']['year'], obj['day']['month'], obj['day']['day'])
        retour['id'] = obj['pk']
        retour['compte_id'] = obj['payment']
        retour['cat'] = models.Cat.objects.get(id=obj['category'])
        retour['lastupdate'] = datetime.datetime.fromtimestamp(obj['lastUpdate'])
        return retour

    def payment(self, obj):
        retour = {'couleur': obj['color'],
                  'lastupdate': datetime.datetime.fromtimestamp(obj['lastUpdate']),
                  'nom': obj['name'],
                  'id': obj['pk']}
        return retour

    def category(self, obj):
        retour = {'couleur': obj['color'],
                  'lastupdate': datetime.datetime.fromtimestamp(obj['lastUpdate']),
                  'nom': obj['name'],
                  'id': obj['pk'], 'type': ('revenu', 'depense')[obj['pk'] - 1]}
        return retour


class Lecture_plist_exception(Exception):
    pass


def simplification(obj, objects, level):
    """fonction recursive de simplification des plist"""
    if isinstance(obj, dict):  # dico
        tab = {}
        if "CF$UID" in obj and len(obj) == 1:
            return simplification(objects[obj["CF$UID"]], objects, level + 1)
        for key in obj.keys():
            if key == "CF$UID":
                temp = objects[obj[key]]
            else:
                temp = obj[key]
            if hasattr(temp, '__iter__'):
                temp = simplification(temp, objects, level + 1)
            tab[key] = temp
        return tab
    if isinstance(obj, list):  # list
        tab = list()
        for item in obj:
            tab.append(simplification(item, objects, level + 1))
        return tab
    return obj


def check():
    config = models.config.objects.get_or_create(id=1, defaults={'id': 1})[0]
    lastmaj = config.derniere_import_money_journal
    for fichier in utils.find_files(os.walk(os.path.join(settings.DIR_DROPBOX, 'Applications', 'Money Journal', 'log'))):
        datemaj = pytz.utc.localize(datetime.datetime.utcfromtimestamp(int(os.path.splitext(os.path.basename(fichier))[0]) / 1000))
        plistdict = plistlib.readPlist(fichier)
        objects = plistdict['$objects']
        liste_obj = objects[plistdict['$top']['$0']['CF$UID']]
        #on transforme en un truc lisible
        reponse = simplification(liste_obj, objects, 1)
        if reponse['device'] == 'tototototo':#c'est une operation provenant de ce pc
            continue
        else:
            del reponse['device']
        if reponse['action'] not in (1, 2, 3):
            raise IndexError(reponse['action'])
        del reponse['action']
        del reponse['$class']
        for key in reponse:
            obj = reponse[key]
            type_enr = obj['$class']['$classname']
            lastup = pytz.utc.localize(datetime.datetime.utcfromtimestamp(obj['lastUpdate'])) if obj['lastUpdate'] != 0 else datemaj
            if lastup > lastmaj:
                if type_enr in ('Record',):
                    return True
                if type_enr not in ('Payment', 'Category', 'Budget'):
                    raise Lecture_plist_exception("attention un type inconnu: %s" % type_enr)
    if models.Ope.objects.filter(lastupdate__gte=lastmaj).order_by('lastupdate').count() > 0:
        return True
    return False


def import_items(lastmaj, request=None, dry=False):
    nb_deja = 0
    nb_ajout = 0
    nb_suppr = 0
    nb_modif = 0
    decimal.getcontext().prec = 6
    log = Log_factory(request)
    ensemble_obj = Objets()
    with transaction.atomic():
        for fichier in utils.find_files(os.walk(os.path.join(settings.DIR_DROPBOX, 'Applications', 'Money Journal', 'log'))):
            log.log("%s\n%s" % ('fichier', fichier))
            datemaj = pytz.utc.localize(datetime.datetime.utcfromtimestamp(int(os.path.splitext(os.path.basename(fichier))[0]) / 1000))
            plistdict = plistlib.readPlist(fichier)
            objects = plistdict['$objects']
            liste_obj = objects[plistdict['$top']['$0']['CF$UID']]
            #on transforme en un truc lisible
            reponse = simplification(liste_obj, objects, 1)
            del reponse['$class']
            if reponse['device'] == 'totototo': #c'est une operation provenant de ce pc
                continue
            else:
                del reponse['device']
            if reponse['action'] == 1:
                type_action = "ajout"
            elif reponse['action'] == 2:
                type_action = "modif"
            elif reponse['action'] == 3:
                type_action = "delete"
            else:
                raise IndexError(reponse['action'])
            del reponse['action']
            for key in reponse:
                obj = reponse[key]
                type_enr = obj['$class']['$classname']
                lastup = pytz.utc.localize(datetime.datetime.utcfromtimestamp(obj['lastUpdate'])) if obj['lastUpdate'] != 0 else datemaj
                if lastup < lastmaj:
                    nb_deja += 1
                    continue
                if type_action == "ajout":
                    nb_ajout += 1
                if type_action == "modif":
                    nb_modif += 1
                if type_action == "delete":
                    nb_suppr += 1
                if type_enr == 'Record':
                    retour = ensemble_obj.record(obj)
                    if type_action == "ajout":
                        if not dry:
                            ope = models.Ope.objects.create(**retour)
                            log.log(u"operation '%s' crée" % ope)
                    elif type_action == "modif":#modif
                        opes = models.Ope.objects.filter(id=retour['id'])
                        if not bool(opes):
                            raise Lecture_plist_exception("attention l'ope %s n'existait pas alors qu'on demande de la modifier" % retour['id'])
                        ope = opes[0]
                        if not ope.is_editable or ope.jumelle:
                            log.log("operation non editable n° %s " % retour['id'])
                            continue
                        if not dry:
                            ope.montant = retour['montant']
                            ope.tiers = retour['tiers']
                            ope.date = retour['date']
                            ope.cat = retour['cat']
                            ope.compte_id = retour['compte_id']
                            ope.lastupdate = retour['lastupdate']
                            ope.save()
                        log.log(u"operation '%s' modifiée" % opes[0])
                    elif type_action == "delete":
                        try:
                            ope = models.Ope.objects.get(**retour)
                            texte = u"operation '%s' supprimée" % ope
                            if not dry:
                                ope.delete()
                            log.log(texte)
                        except models.Ope.DoesNotExist:
                            raise Lecture_plist_exception("attention, cette ope n'existe pas %s" % obj)
                elif type_enr == 'Payment':
                    raise Lecture_plist_exception('changement dans %s' % obj)
                elif type_enr == 'Category':
                    raise Lecture_plist_exception('changement dans %s' % obj)
                elif type_enr == 'Budget':
                    raise Lecture_plist_exception('changement dans %s' % obj)
                else:
                    raise Lecture_plist_exception("attention un type inconnu: %s" % type_enr)

    return {'nb_ajout': nb_ajout, 'nb_deja': nb_deja, 'nb_suppr': nb_suppr, 'nb_modif': nb_modif}


def export(lastmaj, request=None, dry=False):

    #log = Log_factory(request)
    nb = 0
    with transaction.atomic():
        for ope in models.Ope.objects.filter(lastupdate__gte=lastmaj).order_by('lastupdate'):
            nb += 1
            ref_temp = int(calendar.timegm(django.utils.timezone.now().timetuple()))
            final = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>$archiver</key>
    <string>NSKeyedArchiver</string>
    <key>$objects</key>
    <array>
        <string>$null</string>
        <dict>
            <key>$class</key>
            <dict>
                <key>CF$UID</key>
                <integer>9</integer>
            </dict>
            <key>action</key>
            <integer>{type_action}</integer>
            <key>device</key>
            <dict>
                <key>CF$UID</key>
                <integer>2</integer>
            </dict>
            <key>object0</key>
            <dict>
                <key>CF$UID</key>
                <integer>3</integer>
            </dict>
        </dict>
        <string>{device}</string>
        <dict>
            <key>$class</key>
            <dict>
                <key>CF$UID</key>
                <integer>8</integer>
            </dict>
            <key>account</key>
            <integer>0</integer>
            <key>amount</key>
            <real>{amount:f}</real>
            <key>category</key>
            <integer>{ope.cat_id}</integer>
            <key>currency</key>
            <integer>2</integer>
            <key>date</key>
            <real>0.0</real>
            <key>day</key>
            <dict>
                <key>CF$UID</key>
                <integer>4</integer>
            </dict>
            <key>lastUpdate</key>
            <real>{last_update:f}</real>
            <key>memo</key>
            <dict>
                <key>CF$UID</key>
                <integer>6</integer>
            </dict>
            <key>note</key>
            <dict>
                <key>CF$UID</key>
                <integer>0</integer>
            </dict>
            <key>payee</key>
            <dict>
                <key>CF$UID</key>
                <integer>0</integer>
            </dict>
            <key>payment</key>
            <integer>{ope.compte_id}</integer>
            <key>photo</key>
            <integer>0</integer>
            <key>pk</key>
            <integer>{ope.id}</integer>
            <key>place</key>
            <integer>0</integer>
            <key>repeat</key>
            <integer>0</integer>
            <key>type</key>
            <integer>{type_ope}</integer>
            <key>voice</key>
            <integer>0</integer>
        </dict>
        <dict>
            <key>$class</key>
            <dict>
                <key>CF$UID</key>
                <integer>5</integer>
            </dict>
            <key>day</key>
            <integer>{ope.date.day}</integer>
            <key>month</key>
            <integer>{ope.date.month}</integer>
            <key>year</key>
            <integer>{ope.date.year}</integer>
        </dict>
        <dict>
            <key>$classes</key>
            <array>
                <string>Day</string>
                <string>NSObject</string>
            </array>
            <key>$classname</key>
            <string>Day</string>
        </dict>
        <dict>
            <key>$class</key>
            <dict>
                <key>CF$UID</key>
                <integer>7</integer>
            </dict>
            <key>NS.string</key>
            <string>{ope.tiers.nom}</string>
        </dict>
        <dict>
            <key>$classes</key>
            <array>
                <string>NSMutableString</string>
                <string>NSString</string>
                <string>NSObject</string>
            </array>
            <key>$classname</key>
            <string>NSMutableString</string>
        </dict>
        <dict>
            <key>$classes</key>
            <array>
                <string>Record</string>
                <string>NSObject</string>
            </array>
            <key>$classname</key>
            <string>Record</string>
        </dict>
        <dict>
            <key>$classes</key>
            <array>
                <string>SyncData</string>
                <string>NSObject</string>
            </array>
            <key>$classname</key>
            <string>SyncData</string>
        </dict>
    </array>
    <key>$top</key>
    <dict>
        <key>$0</key>
        <dict>
            <key>CF$UID</key>
            <integer>1</integer>
        </dict>
    </dict>
    <key>$version</key>
    <integer>100000</integer>
</dict>
</plist>
""".format(device="totototo",
           amount=abs(float("{!s}".format(ope.montant))),
           type_action=1 if ope.date_created > lastmaj else 2,
           ope=ope,
           last_update=calendar.timegm(ope.lastupdate.timetuple()),
           type_ope=2 if ope.montant > 0 else 1,
            )
            directory = os.path.join(settings.DIR_DROPBOX, 'Applications', 'Money Journal', 'log', str(ref_temp)[:3], str(ref_temp)[3:4],
                                     str(ref_temp)[4:5])
            filename = os.path.join(directory, "{0:d}.log".format(ref_temp * 1000))
            if not os.path.exists(directory):
                os.makedirs(directory)
            if os.path.isfile(filename):
                time.sleep(2)
                ref_temp = calendar.timegm(django.utils.timezone.now().timetuple())
                directory = os.path.join(settings.DIR_DROPBOX, 'Applications', 'Money Journal', 'log', str(ref_temp)[:3],
                                         str(ref_temp)[3:4], str(ref_temp)[4:5])
                filename = os.path.join(directory, "{0:d}.log".format(ref_temp * 1000))
                if not os.path.exists(directory):
                    os.makedirs(directory)
            #log.log(os.path.join(filename))
            with open(os.path.join(filename), 'wb') as f:
                if not dry:
                    f.write(final)
    return nb


# noinspection PyStatementEffect
"""note sur le truc
pour le classement en repertoire:
c'est les trois premier chiffre de la datetime de maj:
    puis chiffre puis chiffre (un 100000 fais a peu pres 2 jours)



si action = 1 : creation
si action = 2 : modification
device: identifiant du truc qui a cree l'operation
prendre le classname:
    si "Payment": nom de compte
        color: RGB hex to int int("00FFFF",16)
        lastupdate: timestamp
        name: nom du compte
        pk: identifiant
        place: ordre en commencant par 0
        symbol: 0 rond, 1 carre, 2 rectangle, 3 triangle
    si "Category": categorie
        color : idem
        lastupdate: idem
        name: idem
        pk:idem
        place: idem
        type: 1 => revenu 2 => depenses
    si "Record":
        account: 0
        amount: montant
        catgorie: pk de la categorie
        currency: pk de la currency (en l'occurence 2 pour euro)
        date: 0.0
        day dict avec day, month YEAR
        lastupdate: idem
        memo: nom du tiers
        note: "$null"
        payee: "$null"
        payment: id du compte
        photo: 0
        pk: pk de l'operation
        place: 0
        repeat: 0
        type:1 => revenu 2 => depenses
        voice: 0
"""
