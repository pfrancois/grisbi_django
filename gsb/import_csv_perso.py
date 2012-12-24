# -*- coding: utf-8 -*-
from __future__ import absolute_import

from . import import_csv



class Csv_perso(import_csv.Csv_unicode_reader_ope_base):
    @property
    def id(self):
        return self.to_id(self.row['id'])

    @property
    def cat(self):
        cat = self.to_str(self.row['cat'], "Divers:Inconnu")
        if cat[-1]==':':#si le dernier caractere est ":" on l'enleve
            cat=cat[:-1]
        return cat 

    @property
    def cpt(self):
        cpt = self.to_str(self.row['cpt'])
        if cpt is None:
            raise self.erreur.append('probleme: il faut un compte a la ligne %s' % self.ligne)
        else:
            return cpt

    @property
    def date(self):
        return self.to_date(self.row['Date'], "%d/%m/%Y")

    @property
    def mt(self):
        return self.to_decimal(self.row['Montant'])
    
    @property
    def notes(self):
        return self.row['Notes']

    @property
    def num_cheque(self):
        return self.to_str(self.row['Num_chq'], "")

    @property
    def tiers(self):
        return self.to_str(self.row['Tiers'], "tiers inconnu")

    @property
    def monnaie(self):
        return "EUR"

    @property
    def jumelle(self):
        return self.to_id(self.row['jumelle'])

    @property
    def moyen(self):
        depense={"sg":"Prelevement","Caisse":"Depense","cb":"Visa"}
        if self.mt<0:
            try:
                return depense[self.cpt]
            except KeyError:
                return None   

class Import_csv_perso(import_csv.Import_csv_ope):
    reader = Csv_perso
    extension = ("csv",)
    type_f = "csv_perso"
    creation_de_compte = True
