# -*- coding: utf-8 -*-
from __future__ import absolute_import


from ..models import Titre, Compte
from . import import_base
from .. import utils

def mot(var):
    return var.partition(' ')[0].strip()
def reste(var):
    return var.partition(' ')[2].strip()
def mots(var):
    tour = var.split(' ')
    tour1 = []
    for i in tour:
        if i.strip() != '':
            tour1.append(i.strip())
    return tour1


class csv_sg_reader(utils.Csv_unicode_reader):
    @property
    def lib(self):
        return self.row['lib'].strip()
    @property
    def detail(self):
        return self.row['detail'].strip()
    @property
    def det(self):
        tour1 = mots(self.detail)
        retour = None
        try:
            if tour1[1] == "EUROPEEN":
                tour1 = ' '.join(tour1[4:])
                retour = tour1
            if self.moyen == "VIR RECU":
                retour = ' '.join(tour1[3:])
            if retour is None:
                retour = ' '.join(tour1[2:])
        except IndexError:
            retour = ' '.join(tour1[1:])
        return retour.strip()

    @property
    def id(self):
        return None

    @property
    def cat(self):
        return None

    @property
    def automatique(self):
        return False

    @property
    def cpt(self):
        return 'SG'

    @property
    def date(self):
        if self.moyen != "visa":
            try:
                if mots(self.detail)[2] == "RETRAIT":
                    annee = utils.to_date(self.row['date'], "%d/%m/%Y").year
                    if mots(self.detail)[4] != "SG":
                        return utils.to_date("%s/%s" % (mots(self.detail)[4], annee), "%d/%m/%Y")
                    else:
                        return utils.to_date("%s/%s" % (mots(self.detail)[5], annee), "%d/%m/%Y")
            except IndexError:
                return utils.to_date(self.row['date'], "%d/%m/%Y")
        else:
            # paiment visa
            annee = utils.to_date(self.row['date'], "%d/%m/%Y").year
            return utils.to_date("%s/%s" % (mots(self.detail)[2], annee), "%d/%m/%Y")

    @property
    def date_val(self):
        if self.moyen == "visa":
            return utils.to_date(self.row['date'].strip(), "%d/%m/%Y")
        else:
            return None

    @property
    def exercice(self):
        return None

    @property
    def ib(self):
        return None

    @property
    def jumelle(self):
        # un retrait
        if self.detail[:19] == u"CARTE X4983 RETRAIT":
            return "caisse"
        if self.det[:14] == "GENERATION VIE":
            return "generation vie"
        if self.det[:16] == "Gr Bque - Banque":
            return "BDF PEE"
        return None

    @property
    def mere(self):
        return None

    @property
    def mt(self):
        return utils.to_decimal(self.row['montant'])

    @property
    def moyen(self):
        m = mots(self.detail)
        if mots(self.detail)[0] == "CARTE":
            if mots(self.detail)[2] != "RETRAIT":
                moyen = "visa"
            else:
                moyen = "virement"
        elif m[0] == "VIR" and m[1] == "RECU":
            moyen = "recette"
        elif m[0] == "CHEQUE":
            moyen = "cheque"
        else:
            moyen = "prelevement"
        return moyen

    @property
    def notes(self):
        return self.detail

    @property
    def num_cheque(self):
        if self.moyen == "CHEQUE":
            return int(self.detail.partition(' ')[2].strip())
        else:
            return None

    @property
    def piece_comptable(self):
        return ''

    @property
    def pointe(self):
        return True

    @property
    def rapp(self):
        return None

    @property
    def tiers(self):
        if self.moyen == "cheque":
            return "inconnu"
        if self.moyen == "virement" and self.mt < 0:
            return "%s=>%s" % (self.cpt, self.jumelle)
        if self.moyen == "virement" and self.mt > 0:
            return "%s=>%s" % (self.jumelle, self.cpt)
        if self.moyen == "visa":
            return " ".join(mots(self.detail)[3:])
        if "%s %s" % (mots(self.detail)[0], mots(self.detail)[1]) == "VIR RECU":
            return " ".join(mots(self.detail)[4:6])
        return self.det.lower()

    @property
    def monnaie(self):
        return self.row['devise']

    @property
    def ope_titre(self):
        return False

    @property
    def ope_pmv(self):
        return False

    @property
    def ligne(self):
        return self.line_num

    @property
    def has_fille(self):
        return False


class Import_csv_ope_titre(import_base.Import_base):
    reader = csv_sg_reader
    extension = ("csv",)
    type_f = "csv_ope_titres"
    creation_de_compte = False

    def import_file(self, nomfich):
        """renvoi un tableau complet de l'import"""
        self.erreur = list()
        self.nb = dict()
        self.id = dict()
        liste = {'titre': dict(), 'compte': dict()}
        for titre in Titre.objects.all():
            liste['titre'][titre.nom] = titre.id
        for compte in Compte.objects.all():
            liste['compte'][compte.nom] = compte.id

        with open(nomfich, 'rt') as f_non_encode:
            fich = self.reader(f_non_encode, encoding="iso-8859-1")
            verif_format = False
            opes = list()
            for row in fich:
                if not verif_format:
                    try:
                        row.compte
                        row.date
                        row.titre
                        row.nombre
                        row.cours
                        row.taxes
                    except KeyError as excp:
                        raise import_base.ImportException(u"il manque la colonne '%s'" % excp.message)
                    else:
                        verif_format = True
                ope = dict()
                ope['ligne'] = row.ligne
                ope['date'] = row.date
                ope['compte'] = liste['compte'][row.compte]
                ope["titre"] = liste['titre'][row.titre]
                ope['nombre'] = row.nombre
                ope['cours'] = row.cours
                ope['taxes'] = row.taxes
                opes.append(ope)
        self.resultat = opes
        return True

