# -*- coding: utf-8 -*-
from __future__ import absolute_import
import csv, cStringIO, codecs, sys, datetime, time, os

from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.core import exceptions as django_exceptions
from django.db import models as models_agg
from django import forms
from django.conf import settings #@Reimport
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist
from django.utils.decorators import method_decorator

from gsb.utils import UTF8Recoder, Excel_csv
from .models import (Tiers, Titre, Cat, Ope, Banque, Ib,
                     Exercice, Rapp, Moyen, Echeance, Compte, Compte_titre, Ope_titre)
from . import forms as gsb_forms
from . import import_base
from .views import Mytemplateview
from . import utils

class Csv_unicode_reader(object):
    """
    A CSV reader which will iterate over lines in the CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, fich, dialect=csv.excel, encoding="utf-8", **kwds):# pylint: disable=W0231
        self.line_num = 0
        fich = UTF8Recoder(fich, encoding)
        self.reader = csv.DictReader(fich, dialect=dialect, **kwds)

    def next(self):
        self.line_num += 1
        self.row = self.reader.next()
        return self
    def __iter__(self):
        return self
    def vide(self, var, retour=None):
        if var == "" or var == 0:
            return retour
        else:
            return var

class Csv_unicode_reader_ope_base(import_base.property_ope_base, Csv_unicode_reader):
    @property
    def ligne(self):
        return self.line_num

class Csv_unicode_reader_ope(Csv_unicode_reader_ope_base):
    @property
    def cat(self):
        return self.vide(self.row['Category'])
    @property
    def cpt(self):
        return self.row['Account']
    @property
    def date(self):
        date_s = self.row['Date']
        return datetime.date(*time.strptime(date_s, "%d/%m/%y")[0:3])
    @property
    def ib(self):
        return self.vide(self.row['Class'])
    @property
    def mt(self):
        return utils.fr2decimal(self.row['Amount'])
    @property
    def notes(self):
        return self.vide(self.row['Memo'],'')
    @property
    def num_cheque(self):
        return self.vide(self.row['ChkNum'],'')
    @property
    def pointe(self):
        if self.row['Cleared'] == "*":
            return True
        else:
            return False
    @property
    def tiers(self):
        return self.vide(self.row['Payee'])
    @property
    def monnaie(self):
        return self.row['CurrencyCode']




class Import_csv_ope(import_base.Import_base):
    reader = Csv_unicode_reader_ope
    extension = ("csv",)
    type_f = "csv_version_pocketmoney"
    remplacement = False
    creation_exo = False
    def tableau_import(self, nomfich):
        """renvoi un tableau complet de l'import"""
        with open(nomfich, 'rt') as f_non_encode:
            opes = list()
            fich = self.reader(f_non_encode, encoding="iso-8859-1")
            for row in fich:
                ope = dict()
                #verification pour les lignes
                if row.monnaie != settings.DEVISE_GENERALE:
                    raise import_base.Import_exception(u"attention ce ne sera pas possible d'importer car il y a plusieurs devises")
                #id ope
                odb = Ope.objects.filter(pk=row.pk)
                if odb.exists() and self.remplacement==False:
                    raise import_base.Import_exception(u"attention un id d'ope existe deja")
                else:
                    ope['pk'] = row.pk
                #compte
                try:
                    ope['compte_id'] = self.listes['cpt'][row.cpt]
                except KeyError:
                    try:
                        cpt = Compte.objects.get(nom=row.cpt)
                        ope['compte_id'] = cpt.id
                    except Compte.DoesNotExist :
                        liste_compte = "'"
                        for cpt in Compte.objects.all():
                            liste_compte = "%s%s," % (liste_compte, cpt.nom)
                        liste_compte = "%s%s," % (liste_compte, "'")
                        raise import_base.Import_exception("attention, le compte %s est demande a la ligne %s alors qu'il n'existe pas, les comptes sont %s"%(row.cpt, row.line_num, liste_compte))
                #cat
                type_cat = 'd' if row.mt < 0 else 'r'
                if row.jumelle is not None:
                    type_cat = 'v'
                ope['cat_id'] = self.element('cat', row.cat, Cat, {'nom':row.cat, 'type':type_cat})
                #tiers
                ope['tiers_id'] = self.element('tiers', row.tiers, Tiers, {'nom':row.tiers, 'notes':"", 'is_titre':False})
                #date
                ope['date'] = row.date
                #auto
                ope['automatique'] = row.automatique
                #date_val
                ope['date_val'] = row.date_val
                #exercice
                if row.exercice is None and self.creation_exo == True:
                    d = row.date
                    q = Exercice.objects.filter(date_debut__lte=d, date_fin__gte=d)
                    if q.exists():
                        exo = q[0]
                    else:
                        #on cree un exercice d'un an
                        date_debut = datetime.date(d.year, 1, 1)
                        date_fin = datetime.date(d.year, 1, 1)
                        name = "du %s au %s" % (date_debut.strftime("%d/%m/%Y"), date_fin.strftime("%d/%m/%Y"))
                        exo = Exercice.objects.create(name, date_debut, date_fin)
                        ope['exercice_id'] = exo.id
                else:
                    ope['exercice_id'] = row.exercice
                #ib
                ope['ib_id'] = self.element('ib', row.ib, Ib, {'nom':row.ib, 'type':type_cat})
                #jumelle et mere
                #attention on prend juste les id toute la creation d'eventuelles operations est plus tard
                ope['jumelle_id'] = row.jumelle
                ope['mere_id'] = row.mere
                #montant
                ope['montant'] = row.mt
                if row.moyen is not None:
                    ope['moyen_id'] = self.element('moyen', row.moyen, Moyen, {'nom':row.moyen, 'type':type_cat})
                else:
                    if type_cat == 'd':
                        ope['moyen_id'] = settings.MD_DEBIT
                    else:
                        if type_cat == 'r':
                            ope['moyen_id'] = settings.MD_CREDIT
                        else:
                            ope['moyen_id'] = Moyen.objects.filter(type='v')[0]
                ope['notes'] = row.notes
                ope['num_cheque'] = row.num_cheque
                ope['piece_comptable'] = row.piece_comptable
                ope['pointe'] = row.pointe
                ope['rapp_id'] = row.rapp
                ope['ligne'] = row.ligne
                ope['ope_titre'] = row.ope_titre
                ope['ope_pmv'] = row.ope_pmv
                opes.append(ope)
        return opes

class Csv_unicode_reader_ope_remp(Csv_unicode_reader_ope_base):
    @property
    def pk(self):
        return self.vide(self.row['id'])
    @property
    def cat(self):
        return self.vide(self.row['cat'])
    @property
    def cpt(self):
        return self.row['account name']
    @property
    def date(self):
        date_s = self.row['Date']
        return datetime.date(*time.strptime(date_s, "%d/%m/%y")[0:3])
    @property
    def ib(self):
        return self.vide(self.row['projet'])
    @property
    def mt(self):
        return utils.fr2decimal(self.row['montant'])
    @property
    def notes(self):
        return self.row['notes']
    @property
    def num_cheque(self):
        return self.vide(self.row['n chq'],"")
    @property
    def pointe(self):
        if self.row['p'] == 1:
            return True
        else:
            return False
    @property
    def rapp(self):
        return self.vide(self.row['m'])
    @property
    def tiers(self):
        return self.vide(self.row['tiers'])
    @property
    def monnaie(self):
        return "EUR"
    @property
    def mere(self):
        return self.vide(self.row['num op vent m'])
    @property
    def jumelle(self):
        return self.vide(self.row['id jumelle lie'])
    @property
    def moyen(self):
        return self.row['moyen']
    @property
    def ope_titre(self):
        return  self.row['ope_titre']
    @property
    def ope_pmv(self):
        if self.row['ope_pmv']:
            return True
        else:
            return False

class Import_csv_ope_remplacement(Import_csv_ope):
    reader = Csv_unicode_reader_ope_remp#TODO
    type_f = "csv_version_gsb"
    remplacement = True
