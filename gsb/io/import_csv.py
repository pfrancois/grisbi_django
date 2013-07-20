# -*- coding: utf-8 -*-
from __future__ import absolute_import
import datetime
import decimal

from django.conf import settings  # @Reimport

from django.contrib import messages

from .. import models
from . import import_base
from .. import utils
from django.db.models import Max


class Csv_unicode_reader_ope_base(import_base.property_ope_base, utils.Csv_unicode_reader):
    pass


class Csv_unicode_reader_ope(Csv_unicode_reader_ope_base):
    @property
    def id(self):
        return utils.to_id(self.row['id'])

    @property
    def cat(self):
        if self.jumelle:
            return 'Virement'
        else:
            return utils.to_unicode(self.row['cat'], "Divers:Inconnu")

    @property
    def cpt(self):
        cpt = utils.to_unicode(self.row['cpt'])
        if cpt is None:
            return "Caisse"
        else:
            return cpt

    @property
    def date(self):
        try:
            return utils.to_date(self.row['date'], "%d/%m/%Y")
        except utils.FormatException:
            return None

    @property
    def ib(self):
            return utils.to_unicode(self.row['projet'], None)

    @property
    def mt(self):
        return utils.to_decimal(self.row['montant'])

    @property
    def notes(self):
        return self.row['notes']

    @property
    def num_cheque(self):
        return utils.to_unicode(self.row['numchq'], "")

    @property
    def pointe(self):
        return utils.to_bool(self.row['p'])

    @property
    def rapp(self):
        return utils.to_bool(self.row['r'])

    @property
    def tiers(self):
        return utils.to_unicode(self.row['tiers'], "tiers inconnu")

    @property
    def monnaie(self):
        return "EUR"

    @property
    def mere(self):
        return utils.to_id(self.row['id_ope_m'])

    @property
    def jumelle(self):
        if self.tiers.count('=>') == 1:
            return True
        return False

    @property
    def moyen(self):
        return None

    @property
    def ope_titre(self):
        return utils.to_bool(self.row['ope_titre'])

    @property
    def ope_pmv(self):
        return utils.to_bool(self.row['ope_pmv'])

    @property
    def has_fille(self):
        return utils.to_bool(self.row['has_fille'])


class Import_csv_ope(import_base.Import_base):
    reader = Csv_unicode_reader_ope
    extension = ("csv",)
    type_f = "csv_version_totale"
    creation_de_compte = True
    titre = "import csv"

    def import_file(self, nomfich):
        """renvoi un tableau complet de l'import"""
        self.erreur = list()
        self.request=getattr(self,'request',None)
        if self.request is None:
            debug=True
        self.init_class()
        nb = {"moyen": list(), 'cat': list(), 'compte': [], 'ib': []}
        nb['moyen'] = 0
        #les moyens par defaut
        created = models.Moyen.objects.get_or_create(id=settings.MD_DEBIT, defaults={"id": settings.MD_DEBIT, "nom": 'DEBIT', "type": "d"})[1]
        if created:
            if not debug: messages.info(self.request, "ajout moyen debit par defaut")
            nb['moyen'] += 1
        created = models.Moyen.objects.get_or_create(id=settings.MD_CREDIT, defaults={"id": settings.MD_CREDIT, "nom": 'CREDIT', "type": "r"})[1]
        if created:
            if not debug: messages.info(self.request, "ajout moyen credit par defaut")
            nb['moyen'] += 1
        moyen = models.Moyen.objects.filter(type='v')
        if moyen.exists():
            moyen_virement_id = models.Moyen.objects.create(nom='Virement', type="v").id
            if not debug: messages.info(self.request, "ajout moyen virement par defaut")
            nb['moyen'] += 1
        #les cat
        created = models.Moyen.objects.get_or_create(id=settings.ID_CAT_OST, defaults={"id": settings.ID_CAT_OST, "nom": 'Operation sur titre', "type": "d"})[1]
        if created:
            if not debug: messages.info(self.request, "ajout cat OST")
            nb['cat'] = 1
        else:
            nb['cat'] = 0
        created = models.Moyen.objects.get_or_create(id=settings.ID_CAT_PMV, defaults={"id": settings.ID_CAT_PMV, "nom": 'Revenus de placement:Plus-values', "type": "r"})[1]
        if created:
            if not debug: messages.info(self.request, "ajout cat PMV")
            nb['cat'] += 1
        #lecture effective du fichier
        with open(nomfich, 'rt') as f_non_encode:
            fich = self.reader(f_non_encode, encoding="iso-8859-1")
            verif_format = False
            for row in fich:
                if not verif_format:  # on verifie a la premiere ligne
                    try:
                        row.id
                        row.automatique
                        row.cat
                        row.cpt
                        row.date
                        if settings.UTILISE_EXERCICES == True:
                            row.exercice
                        row.has_fille
                        row.ib
                        row.jumelle
                        row.line_num
                        row.mere
                        row.monnaie
                        row.moyen
                        row.mt
                        row.notes
                        row.num_cheque
                        row.ope_pmv
                        #row.ope_titre
                        #row.piece_comptable
                        row.rapp
                        row.tiers
                    except KeyError as excp:
                        raise import_base.ImportException(u"il manque la colonne '%s'" % excp.message)
                    else:
                        verif_format = True
                ope = dict()
                ope['ligne'] = row.line_num
                # verification pour les lignes
                if row.monnaie != settings.DEVISE_GENERALE:
                    self.erreur.append(u"la devise du fichier n'est pas la meme que celui du fichier")
                # compte
                try:
                    ope['compte'] = self.comptes.goc(row.cpt)
                except import_base.ImportException:
                    self.erreur.append(u"cpt inconnu (%s) à la ligne %s" % (row.cpt, row.line_num))
                # cat
                if row.jumelle is not None:
                    try:
                        ope['cat_id'] = self.cats.goc('Virement')
                    except import_base.ImportException:
                        self.erreur.append(u"la cat 'virement' est inconnu à la ligne %s" % row.line_num)
                else:
                    try:
                        ope['cat_id'] = self.cats.goc(row.cat)
                    except import_base.ImportException:
                        self.erreur.append(u"la cat %s est inconnu à la ligne %s" % (row.cat, row.line_num))
                # tiers
                ope['tiers_id'] = self.tiers.goc(row.tiers)
                # date
                ope['date'] = row.date
                # auto
                ope['automatique'] = row.automatique
                # date_val
                ope['date_val'] = row.date_val
                # ib
                if settings.UTILISE_IB == True:
                    ope['ib_id'] = self.ibs.goc(row.ib)
                else:
                    ope['ib_id'] = None
                # jumelle et mere
                # attention on prend juste les id toute la creation d'eventuelles operations est plus tard
                ope['jumelle_id'] = row.jumelle
                if row.jumelle == row.id:
                    raise import_base.ImportException("attention une ope ne peut etre jumelle avec elle meme. ligne %s" % ope['ligne'])
                ope['mere_id'] = row.mere
                ope['has_fille'] = row.has_fille
                # montant
                ope['montant'] = row.mt
                ope['notes'] = row.notes
                ope['num_cheque'] = row.num_cheque
                ope['piece_comptable'] = row.piece_comptable
                ope['pointe'] = row.pointe
                self.opes.create(ope)

    def init_class(self):
        self.moyens = Moyen_cache(self.request)
        self.cats = Cat_cache(self.request)
        self.ibs = IB_cache(self.request)
        self.comptes = Compte_cache(self.request)
        self.banques = Banque_cache(self.request)
        self.cours = Cours_cache(self.request)
        self.exos = Exercice_cache(self.request)
        self.tiers = Tiers_cache(self.request)
        self.opes = Ope_cache(self.request)


class Table(object):
    """Moyen avec cache"""
    element = None
    readonly = False
    def __init__(self, request, cle='nom'):
        self.id = dict()
        self.create_item = list()
        self.request = request
        self.cle = cle
        if self.element is None:
            raise NotImplementedError("table de l'element non choisi")
        else:
            self.last_id = self.element.objects.aggregate(id_max=Max('id'))['id_max']
    def goc(self, nom):
        try:
            id = self.id[nom]
        except KeyError:
            try:
                arguments = {self.cle: nom}
                id = self.element.objects.get(**arguments).id
                self.id[nom] = id
            except self.element.DoesNotExist:
                if not self.readonly:
                    self.create_item.append(nom)
                    self.id[nom] = self.create_item.index(nom)+self.last_id
                else:
                    raise import_base.ImportException("%s non defini alors que c'est read only" % self.element.__class__.__name__)
    def save(self):
        for el in self.create_item:
            id = self.id[el]
            self.save_(id, el)
    def save_(self, id, el):
        raise NotImplementedError("methode save non defini")

class Cat_cache(Table):
    element = models.Cat
    readonly = True

class Moyen_cache(Table):
    element = models.Moyen
    readonly = True

class IB_cache(Table):
    element = models.Ib
    def save_(self, id, el):
        self.element.objects.create(id=id, nom=el, type='d')
        messages.info('creation de l\'ib "%s"' % el)

class Compte_cache(Table):
    element = models.Compte
    readonly = True

class Banque_cache(Table):
    element = models.Banque
    readonly = True

class Cours_cache(Table):
    element = models.Cours
    def goc(self, date, titre, montant):
        try:
            titre_id = self.id[titre]
            id = titre_id[date]
        except KeyError:
            try:
                el = self.element.objects.get(date=date, titre_id=titre)
                id = el.id
                if el.montant != montant:
                    raise import_base.ImportException(u'difference de montant %s et %s pour le titre %s à la date %s' % (el.montant, montant, el.titre.nom, date))
            except self.element.DoesNotExist:
                self.create_item.append({'titre': titre, 'date': date, "montant": montant})
                id = self.create_item.index({'titre': titre, 'date': date, "montant": montant}) + self.last_id
            finally:
                if self.id.get(titre) is not None:
                    self.id[titre][date] = id
                else:
                    self.id[titre] = titre
                    self.id[titre][date] = id
                id = self.id[titre][date]

class Exercice_cache(Table):
    element = models.Exercice
    readonly = True  # a finir

class Tiers_cache(Table):
    element = models.Tiers
    def save_(self, id, el):
        self.element.objects.create(id=id, nom=el)
        if not self.request: messages.info('creation du tiers "%s"' % el)

class Titre_cache(Table):
    element = models.Titre
    def save_(self, id, el):
        self.element.objects.create(id=id, isin="XX00000%s" % id, type="XXX")
class Ope_cache(Table):
    element = models.Ope
    def goc(self, nom):
        raise NotImplementedError("methode goc non defini")
    def create(self, ope):
        self.create_item.append(ope)
    def save(self):
        for ope in self.create_item:
            self.element.objects.create(**ope)
