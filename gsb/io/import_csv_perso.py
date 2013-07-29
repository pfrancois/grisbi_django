# -*- coding: utf-8 -*-
from __future__ import absolute_import
import datetime
import decimal

from django.conf import settings  # @Reimport

from django.contrib import messages

from ..models import (Tiers, Cat, Ib,
                     Exercice, Moyen, Compte, Titre,
                       Ope_titre, Rapp, Ope)
from . import import_base
from .. import utils


class Csv_unicode_reader_ope_base(import_base.property_ope_base, utils.Csv_unicode_reader):
    pass


class Csv_unicode_reader_ope(Csv_unicode_reader_ope_base):
    @property
    def id(self):
        return utils.to_id(self.row['id'])

    @property
    def cat(self):
        cat = utils.to_unicode(self.row['cat'], "Divers:Inconnu")
        return cat

    @property
    def cpt(self):
        cpt = utils.to_unicode(self.row['account name'])
        if cpt is None:
            raise import_base.ImportException('probleme: il faut un compte a la ligne %s' % self.line_num)
        else:
            return cpt

    @property
    def date(self):
        try:
            return utils.to_date(self.row['date'], "%d/%m/%Y")
        except ValueError:
            return None

    @property
    def ib(self):
        return utils.to_unicode(self.row['projet'], None)

    @property
    def montant(self):
        return utils.to_decimal(self.row['montant'])

    @property
    def notes(self):
        return self.row['notes']

    @property
    def num_cheque(self):
        return utils.to_unicode(self.row['n chq'], "")

    @property
    def pointe(self):
        return utils.to_bool(self.row['p'])

    @property
    def rapp(self):
        return utils.to_unicode(self.row['r'])

    @property
    def tiers(self):
        return utils.to_unicode(self.row['tiers'], "tiers inconnu")

    @property
    def monnaie(self):
        return "EUR"

    @property
    def mere(self):
        return utils.to_id(self.row['num op vent m'])

    @property
    def jumelle(self):
        return utils.to_id(self.row['id jumelle lie'])

    @property
    def moyen(self):
        return utils.to_unicode(self.row['moyen'])

    @property
    def ope_titre(self):
        return utils.to_bool(self.row['ope_titre'])

    @property
    def ope_pmv(self):
        return utils.to_bool(self.row['ope_pmv'])

    @property
    def has_fille(self):
        return utils.to_bool(self.row['has fille'])


class Import_csv_ope(import_base.Import_base):
    reader = Csv_unicode_reader_ope
    extension = ("csv",)
    type_f = "csv_version_totale"
    creation_de_compte = True
    titre = "import csv"

    def tableau_import(self, nomfich):
        """renvoi un tableau complet de l'import"""
        titre_nb = 0  # nb de nouveaux titres
        nb_titres = dict()
        ope_jumelle = list()
        with open(nomfich, 'rt') as f_non_encode:
            fich = self.reader(f_non_encode, encoding="iso-8859-1")
            verif_format = False
            for row in fich:
                if not verif_format:
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
                        row.montant
                        row.notes
                        row.num_cheque
                        row.ope_pmv
                        # row.ope_titre
                        # row.piece_comptable
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
                    raise import_base.ImportException(u"attention ce ne sera pas possible d'importer car il y a plusieurs devises")
                # compte
                try:
                    ope['compte_id'] = self.listes['compte'][row.cpt]
                except KeyError:
                    try:
                        ope['compte_id'] = Compte.objects.get(nom=row.cpt).id
                        self.listes['compte'][row.cpt] = ope['compte_id']
                    except Compte.DoesNotExist:
                        if self.creation_de_compte:
                            if row.ope_titre == False:
                                nouveau = {"nom": row.cpt, "type": "b"}
                                self.listes['compte'][row.cpt] = self.ajout(obj='compte', model=Compte, nouveau=nouveau)
                                ope['compte_id'] = self.listes['compte'][row.cpt]
                        else:
                            liste_compte = "'"
                            for cpt in Compte.objects.all():
                                liste_compte = "%s%s," % (liste_compte, cpt.nom)
                            liste_compte = "%s%s" % (liste_compte, "'")
                            raise import_base.ImportException("attention, le compte %s est demande a la ligne %s alors qu'il n'existe pas, les comptes sont %s" % (row.cpt, ope['ligne'], liste_compte))
                # cat
                type_cat = 'd' if row.montant <= 0 else 'r'
                if row.has_fille:
                    type_cat = 'd'  # par convention les ovm sont des depenses
                if row.jumelle is not None:
                    type_cat = 'v'
                    ope['cat_id'] = self.element('cat', "Virement", Cat, {'nom': "Virement", 'type': 'v'})
                    if row.jumelle is None:
                        raise import_base.ImportException("attention pas d'operation jumelle pour un virement a la ligne %s" % ope['ligne'])
                else:
                    ope['cat_id'] = self.element('cat', row.cat, Cat, {'nom': row.cat, 'type': type_cat})
                # tiers
                ope['tiers_id'] = self.element('tiers', row.tiers, Tiers, {'nom': row.tiers, 'notes': "", 'is_titre': False})
                # date
                ope['date'] = row.date
                # auto
                ope['automatique'] = row.automatique
                # date_val
                ope['date_val'] = row.date_val
                # exercice
                if row.exercice is None and settings.UTILISE_EXERCICES == True:
                    d = row.date
                    q = Exercice.objects.filter(date_debut__lte=d, date_fin__gte=d)
                    if q.exists():
                        exo = q[0].id
                    else:
                        # on cree un exercice d'un an
                        date_debut = datetime.date(d.year, 1, 1)
                        date_fin = datetime.date(d.year, 12, 31)
                        name = "du %s au %s" % (date_debut.strftime("%d/%m/%Y"), date_fin.strftime("%d/%m/%Y"))
                        exo = self.ajout('exercice', Exercice, {"nom": name, "date_debut": date_debut, "date_fin": date_fin})
                    ope['exercice_id'] = exo
                else:
                    ope['exercice_id'] = None
                # ib
                if settings.UTILISE_IB == True:
                    ope['ib_id'] = self.element('ib', row.ib, Ib, {'nom': row.ib, 'type': type_cat})
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
                ope['montant'] = row.montant
                if row.moyen is not None:
                    ope['moyen_id'] = self.element('moyen', row.moyen, Moyen, {'nom': row.moyen, 'type': type_cat})
                    if ope['moyen_id'] == self.listes['moyen']['Virement'] and row.jumelle is None:
                        raise import_base.ImportException("attention pas d'operation jumelle pour un virement a la ligne %s" % ope['ligne'])
                else:
                    if type_cat == 'd':
                        ope['moyen_id'] = settings.MD_DEBIT
                    else:
                        if type_cat == 'r':
                            ope['moyen_id'] = settings.MD_CREDIT
                        else:
                            ope['moyen_id'] = self.listes['moyen']['Virement']
                            if row.jumelle is None:
                                raise import_base.ImportException(u"attention pas d'operation jumelle pour un virement a la ligne %s" % ope['ligne'])
                ope['notes'] = row.notes
                ope['num_cheque'] = row.num_cheque
                ope['piece_comptable'] = row.piece_comptable
                ope['pointe'] = row.pointe
                if row.jumelle == row.id:
                    import_base.ImportException(u"virement incorect a la ligne %s" % ope['ligne'])
                if row.rapp is not None:
                    ope['rapp_id'] = self.element('rapp', row.rapp, Rapp, {'nom': row.rapp, 'date': utils.today()})
                else:
                    ope['rapp_id'] = None
                ope['ligne'] = row.line_num
                if row.ope_titre == False and row.ope_pmv == False:  # on elimine les ope_pmv et les ope_titre sont gere en dessous
                    ope_id = self.ajout('ope', Ope, ope)
                    self.listes['ope'][row.id] = ope_id
                if row.ope_titre == True:
                    cpt_titre = self.listes['compte'][row.cpt]
                    ok = False
                    if self.creation_de_compte:
                        for cptr_boucle in self.ajouter['compte']:
                            if cptr_boucle['id'] == cpt_titre:
                                cptr_boucle['type'] = "t"
                                ok = True
                            if not ok:
                                Cpt = Compte.objects.filter(id=cpt_titre)
                                if Cpt.exists():
                                        cpt[0].type = 't'
                                else:
                                    raise import_base.ImportException(u'attention un compte a été change en cpt titre ligne %s' % row.line_num)

                    # gestion des ope_titre
                    try:
                        titre_id = self.listes['titre'][ope['tiers_id']]  # pylint: disable=W0622
                        ope['titre_id'] = titre_id
                    except KeyError:
                        titre_nb += 1
                        # reflechir si on met des fetch related
                        name = row.tiers[7:]
                        try:
                            titre_id = Titre.objects.get(nom=name).id
                        except Titre.DoesNotExist:
                            if name == '' or name is None or name == 0:
                                name = u"titre %s inconnu cree le %s" % (titre_nb, utils.now().strftime("%d/%m/%Y a %H:%M:%S"))
                            isin = u"ZZ%s%s" % (utils.today().strftime('%d%m%Y'), titre_nb)
                        # on cree en lazy un titre
                            titre_id = self.ajout('titre', Titre, {'nom': name, 'type': 'ZZZ', 'isin': isin, 'tiers_id': ope['tiers_id']})
                        self.listes['titre'][ope['tiers_id']] = titre_id
                        ope['titre_id'] = titre_id
                    # on recupere le reste
                    s = row.notes.partition('@')
                    try:
                        nombre = decimal.Decimal(s[0])
                        cours = decimal.Decimal(s[2])
                    except KeyError:
                        self.erreur.append('probleme import operation ligne %s # %s:pas bon format des notes pour importation, il doit etre de la forme nombre@montant' % (row.line_num, row.id))
                    except decimal.InvalidOperation:
                        if s[0] == '':
                            self.erreur.append('probleme import operation ligne %s # %s:pas bon format des notes pour importation' % (row.line_num, row.id))
                        if s[1] == '':
                            if not self.test:
                                messages.info(self.request, "le cours de l'ope_titre %s à ligne %s etait de 1" % (row.id, row.line_num))
                            cours = 1
                    try:
                        nb_titres[titre_id] = nb_titres[titre_id] + nombre
                    except KeyError:
                        try:
                            nb_titres[titre_id] = nombre + Titre.objects.get(id=titre_id).nb()
                        except Titre.DoesNotExist:
                            nb_titres[titre_id] = nombre
                    if nb_titres[titre_id] < 0:
                        raise import_base.ImportException('attention il ne peut avoir un solde de titre negatif pour le titre %s a la ligne %s' % (row.tiers[7:], row.line_num))
                    nouveau = {"titre_id": ope['titre_id'],
                             "compte_id": ope['compte_id'],
                             "nombre": nombre,
                             "cours": cours,
                             "date": ope['date'],
                             "rapp_id": ope['rapp_id'],  # on le met ici car comme les opes
                             'pointe': ope['pointe'],
                             "exercice_id": ope["exercice_id"],
                             "ligne": row.line_num}
                    self.ajout('ope_titre', Ope_titre, nouveau)

        if not self.test:
            print "-----------second tour-----"
        self.flag = True
        for ope in self.ajouter['ope']:
            if ope['jumelle_id'] is not None:
                try:
                    ope['jumelle_id'] = self.listes['ope'][ope['jumelle_id']]
                except KeyError:
                    self.erreur.append("attention il y a une des deux branches qui n'existe pas. id %s ligne %s " % (ope['jumelle_id'], ope['ligne']))
                if ope['jumelle_id'] not in ope_jumelle:
                    ope_jumelle.append(ope['jumelle_id'])
                else:
                    raise import_base.ImportException("attention un virement ne peut se faire qu'entre deux opes pas plus. ligne %s" % ope['ligne'])
                # on ecrase le nom du tiers et la cat afin d'homogeneiser
                ope['tiers_id'] = self.element('tiers', "Virement", Tiers, {'nom': "Virement", 'notes': "", 'is_titre': False})
                if ope['moyen_id'] == self.listes['moyen']["Virement"]:
                    pass
                else:
                    if not self.test:
                        messages.info(self.request, u"harmonisation de la cat en 'virement' de l'ope à la ligne %s " % ope['ligne'])
                    ope['cat_id'] = self.element('cat', "Virement", Cat, {'nom': "Virement", 'type': 'v'})
                for jumelle in self.ajouter['ope']:
                    if jumelle['id'] == ope['jumelle_id']:  # jumelle trouve
                        if jumelle['montant'] != ope['montant'] * -1:
                            if self.flag == True:
                                self.erreur.append("attention le montant entre les deux partie du virement n'est pas le meme. ligne %s et %s" % (ope['ligne'], jumelle['ligne']))
                                self.flag = False
                            else:
                                self.flag = True
                        if jumelle['date'] != ope['date']:
                            ope['date'] = jumelle['date']
                            if not self.test:
                                messages.info(self.request, "attention la date corrige. ligne %s et %s" % (ope['ligne'], jumelle['ligne']))
            if ope['mere_id'] is not None:
                try:
                    ope['mere_id'] = self.listes['ope'][ope['mere_id']]
                except KeyError:
                    self.erreur.append("attention opemere n'existe pas.  ligne %s " % ope['ligne'])
            if ope['has_fille'] == True:
                ope['cat_id'] = self.element('cat', "Opération Ventilée", Cat, {'nom': u"opération ventilée", 'type': 'd'})
