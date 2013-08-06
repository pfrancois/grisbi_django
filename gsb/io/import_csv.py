# -*- coding: utf-8 -*-
from __future__ import absolute_import

from django.conf import settings  # @Reimport

from django.contrib import messages

from .. import models
from . import import_base
from .. import utils

class Csv_unicode_reader_ope_base(import_base.property_ope_base, utils.Csv_unicode_reader):
    pass

class Csv_unicode_reader_ope(Csv_unicode_reader_ope_base):
    @property
    def id(self):
        if 'id' in self.row:
            return utils.to_id(self.row['id'])

    @property
    def cat(self):
        if self.jumelle:
            return 'Virement'
        else:
            return utils.to_unicode(self.row['cat'], "Divers:Inconnu")

    @property
    def cpt(self):
        if 'cpt' in self.row:
            cpt = utils.to_unicode(self.row['cpt'])
        else:
            cpt = "Caisse"
        if cpt is None:
            return "Caisse"
        else:
            return cpt

    @property
    def date(self):
        try:
            return utils.to_date(self.row['date'], "%d/%m/%Y")
        except utils.FormatException:
            raise utils.FormatException ("%s" % self.row['date'])

    @property
    def ib(self):
        if 'projet' in self.row:
            return utils.to_unicode(self.row['projet'], None)

    @property
    def montant(self):
        return utils.to_decimal(self.row['montant'])


    @property
    def notes(self):
        if 'notes' in self.row:
            return self.row['notes']
        else:
            return ""

    @property
    def num_cheque(self):
        if 'numchq' in self.row:
            return utils.to_unicode(self.row['numchq'], "")
        else:
            return ""

    @property
    def pointe(self):
        if 'p' in self.row:
            return utils.to_bool(self.row['p'])
        else:
            return False

    @property
    def rapp(self):
        if 'r' in self.row:
            return utils.to_bool(self.row['r'])
        else:
            return False

    @property
    def tiers(self):
        return utils.to_unicode(self.row['tiers'], "tiers inconnu")

    @property
    def monnaie(self):
        return "EUR"

    @property
    def mere(self):
        if 'id_ope_m' in self.row:
            return utils.to_id(self.row['id_ope_m'])
    

    @property
    def jumelle(self):
        if self.tiers.count('=>') == 1:
            return True
        return False

    @property
    def moyen(self):
        if 'moyen' in self.row:
            return utils.to_unicode(self.row['moyen'], None)
        else:
            return None

    @property
    def ope_titre(self):
        if 'ope_titre' in self.row:
            return utils.to_bool(self.row['ope_titre'])

    @property
    def ope_pmv(self):
        if 'ope_pmv' in self.row:
            return utils.to_bool(self.row['ope_pmv'])

    @property
    def has_fille(self):
        if 'has_fille' in self.row:
            return utils.to_bool(self.row['has_fille'])
        else:
            return False

    @property
    def ligne(self):
        return self.line_num

class Import_csv_ope(import_base.Import_base):
    reader = Csv_unicode_reader_ope
    extension = ("csv",)
    type_f = "csv_version_totale"
    creation_de_compte = True
    titre = "import csv"
    encoding = "iso-8859-1"

    def init_cache(self):
        self.moyens = import_base.Moyen_cache(self.request)
        self.cats = import_base.Cat_cache(self.request)
        self.ibs = import_base.IB_cache(self.request)
        self.comptes = import_base.Compte_cache(self.request)
        self.banques = import_base.Banque_cache(self.request)
        self.cours = import_base.Cours_cache(self.request)
        self.exos = import_base.Exercice_cache(self.request)
        self.tiers = import_base.Tiers_cache(self.request)
        self.opes = import_base.Ope_cache(self.request)
        self.titres = import_base.Titre_cache(self.request)
        self.moyen_par_defaut = import_base.moyen_defaut_cache(self.request)

    def import_file(self, nomfich):
        """renvoi un tableau complet de l'import"""
        self.init_cache()
        self.erreur = list()

        # les moyens par defaut
        moyen_virement = self.moyens.goc('', {'nom':"virement", 'type':'v'})
        retour = False
        try:
            with open(nomfich, 'rt') as f_non_encode:
                fich = self.reader(f_non_encode, encoding=self.encoding)
                #---------------------- boucle
                retour = self.tableau(fich, moyen_virement)
                #------------------fin boucle
        except (utils.FormatException, import_base.ImportException) as e:
            messages.error(self.request, "attention traitement interrompu parce que %s" % e)
            retour = False
        # gestion des erreurs
        if len(self.erreur) or retour == False:
            for err in self.erreur:
                    messages.warning(self.request, err)
            return False
        # on gere le nombre de truc annex crée
        for obj in(self.ibs, self.banques, self.cats, self.comptes, self.cours, self.exos, self.moyens, self.tiers, self.titres):
            if obj.nb_created > 0:
                messages.info(self.request, u"%s %s crées" % (obj.nb_created, obj.element._meta.object_name))
        # maintenant on sauvegarde les operations
        for ope in self.opes.create_item:
            ligne = ope.pop('ligne')
            ope.pop('mere_id')  # on efface ca comme pour l'instant je gere pas
            if ope.get('has_fille', True):
                messages.warning(self.request, u"opé ligne %s efface car ope mere " % ligne)
                continue
            ope.pop('has_fille', False)
            virement = ope.pop('virement', False)
            if virement:
                # on cree deux operation
                ope_origine = models.Ope.objects.create(**ope)
                dest = ope.pop('dest_id')
                ope['compte'] = dest
                ope['montant'] = ope['montant'] * -1
                ope.pop('ib_id', None)
                ope_dest = models.Ope.objects.create(**ope)
                ope_origine.jumelle = ope_dest
                ope_origine.save()
                ope_dest.jumelle = ope_origine
                ope_dest.save()
            else:
                models.Ope.objects.create(**ope)
        if self.opes.nb_created > 0:
            messages.info(self.request, u"%s opés crées" % (self.opes.nb_created))

        return True 
    
    def tableau(self, fich, moyen_virement):
        # lecture effective du fichier
        verif_format = False
        for row in fich:
            if row.ligne < 1:
                self.erreur.append(u"Ligne numero %x saute" % row.ligne)
                continue
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
                    row.ligne
                    row.mere
                    row.monnaie
                    row.moyen
                    row.montant
                    row.notes
                    row.num_cheque
                    row.ope_pmv
                    row.ope_titre
                    row.piece_comptable
                    row.rapp
                    row.tiers
                except KeyError as excp:
                    raise import_base.ImportException(u"il manque la colonne '%s'" % excp.message)
                else:
                    verif_format = True
            ope = dict()
            ope['ligne'] = row.ligne
            # verification pour les lignes
            if row.monnaie != settings.DEVISE_GENERALE:
                self.erreur.append(u"la devise du fichier n'est pas la meme que celui du fichier")
                continue
            # compte
            try:
                ope['compte_id'] = self.comptes.goc(row.cpt)
            except import_base.ImportException:
                self.erreur.append(u"cpt inconnu (%s) à la ligne %s" % (row.cpt, row.ligne))
                continue
            # virement (cat, moyen)
            if "=>" in row.tiers:
                virement = True
                ope['cat_id'] = self.cats.goc('Virement')
                ope['moyen_id'] = moyen_virement
                origine = row.tiers.split("=>")[0]
                origine = origine.strip()
                dest = row.tiers.split("=>")[1]
                dest = dest.strip()
                ope['dest_id'] = self.comptes.goc(dest)
                if origine  and dest:
                    if self.comptes.goc(origine) != ope['compte_id']:
                        if self.comptes.goc(dest) != ope['compte_id']:
                            self.erreur.append(u"attention cette operation n'a pas la bonne origine, elle dit partir de %s alors qu'elle part de %s" % (origine, self.compte))
                        else:
                            self.erreur.append(u"attention cette operation n'a pas orientée corectement, il faut remplir le compte de depart et non le compte d'arrivee" % (dest, self.compte))
                        continue
                else:
                    self.erreur.append("attention il faut deux bout a un virement ligne %s" % row.ligne)
                    continue
            else:
                virement = False
                try:
                    ope['cat_id'] = self.cats.goc(row.cat)
                except import_base.ImportException:
                    self.erreur.append(u"la cat %s est inconnu à la ligne %s" % (row.cat, row.ligne))
                    continue
                try:
                    if row.moyen:
                        ope['moyen_id'] = self.moyens.goc(row.moyen)
                    else:
                            ope['moyen_id'] = self.moyen_par_defaut.goc(row.cpt, row.montant)
                except import_base.ImportException:
                    self.erreur.append(u"le moyen %s est inconnu à la ligne %s" % (row.cat, row.ligne))
                    continue
            ope['virement'] = virement
            # tiers
            ope['tiers_id'] = self.tiers.goc(row.tiers)
            # date
            try:
                ope['date'] = row.date
                if ope['date'] is None:
                    ope['date'] = utils.today()
            except utils.FormatException as e:
                self.erreur.append(u"date au mauvais format %s est inconnu à la ligne %s" % (e, row.ligne))
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
            ope['mere_id'] = row.mere
            ope['has_fille'] = row.has_fille
            # montant
            ope['montant'] = row.montant
            ope['notes'] = row.notes
            ope['num_cheque'] = row.num_cheque
            ope['piece_comptable'] = row.piece_comptable
            ope['pointe'] = row.pointe
            self.opes.create(ope)
        retour = True
        return retour


