# -*- coding: utf-8 -*-
from __future__ import absolute_import
import csv
import cStringIO
import codecs
import sys
import datetime
import time
import os
import logging
import decimal

class Import_exception(Exception):
    pass

class UTF8Recoder:
    """
    Iterator that reads an encoded stream and reencodes the input to UTF-8
    """

    def __init__(self, fich, encoding):
        self.reader = codecs.getreader(encoding)(fich)

    def __iter__(self):
        return self

    def next(self):
        return self.reader.next().encode("utf-8")


class Excel_csv(csv.Dialect):
    """Describe the usual properties of Excel-generated CSV files."""
    delimiter = ';'
    quotechar = '"'
    doublequote = True
    skipinitialspace = False
    lineterminator = "\r\n"
    quoting = csv.QUOTE_MINIMAL

csv.register_dialect("excel_csv", Excel_csv)


def strpdate(end_date,fmt="%Y-%m-%d"):
    """@param s: YYYY-MM-DD
    attention si s est None ou impossible renvoie None"""
    if end_date is not None:
        try:
            end_date = time.strptime(end_date, fmt)
        except ValueError as  v:
            if len(v.args) > 0 and v.args[0][:26] == 'unconverted data remains: ':
                end_date = end_date[:-(len(v.args[0])-26)]
                end_date = time.strptime(end_date, fmt)
            else:
                raise v
        return datetime.date(*end_date[0:3])
    else:
        return datetime.date(1, 1, 1)

class Csv_unicode_reader_ope_remp(object):

    def __init__(self, fich, dialect=Excel_csv, encoding="utf-8", **kwds):  # pylint: disable=W0231
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

    @property
    def ligne(self):
        return self.line_num

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
        date_s = self.row['date']
        return strpdate(date_s, "%d/%m/%y")
    @property
    def ib(self):
        return self.vide(self.row['projet'])

    @property
    def mt(self):
        s=self.row['montant']
        if s is not None:
            return decimal.Decimal(str(s).replace(',', '.'))
        else:
            return decimal.Decimal('0')


    @property
    def notes(self):
        return self.row['notes']

    @property
    def num_cheque(self):
        return self.vide(self.row['n chq'], "")

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
    @property
    def exercice(self):
        return None


logger = logging.getLogger('gsb.import')
listes = dict()
nb = dict()
listes['id'] = dict()
test = None
nomfich = "../export_ope_18_11_2012-05_17_47.csv"
with open(nomfich, 'rt') as f_non_encode:
    opes = list()
    fich = Csv_unicode_reader_ope_remp(f_non_encode, encoding="iso-8859-1")
    for row in fich:
        ope = dict()
        #verification pour les lignes
        if row.monnaie != "EUR":
            raise Import_exception(u"attention ce ne sera pas possible d'importer car il y a plusieurs devises")
        #id ope
        ope['pk'] = row.pk
        #compte
        ope['compte_id'] = row.cpt
        #cat
        type_cat = 'd' if row.mt < 0 else 'r'
        if row.jumelle is not None:
            type_cat = 'v'
        ope['cat_id'] = row.cat
        #tiers
        ope['tiers_id'] = row.tiers
        #date
        ope['date'] = row.date
        #auto
        ope['automatique'] = None
        #date_val
        ope['date_val'] = None
        #exercice
        ope['exercice_id'] = row.exercice
        #ib
        ope['ib_id'] = row.ib
        #jumelle et mere
        #attention on prend juste les id toute la creation d'eventuelles operations est plus tard
        ope['jumelle_id'] = row.jumelle
        ope['mere_id'] = row.mere
        #montant
        ope['montant'] = row.mt
        if row.moyen is not None:
            ope['moyen_id'] = row.moyen
        else:
            if type_cat == 'd':
                ope['moyen_id'] = 1111
            else:
                if type_cat == 'r':
                    ope['moyen_id'] = 2222
                else:
                    ope['moyen_id'] = 3333
        ope['notes'] = row.notes
        ope['num_cheque'] = row.num_cheque
        ope['piece_comptable'] = None
        ope['pointe'] = row.pointe
        ope['rapp_id'] = row.rapp
        ope['ligne'] = row.ligne
        ope['ope_titre'] = row.ope_titre
        ope['ope_pmv'] = row.ope_pmv
        print ope
        opes.append(ope)
print "___________________________________"
print opes
