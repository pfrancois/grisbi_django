# coding=utf-8
import plistlib
import pprint

import os

import datetime
from django.conf import settings
from django.core.management.base import NoArgsCommand
from optparse import make_option
from gsb import utils

def print_debug(texte, debug):
    if debug:
        print texte

def simplification(obj, objects, level, debug=False):
    print_debug=  lambda x,y: pprint.pformat("%s%s" % (y,x))
    tabs = ""
    for i in range(level):
        tabs += "...."
    print_debug("%s%s" % (tabs, level), debug)
    print_debug("%sobj level %s :%s" % (tabs, level, obj), debug)
    if isinstance(obj, dict):  # dico
        print_debug(tabs + "dico", debug)
        tab = {}
        if "CF$UID" in obj and len(obj) == 1:
            return simplification(objects[obj["CF$UID"]], objects, level + 1, debug)
        for key in obj.keys():
            print_debug(tabs + key, debug)
            if key == "CF$UID":
                temp = objects[obj[key]]
            else:
                temp = obj[key]
            print_debug("%skey:%s obj:%s" % (tabs, key, temp), debug)
            if hasattr(temp, '__iter__'):
                temp = simplification(temp, objects, level + 1, debug)
            tab[key] = temp
        print_debug(tabs + "retour level %s: %s\n" % (level, tab), debug)
        return tab
    if isinstance(obj, list):  # list
        print_debug(tabs + "list", debug)
        tab = list()
        for item in obj:
            tab.append(simplification(item, objects, level + 1, debug))
        print_debug(tabs + "retour level %s: %s\n" % (level, tab), debug)
        return tab
    return obj

class Command(NoArgsCommand):
    option_list = NoArgsCommand.option_list + (
        make_option('-f','--file', action='store',dest='fichier',default='*.log',help='indiquer le fichier que voulez afficher'),
        make_option('-e','--element', action='store',dest='element',default='',help="indiquer l'element que voulez afficher"),
        make_option('-d','--device', action='store_true' ,dest='device',help="liste les iphones"),
    )

    def handle_noargs(self, **options):
        fichier = ''
        recherche = options['fichier']
        device=False
        if 'element' in options:
            element = options['element']
        else:
            element=''
        if int(options['verbosity']) > 1:
            debug = True
        else:
            debug = False
        reponses = []
        if options['device']:
            device=True
            fichier = os.path.join(settings.DIR_DROPBOX,"devices","devices.xml")
            element = "NS.objects"
        if not fichier:
            repertoire=[f for f in utils.find_files(os.path.join(settings.DIR_DROPBOX, 'Applications', 'Money Journal', 'log'),recherche=recherche)]
        else:
            repertoire=[fichier,]
        for fichier in repertoire:
            if not device:
                datemaj = datetime.datetime.utcfromtimestamp(int(os.path.splitext(os.path.basename(fichier))[0]) / 1000)
                print datemaj.strftime('%d/%m/%Y %H:%M:%S')
            plistdict = plistlib.readPlist(fichier)
            objects = plistdict['$objects']
            liste_obj = objects[plistdict['$top']['$0']['CF$UID']]
            reponse = simplification(liste_obj, objects, 1, debug)
            if element:
                reponse = reponse[element]
            reponses.append([os.path.realpath(fichier),reponse])
        pprint.pprint(reponses, width=100)

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
