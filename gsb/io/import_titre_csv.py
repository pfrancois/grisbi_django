# -*- coding: utf-8 -*-

#from django.conf import settings  # @Reimport

from django.contrib import messages

from .. import models
from . import import_base
from .. import utils


class Csv_unicode_reader_titre(utils.Csv_unicode_reader):

    """obligatoire :  cpt date titre nombre cours"""

    @property
    def compte(self):
        return utils.to_unicode(self.row['cpt'], 'compte_titre1')

    @property
    def date(self):
        try:
            return utils.to_date(self.row['date'], "%d/%m/%Y")
        except utils.FormatException:
            raise utils.FormatException("erreur de date '%s' à la ligne %s" % (self.row['date'], self.ligne))

    @property
    def titre(self):
        return utils.to_unicode(self.row['titre'])

    @property
    def nombre(self):
        return utils.to_decimal(self.row['nombre'])

    @property
    def cours(self):
        return utils.to_decimal(self.row['cours'])

    @property
    def ligne(self):
        return self.line_num

    @property
    def frais(self):
        return utils.to_decimal(self.row['frais'])

    @property
    def isin(self):
        return utils.to_unicode(self.row['isin'])


# noinspection PyUnresolvedReferences
class Import_csv_ope_titre(import_base.Import_base):
    titre = "import titre csv"
    encoding = "iso-8859-1"
    complexe = False
    reader = Csv_unicode_reader_titre
    extensions = (".csv",)
    type_f = "csv_ope_titres"
    creation_de_compte = False

    def import_file(self, nomfich):
        """renvoi un tableau complet de l'import"""
        self.init_cache()
        self.erreur = list()
        # les moyens par defaut
        retour = False
        verif_format = False
        nb_ope = 0
        try:
            with open(nomfich, 'r', encoding=self.encoding) as f_non_encode:
                fich = self.reader(f_non_encode)
                #---------------------- boucle
                for row in fich:
                    if row.ligne < 1:
                        continue
                    if not verif_format:  # on verifie a la premiere ligne
                        liste_colonnes = ['cpt', 'date', 'titre', 'nombre', 'cours', "frais", "isin"]
                        colonnes_oublies = []
                        for attr in liste_colonnes:
                            if not hasattr(row, attr):
                                colonnes_oublies.append(attr)
                        if len(colonnes_oublies) > 0:
                            raise import_base.ImportException("il manque la/les colonne(s) '%s'" % "','".join(colonnes_oublies))
                        else:
                            verif_format = True
                    ope = dict()
                    ope['ligne'] = row.ligne
                    ope['date'] = row.date
                    ope['compte_id'] = self.comptes.goc(row.compte)
                    ope["titre_id"] = self.titres.goc(nom=row.titre)
                    ope['nombre'] = row.nombre
                    ope['cours'] = row.cours
                    if row.frais:
                        ope['frais'] = row.frais
                    else:
                        ope['frais'] = 0
                    if ope['nombre'] != 0:
                        self.opes.create(ope)
                    else:
                        models.Cours.objects.create(date=ope["date"], titre_id=ope["titre_id"], valeur=ope['cours'])
                        messages.info(self.request, 'cours du titre %s a la date du %s ajoute' % (row.titre, ope["date"]))
                retour = True
                #------------------fin boucle
        except import_base.ImportException as e:
            messages.error(self.request, "attention traitement interrompu parce que %s" % e)
            retour = False
            # gestion des erreurs
        if len(self.erreur) or retour is False:
            for err in self.erreur:
                messages.warning(self.request, err)
            return False
        for ope in self.opes.created_items:
            compte = models.Compte.objects.get(id=ope['compte_id'])
            if compte.type != 't':
                messages.warning(self.request, 'attention, compte non compte_titre %s ligne %s' % (compte.nom, ope['ligne']))
                continue
            titre = models.Titre.objects.get(id=ope['titre_id'])
            nombre = ope['nombre']
            cours = ope['cours']
            if nombre == 0 and cours == 0:
                messages.warning(self.request, 'attention, nombre et cours nul ligne %s' % ope['ligne'])
            if nombre > 0:
                compte.achat(titre=titre, nombre=nombre, prix=cours, date=ope['date'], frais=ope['frais'])
            else:
                compte.vente(titre=titre, nombre=nombre, prix=cours, date=ope['date'], frais=ope['frais'])
            nb_ope += 1
        messages.info(self.request, "%s opés titres crées" % nb_ope)
        if self.titres.nb_created > 0:
            messages.info(self.request, "%s titres crées" % self.titres.nb_created)
        return True
