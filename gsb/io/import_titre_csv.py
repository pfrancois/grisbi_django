# -*- coding: utf-8 -*-
from __future__ import absolute_import


from ..models import Titre, Compte
from . import import_base
from .. import utils


class Import_csv_ope_titre(import_base.Import_base):
    reader = utils.Csv_unicode_reader
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
