# -*- coding: utf-8 -*-
from __future__ import absolute_import
import csv
import datetime
import decimal

from django.conf import settings  # @Reimport

from django.contrib import messages

from gsb.utils import UTF8Recoder
from .models import (Tiers, Cat, Ib,
                     Exercice, Moyen, Compte, Titre,
                      Compte_titre, Ope_titre, Rapp, Ope)
from . import import_base
from . import utils


class Csv_unicode_reader(object):
    """
    A CSV reader which will iterate over lines in the CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, fich, dialect=utils.Excel_csv, encoding="utf-8", **kwds):  # pylint: disable=W0231
        self.line_num = 1
        fich = UTF8Recoder(fich, encoding)
        self.reader = csv.DictReader(fich, dialect=dialect, **kwds)

    def next(self):
        self.line_num += 1
        self.row = self.reader.next()
        return self

    def __iter__(self):
        return self


class Csv_unicode_reader_ope_base(import_base.property_ope_base, Csv_unicode_reader):
    @property
    def ligne(self):
        return self.line_num



class Csv_unicode_reader_ope(Csv_unicode_reader_ope_base):
    @property
    def id(self):
        return self.to_id(self.row['id'])

    @property
    def cat(self):
        cat = self.to_str(self.row['cat'], "Divers:Inconnu")
        return cat 

    @property
    def cpt(self):
        cpt = self.to_str(self.row['account name'])
        if cpt is None:
            raise self.erreur.append('probleme: il faut un compte a la ligne %s' % self.ligne)
        else:
            return cpt

    @property
    def date(self):
        return self.to_date(self.row['date'], "%d/%m/%Y")

    @property
    def ib(self):
        return self.to_str(self.row['projet'])

    @property
    def mt(self):
        return self.to_decimal(self.row['montant'])
    
    @property
    def notes(self):
        return self.row['notes']

    @property
    def num_cheque(self):
        return self.to_str(self.row['n chq'], "")

    @property
    def pointe(self):
        return self.to_bool(self.row['p'])

    @property
    def rapp(self):
        return self.to_str(self.row['m'])

    @property
    def tiers(self):
        return self.to_str(self.row['tiers'], "tiers inconnu")

    @property
    def monnaie(self):
        return "EUR"

    @property
    def mere(self):
        return self.to_id(self.row['num op vent m'])

    @property
    def jumelle(self):
        return self.to_id(self.row['id jumelle lie'])

    @property
    def moyen(self):
        return self.to_str(self.row['moyen'])

    @property
    def ope_titre(self):
        return self.to_bool(self.row['ope_titre'])

    @property
    def ope_pmv(self):
        return self.to_bool(self.row['ope_pmv'])

    @property
    def has_fille(self):
        return self.to_bool(self.row['has_fille'])


class Import_csv_ope(import_base.Import_base):
    reader = Csv_unicode_reader_ope
    extension = ("csv",)
    type_f = "csv_version_totale"
    creation_de_compte = True

    def tableau_import(self, nomfich):
        """renvoi un tableau complet de l'import"""
        titre_nb = 0 #nb de nouveaux titres
        nb_titres=dict()
        with open(nomfich, 'rt') as f_non_encode:
            fich = self.reader(f_non_encode, encoding="iso-8859-1")
            for row in fich:
                if row.row['date'] == "":
                    continue
                ope = dict()
                ope['ligne'] = row.ligne
                print row.ligne
                #verification pour les lignes
                if row.monnaie != settings.DEVISE_GENERALE:
                    raise import_base.Import_exception(u"attention ce ne sera pas possible d'importer car il y a plusieurs devises")
                #compte
                try:
                    ope['compte_id'] = self.listes['compte'][row.cpt]
                except KeyError:
                    try:
                        ope['compte_id'] = Compte.objects.get(nom=row.cpt).id
                        self.listes['compte'][row.cpt] = ope['compte_id']
                    except Compte.DoesNotExist:
                        if self.creation_de_compte:
                            nouveau = {"nom":row.cpt, "type":"b"}
                            self.listes['compte'][row.cpt] = self.ajout(obj='compte', model=Compte, nouveau=nouveau)
                            ope['compte_id'] = self.listes['compte'][row.cpt] 
                        else:
                            liste_compte = "'"
                            for cpt in Compte.objects.all():
                                liste_compte = "%s%s," % (liste_compte, cpt.nom)
                            liste_compte = "%s%s" % (liste_compte, "'")
                            raise import_base.Import_exception("attention, le compte %s est demande a la ligne %s alors qu'il n'existe pas, les comptes sont %s" % (row.cpt, row.line_num, liste_compte))
                #cat
                type_cat = 'd' if row.mt < 0 else 'r'
                if row.jumelle is not None:
                    ope['cat_id'] = self.element('cat', "Virement", Cat, {'nom': "Virement", 'type': 'v'})
                else:
                    ope['cat_id'] = self.element('cat', row.cat, Cat, {'nom': row.cat, 'type': type_cat})
                #tiers
                ope['tiers_id'] = self.element('tiers', row.tiers, Tiers, {'nom': row.tiers, 'notes': "", 'is_titre': False})
                #date
                ope['date'] = row.date
                #auto
                ope['automatique'] = row.automatique
                #date_val
                ope['date_val'] = row.date_val
                #exercice
                if row.exercice is None and settings.UTILISE_EXERCICES == True:
                    d = row.date
                    q = Exercice.objects.filter(date_debut__lte=d, date_fin__gte=d)
                    if q.exists():
                        exo = q[0].id
                    else:
                        #on cree un exercice d'un an
                        date_debut = datetime.date(d.year, 1, 1)
                        date_fin = datetime.date(d.year, 12, 31)
                        name = "du %s au %s" % (date_debut.strftime("%d/%m/%Y"), date_fin.strftime("%d/%m/%Y"))
                        exo = self.ajout('exercice', Exercice, {"nom":name, "date_debut":date_debut, "date_fin":date_fin})
                    ope['exercice_id'] = exo
                else:
                    ope['exercice_id'] = None
                #ib
                if settings.UTILISE_IB == True:
                    ope['ib_id'] = self.element('ib', row.ib, Ib, {'nom': row.ib, 'type': type_cat})
                else:
                    ope['ib_id']=None
                #jumelle et mere
                #attention on prend juste les id toute la creation d'eventuelles operations est plus tard
                ope['jumelle_id'] = row.jumelle
                ope['mere_id'] = row.mere
                ope['has_fille'] = row.has_fille
                #montant
                ope['montant'] = row.mt
                if row.moyen is not None:
                    ope['moyen_id'] = self.element('moyen', row.moyen, Moyen, {'nom': row.moyen, 'type': type_cat})      
                else:
                    if type_cat == 'd':
                        ope['moyen_id'] = settings.MD_DEBIT
                    else:
                        if type_cat == 'r':
                            ope['moyen_id'] = settings.MD_CREDIT
                        else:
                            ope['moyen_id'] = Moyen.objects.filter(type='v')[0].id
                ope['notes'] = row.notes
                ope['num_cheque'] = row.num_cheque
                ope['piece_comptable'] = row.piece_comptable
                ope['pointe'] = row.pointe
                
                if row.rapp is not None:
                    ope['rapp_id'] = self.element('rapp', row.rapp, Rapp, {'nom': row.rapp, 'date': utils.today()})
                else:
                    ope['rapp_id'] = None
                ope['ligne'] = row.ligne
                if row.ope_titre == False and row.ope_pmv == False:#on elimine les ope_pmv et les ope_titre sont gere en dessous
                    ope_id = self.ajout('ope', Ope, ope)
                    self.listes['ope'][row.id] = ope_id
                
                if row.ope_titre == True:
                    #on verifie que le compte_titre existe et au besoin on l'ajoute
                    try:
                        self.listes['compte_titre'][row.cpt]
                    except KeyError:  
                        try:
                            self.listes['compte_titre'][row.cpt] = Compte_titre.objects.get(nom=ope['compte_id'])
                        except Compte_titre.DoesNotExist:
                            if Compte.objects.filter(nom=ope['compte_id']).exists():
                                raise import_base.Import_exception('probleme import operation ligne %s # %s:le compte n\'est pas un compte titre' % (row.ligne, row.id))
                            else:
                                for cpt in self.ajouter['compte']:
                                    if cpt['id'] == ope['compte_id']:
                                        self.ajouter['compte_titre'].append({'id':ope['compte_id'], 'nom':row.cpt, 'type':'t'})
                                        cpt['type'] = 't'
                                        self.listes['compte_titre'][row.cpt] = ope['compte_id']
                    #gestion des ope_titre
                    try:
                        titre_id = self.listes['titre'][ope['tiers_id']]  # pylint: disable=W0622
                        ope['titre_id'] = titre_id
                    except KeyError:
                        titre_nb += 1
                        #reflechir si on met des fetch related
                        name = row.tiers[7:]
                        try:
                            titre_id = Titre.objects.get(nom=name).id
                        except Titre.DoesNotExist:
                            if name == '' or name is None or name == 0:
                                name = u"titre %s inconnu cree le %s" % (titre_nb, utils.now().strftime("%d/%m/%Y a %H:%M:%S"))
                            isin = u"ZZ%s%s" % (utils.today().strftime('%d%m%Y'), titre_nb)
                        #on cree en lazy un titre
                            titre_id = self.ajout('titre', Titre, {'nom': name, 'type': 'ZZZ', 'isin': isin, 'tiers_id': ope['tiers_id']})
                        self.listes['titre'][ope['tiers_id']] = titre_id
                        ope['titre_id'] = titre_id
                    #on recupere le reste
                    s = row.notes.partition('@')
                    try:
                        nombre = decimal.Decimal(s[0])
                        cours = decimal.Decimal(s[2])
                    except KeyError:
                        self.erreur.append('probleme import operation ligne %s # %s:pas bon format des notes pour importation, il doit etre de la forme nombre@montant' % (row.ligne, row.id))
                    except  decimal.InvalidOperation:
                        if s[0] == '':
                            self.erreur.append('probleme import operation ligne %s # %s:pas bon format des notes pour importation' % (row.ligne, row.id))
                        if s[1] == '':
                            messages.info(self.request, "le cours de l'ope_titre %s à ligne %s etait de 1" % (row.id, row.ligne))
                            cours = 1
                    try:
                        nb_titres[titre_id]=nb_titres[titre_id]+nombre
                    except KeyError:
                        try: 
                            nb_titres[titre_id]=nombre+Titre.objects.get(id=titre_id).nb()
                        except Titre.DoesNotExist:
                            nb_titres[titre_id]=nombre
                    if nb_titres[titre_id] <0:
                        raise import_base.Import_exception('attention il ne peut avoir un solde de titre negatif pour le titre %s a la ligne %s' % (row.tiers[7:],row.ligne))
                        
                    nouveau = {"titre_id":ope['titre_id'],
                             "compte_id":ope['compte_id'],
                             "nombre":nombre,
                             "cours":cours,
                             "date":ope['date'],
                             "rapp_id":ope['rapp_id'], #on le met ici car comme les opes
                             'pointe':ope['pointe'],
                             "exercice_id":ope["exercice_id"],
                             "ligne":row.ligne}
                    self.ajout('ope_titre', Ope_titre, nouveau)

        print "-----------second tour-----"
        for ope in self.ajouter['ope']:
            print 2, ope['ligne']
            if ope['jumelle_id'] is not None:
                try:
                    ope['jumelle_id'] = self.listes['ope'][ope['jumelle_id']]
                except KeyError:
                    self.erreur.append("attention il y a une des deux branches qui n'existe pas. id %s ligne %s " % (ope['jumelle_id'], ope['ligne']))
                #on ecrase le nom du tiers et la cat afin d'homogeneiser
                ope['tiers_id'] = self.element('tiers', "Virement", Tiers, {'nom': "Virement", 'notes': "", 'is_titre': False})
                if ope['moyen_id'] == self.listes['moyen']['Virement']:
                    pass
                else:
                    messages.info(self.request, u"harmonisation de la cat en 'Virement' de l'ope à la ligne %s " % ope['ligne']) 
                    ope['cat_id'] = self.element('cat', "Virement", Cat, {'nom': "Virement", 'type':'v'})
                for jumelle in self.ajouter['ope']:
                    if jumelle['id'] == ope['jumelle_id']:#jumelle trouve
                        if jumelle['montant'] != ope['montant'] * -1:
                            self.erreur.append("attention le montant entre les deux partie du virement n'est pas le meme. ligne %s et %s" % (ope['ligne'], jumelle['ligne']))
                        if jumelle['date'] != ope['date']:
                            ope['date'] = jumelle['date']
                            messages.info(self.request, "attention la date corrige. ligne %s et %s" % (ope['ligne'], jumelle['ligne']))

                    
            if ope['mere_id'] is not None:
                ope['mere_id'] = self.listes['ope'][ope['mere_id']]
            if ope['has_fille'] == True:
                ope['cat_id'] = self.element('cat', "Opération Ventilée", Cat, {'nom': "Virement", 'type':'v'})
                

class Csv_unicode_reader_pocket_money(Csv_unicode_reader_ope_base):
    @property
    def cat(self):
        return self.to_id(self.row['Category'])

    @property
    def cpt(self):
        cpt = self.to_str(self.row['Account'])
        if cpt is None:
            raise self.erreur.append('probleme: il faut un compte a la ligne %s' % self.ligne)
        else:
            return cpt

    @property
    def date(self):
        return self.to_date(self.row['Date'], "%d/%m/%y")

    @property
    def ib(self):
        return self.to_id(self.row['Class'])

    @property
    def mt(self):
        return self.to_decimal(self.row['Amount'])

    @property
    def notes(self):
        return self.to_str(self.row['Memo'], "")

    @property
    def num_cheque(self):
        return self.to_str(self.row['ChkNum'], '')

    @property
    def pointe(self):
        if self.to_str(self.row['Cleared']) == "*":
            return True
        else:
            return False

    @property
    def tiers(self):
        return self.to_id(self.row['Payee'])

    @property
    def monnaie(self):
        return self.to_str(self.row['CurrencyCode'])

