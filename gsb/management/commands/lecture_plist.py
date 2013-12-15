import plistlib
import os
import datetime
import fnmatch
import decimal
import pytz
from django.core.management.base import BaseCommand
from ... import models
from ... import utils
from django.db import transaction


class lecture_plist_exception(Exception):
    pass


def lecture(path):
    plistdict = plistlib.readPlist(path)
    objects = plistdict['$objects']
    liste_obj = objects[plistdict['$top']['$0']['CF$UID']]
    plist_final = simplification(liste_obj, objects, 1)
    return plist_final


def simplification(obj, objects, level):
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


def find_files(directory, pattern):
    """trouve recursivement les fichiers voulus"""
    for root, dirs, files in os.walk(directory):
        for basename in files:
            if fnmatch.fnmatch(basename, pattern):
                filename = os.path.join(root, basename)
                yield filename


class Command(BaseCommand):
    option_list = BaseCommand.option_list

    @transaction.atomic
    def handle(self, *args, **options):
        config = models.config.objects.get_or_create(id=1, defaults={'id': 1})[0]
        lastmaj = config.derniere_import_money_journal
        nb_deja = 0
        nb_ok = 0
        for fichier in find_files('D:\Dropbox\Applications\Money Journal\log', '*.*'):
            datemaj = pytz.utc.localize(datetime.datetime.utcfromtimestamp(int(os.path.splitext(os.path.basename(fichier))[0])/1000))
            print datemaj
            reponse = lecture(fichier)
            del reponse['$class']
            if reponse['device'] == 'tototototo':#c'est une operation provenant de ce pc
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
            with transaction.atomic():
                for key in reponse:
                    obj = reponse[key]
                    type_enr = obj['$class']['$classname']
                    lastup = obj['lastUpdate'] if obj['lastUpdate'] != 0 else datemaj
                    try:
                        lastup = pytz.utc.localize(lastup)
                    except ValueError:
                        pass
                    if lastup < lastmaj:
                        nb_deja += 1
                        continue
                    if type_enr == 'Record':
                        self.record(obj, lastup, type_action)
                    elif type_enr == 'Payment':
                        pass
                    elif type_enr == 'Category':
                        pass
                    elif type_enr == 'Budget':
                        pass
                    else:
                        raise lecture_plist_exception("attention un type inconnu: %s" % type_enr)
                    nb_ok += 1
                #on gere ceux qu'on elimine car deja pris en en compte
                config.derniere_import_money_journal = utils.now()
                config.save()

    def Record(obj, datemaj, type_action):
        #on recupere les donnees de l'ope
        if obj['type'] == 1:#ajout
            montant = decimal.Decimal(round(float(obj['amount']), 2))
        else:
            montant = decimal.Decimal(round(float(obj['amount']), 2)) * -1
        if type_action == "ajout":
            models.Ope.objects.create(id=obj['pk'],
                                            compte_id=obj['payment'],
                                            date=datetime.date(obj['day']['year'], obj['day']['month'], obj['day']['day']),
                                            montant=montant,
                                            tiers=models.tiers.objects.get_or_create(nom=obj['memo'], defaults={'nom': obj['memo']}),
                                            cat_id=obj['category'])
        elif type_action == "modif":#modif
            try:
                ope = models.Ope.objects.get(id=obj['pk'])
            except models.Ope.DoesNotExist:
                print "attention l'ope %s n'existait pas alors qu'on demande de la modifier" % obj['pk']
                ope = models.Ope(id=obj['pk'])
            ope.compte_id = obj['payment']
            ope.date = datetime.date(obj['day']['year'], obj['day']['month'], obj['day']['day'])
            ope.montant = montant
            ope.tiers = models.tiers.objects.get_or_create(nom=obj['memo'], defaults={'nom': obj['memo']})
            ope.cat_id = obj['category']
            ope.save()
        elif type_action == "delete":
            try:
                ope = models.Ope.objects.get(id=obj['pk'],
                                            compte_id=obj['payment'],
                                            date=datetime.date(obj['day']['year'], obj['day']['month'], obj['day']['day']),
                                            montant=montant,
                                            tiers=models.tiers.objects.get_or_create(nom=obj['memo'], defaults={'nom': obj['memo']}),
                                            cat_id=obj['category'])
                ope.delete()
            except models.Ope.DoesNotExist:
                raise lecture_plist_exception("attention, cette ope n'existe pas %s" % obj)
