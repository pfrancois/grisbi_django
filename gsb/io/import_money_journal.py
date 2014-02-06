# -*- coding: utf-8 -*-
from __future__ import absolute_import
#import re
# from django.conf import settings  # @Reimport

#from django.contrib import messages
#from gsb import models
from gsb import utils
#import os
#import time
#from django.http import HttpResponseRedirect
import csv
from gsb.io import import_csv
#from gsb.io import import_base
#import os


class money_journal_csv(object, csv.Dialect):
    """fichier csv de money journal"""
    delimiter = ','
    quotechar = '"'
    doublequote = True
    skipinitialspace = True
    lineterminator = "\r\n"
    quoting = csv.QUOTE_ALL


class csv_money_journal_reader(import_csv.Csv_unicode_reader_ope_sans_jumelle_et_ope_mere):
    champs = ["Date", "Type", "Paiement", u"Catégorie", u"Pièce jointe", u"Mémo", "Montant", u"Répéter"]
    champ_test = u'Catégorie'

    def __init__(self, fich, dialect=money_journal_csv, encoding="utf-8", **kwds):
        super(csv_money_journal_reader, self).__init__(fich=fich, dialect=dialect, encoding=encoding, **kwds)

    @property
    def cat(self):
        return utils.to_unicode(self.row['Catégorie'])

    @property
    def cpt(self):
        return utils.to_unicode(self.row['Paiement'])

    @property
    def date(self):
        return utils.strpdate(self.row['Date'], "%Y/%m/%d")

    @property
    def date_val(self):
        return self.date

    @property
    def montant(self):
        if self.row['Type'] == "Revenu":
            return utils.fr2decimal(self.row['Montant'][2:])
        else:
            return utils.fr2decimal(self.row['Montant'][2:]) * -1

    @property
    def moyen(self):
        if self.montant < 0:
            if self.cpt == "Sg":
                return u"carte visa"
            else:
                return u"depense"
        else:
            return u"recette"

    @property
    def notes(self):
        return ""

    @property
    def num_cheque(self):
        return ""

    @property
    def pointe(self):
        return False

    @property
    def jumelle_tiers(self):
        return False

    @property
    def tiers(self):
        if self.row['Mémo']:
            return self.row['Mémo'].lower()
        else:
            return "inconnu"

    @property
    def ligne(self):
        return self.line_num - 1

    @property
    def ib(self):
        return None

    @property
    def rapp(self):
        return None


class Import_view_money_journal(import_csv.Import_csv_ope_sans_jumelle_et_ope_mere):
    # classe du reader
    reader = csv_money_journal_reader
    # extension du fichier
    extension = ('csv',)
    # nom du type de fichier
    type_f = "csv_version_money_journal"
    encoding = "iso-8859-1"
