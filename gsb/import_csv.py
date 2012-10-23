# -*- coding: utf-8 -*-
from __future__ import absolute_import
import csv
import cStringIO
import codecs
import sys
import datetime
import time
import os

from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.core import exceptions as django_exceptions
from django.views.generic.edit import FormView
from django.db import models as models_agg
from django import forms
from django.conf import settings  # @Reimport
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist

from gsb.utils import UTF8Recoder, Writer_base, Excel_csv, Reader_base
from .models import (Tiers, Titre, Cat, Ope, Banque, Ib,
                     Exercice, Rapp, Moyen, Echeance, Compte, Compte_titre, Ope_titre)
from gsb import forms as gsb_forms
import gsb.utils as utils
from gsb.views import Mytemplateview


class Csv_unicode_reader(utils.Reader_base):
    """
    A CSV reader which will iterate over lines in the CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, fich, dialect=csv.excel, encoding="utf-8", **kwds):  # pylint: disable=W0231
        self.line_num = 0
        fich = UTF8Recoder(fich, encoding)
        self.reader = csv.DictReader(fich, dialect=dialect, **kwds)

    def next(self):
        self.line_num += 1
        self.row = self.reader.next()
        return self

    def __iter__(self):
        return self


class Csv_unicode_reader_ope_base(Csv_unicode_reader):
    @property
    def cat(self):
        return None

    @property
    def automatique(self):
        return False

    @property
    def cpt(self):
        return None

    @property
    def date(self):
        return None

    @property
    def date_val(self):
        return None

    @property
    def exercice(self):
        return None

    @property
    def ib(self):
        return None

    @property
    def jumelle(self):
        return None

    @property
    def mere(self):
        return None

    @property
    def mt(self):
        return 0

    @property
    def moyen(self):
        return None

    @property
    def notes(self):
        return None

    @property
    def num_cheque(self):
        return None

    @property
    def piece_comptable(self):
        return None

    @property
    def pointe(self):
        return None

    @property
    def rapp(self):
        return None

    @property
    def tiers(self):
        return None

    @property
    def monnaie(self):
        return None


class Csv_unicode_reader_ope(Csv_unicode_reader_ope_base):
    @property
    def cat(self):
        return self.row['Category']

    @property
    def cpt(self):
        return self.row['Account']

    @property
    def date(self):
        date_s = self.row['Date']
        return datetime.date(*time.strptime(date_s, "%d/%m/%y")[0:3])

    @property
    def ib(self):
        return self.row['Class']

    @property
    def mt(self):
        return utils.fr2decimal(self.row['Amount'])

    @property
    def notes(self):
        return self.row['Memo']

    @property
    def num_cheque(self):
        return self.row['ChkNum']

    @property
    def pointe(self):
        if self.row['Cleared'] == "*":
            return True
        else:
            return False

    @property
    def tiers(self):
        return self.row['Payee']

    @property
    def monnaie(self):
        return self.row['CurrencyCode']

    @property
    def mere(self):
        try:
            return self.row['mere']
        except KeyError:
            return None

    @property
    def jumelle(self):
        try:
            return self.row['jumelle']
        except KeyError:
            return None


#@transaction.commit_on_success
class Import_csv_ope(Mytemplateview):
    template_name = "generic.djhtm"
    titre = "import csv"
    reader = Csv_unicode_reader_ope

    def get_context_data(self, **kwargs):
        self.listes = dict()
        self.nb = dict()
        return self.import_csv()

    def element(self, liste, name, model, nouveau):
        """
        @param liste: nom de la liste ou l'on doit chercher le nom
        @param name: nom de l'element a chercher
        @param model: classe model a chercher
        @param nouveau: dic pour creer un nouveau objet
        """
        try:
            id = self.listes[liste][name]  # pylint: disable=W0622
        except KeyError:
            obj, created = model.objects.get_or_create(nom=name, defaults=nouveau)
            if created:
                try:
                    self.nb[liste] += 1
                except KeyError:
                    self.nb[liste] = 1
            id = obj.id
        return id

    def import_csv(self):

        with open(os.path.join(settings.PROJECT_PATH, "gsb", "perso.csv"), 'rt') as f_non_encode:
            opes = list()
            fich = Csv_unicode_reader_ope(f_non_encode, encoding="iso-8859-1")
            for row in fich:
                ope = dict()
                #verification pour les lignes
                if row.monnaie != settings.DEVISE_GENERALE:
                    raise utils.Import_exception(u"attention ce ne sera pas possible d'importer car il y a plusieurs devises")
                try:
                    ope['cpt_id'] = self.listes['cpt'][row.cpt]
                except KeyError:
                    try:
                        cpt = Compte.objects.get(nom=row.cpt)
                        ope['cpt_id'] = cpt.id
                    except Compte.DoesNotExist:
                        raise utils.Import_exception("attention, le compte %s est demande a la ligne %s" % (row.cpt, row.line_num))
                type_cat = 'd' if row.mt < 0 else 'r'
                ope['jumelle_id'] = row.jumelle
                if ope['jumelle_id'] is not None:
                    type_cat = 'v'
                ope['cat_id'] = self.element('cat', row.cat, Cat, {'nom': row.cat, 'type': type_cat})
                ope['tiers_id'] = self.element('tiers', row.tiers, Tiers, {'nom': row.tiers, 'notes': "", 'is_titre': False})
                ope['date'] = row.date
                ope['automatique'] = row.automatique
                ope['date_val'] = row.date_val
                ope['exercice'] = row.exercice
                ope['ib_id'] = self.element('ib', row.ib, Ib, {'nom': row.ib, 'type': type_cat})
                ope['mere_id'] = row.mere
                ope['montant'] = row.mt
                if row.moyen is not None:
                    ope['moyen'] = self.element('moyen', row.moyen, Moyen, {'nom': row.moyen, 'type': type_cat})
                else:
                    if type_cat == 'd':
                        ope['moyen'] = settings.MD_DEBIT
                    else:
                        if type_cat == 'r':
                            ope['moyen'] = settings.MD_CREDIT
                        else:
                            ope['moyen'] = Moyen.objects.filter(type='v')[0]
                ope['notes'] = row.notes
                ope['num_cheque'] = row.num_cheque
                ope['piece_comptable'] = row.piece_comptable
                ope['pointe'] = row.pointe
                ope['rapp_id'] = row.rapp
                opes.append(ope)
        print opes
