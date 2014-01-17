# -*- coding: utf-8 -*-
from __future__ import absolute_import

from __future__ import absolute_import
import plistlib
import os
import datetime
import time
import fnmatch
import decimal
from django.core.management.base import BaseCommand
from ... import models
from ... import utils
from django.db import transaction
from django.conf import settings
from django.template import Context, Template, loader

        # on export les fichier dans un enroit temporaire

        # on importe les nouveaux

        # on copie les fichiers dans dropbox


class lecture_plist_exception(Exception):
    pass


def lecture(path):
    plistdict = plistlib.readPlist(path)
    objects = plistdict['$objects']
    liste_obj = objects[plistdict['$top']['$0']['CF$UID']]
    plist_final = simplification(liste_obj, objects, 1)
    return plist_final


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
        """fonction principale de la commande manage"""
        config = models.config.objects.get_or_create(id=1, defaults={'id': 1})[0]
        last_import = config.derniere_import_money_journal
        nb_deja = 0
        nb_ok = 0
        template = loader.get_template('export_xml/operation.xml')
        import pprint
        for ope in models.Ope.objects.filter(lastupdate__gte=last_import).select_related('cat').order_by('id'):
            time.sleep(0.05)
            if ope.date < ope.date_created.date():
                action = 2  # modification
            else:
                action = 1  # creation
            context = {"montant": abs(float(str(ope.montant))),
                      "cat_id": utils.nulltostr(ope.cat.id),
                      "last_update": time.mktime(ope.lastupdate.timetuple()),
                      "compte_id": ope.compte_id,
                      "pk_id": ope.id,
                      "date_ope": ope.date,
                      "action": action,
                      "type_id": 1 if ope.montant > 0 else 0,
                      "memo": ope.tiers
            }

            if ope.cat.nom in ('Virement', u"Opération Ventilée"):
                context['montant'] = 0
            xml = template.render(Context(context))
            nomfich = "%s" % int(time.time() * 1000)
            # path=os.path.join(settings.DIR_DROPBOX,nomfich[0:3],nomfich[4],nomfich[5])
            path = os.path.join("c:\\temp", nomfich[0:3], nomfich[4], nomfich[5])
            if not os.path.exists(path):
                os.makedirs(path)
            with open(os.path.join(path, "%s.log" % nomfich), "wb") as temp:
                try:
                    temp.write(xml)
                except UnicodeEncodeError:
                    temp.write(xml.encode("iso-8859-15", "xmlcharrefreplace"))
                    pprint.pprint(context)
                    raise
                self.stdout.write("%s" % ope.id)
        self.stdout.write("%s operation ecrites" % models.Ope.objects.filter(lastupdate__gte=last_import).select_related('cat').count())
        # lire les donnees
