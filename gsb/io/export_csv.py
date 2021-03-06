# -*- coding: utf-8 -*-

from django.http import HttpResponse
from .. import models
from .. import utils
# pour les vues
from . import export_base
from ..models import Ope_titre, Compte
from ..utils import Excel_csv
from .. import widgets as gsb_field


class Export_view_csv_base(export_base.ExportViewBase):

    def export(self, query):
        raise NotImplementedError("il faut initialiser")

    extension_file = "csv"
    fieldnames = None
    csv_dialect = None
    class_csv_dialect = Excel_csv

    def export_csv_view(self, data):
        """machinerie commune aux classes filles"""
        csv_file = export_base.Csv_unicode_writer(encoding='iso-8859-15', fieldnames=self.fieldnames, dialect=self.class_csv_dialect)
        csv_file.writeheader()
        csv_file.writerows(data)
        if self.debug:
            return HttpResponse(csv_file.getvalue(), content_type="text/plain")
        else:
            return HttpResponse(csv_file.getvalue(), content_type='text/csv')


class Export_ope_csv(Export_view_csv_base):
    debug = False
    form_class = export_base.Exportform_ope
    model_initial = models.Ope
    nomfich = "export_ope"
    fieldnames = ['id', 'cpt', 'date', 'date_val', "montant", 'r', 'p', "moyen", 'cat', "tiers", "notes", "ib", "num_cheque"]
    titre = "Export des operations au format csv"

    def export(self, query):
        """
        fonction principale
        """
        data = []
        # on exclue les ope mere car cela fait doublon
        query = query.exclude(filles_set__isnull=False)
        query = query.order_by('date', 'id')
        # initialement on elemine la seconde jambe des virement mais en fait il faut pas le faire car sinon pour l'autre jambe c'est pas bon
        # query = query.exclude(jumelle__isnull=False, montant__gte=0)
        query = query.select_related('cat', "compte", "tiers", "ib", "rapp", "moyen", "ope_titre_ost", "jumelle", "mere")
        for ope in query:
                # id compte date montant
            ligne = {'id': ope.id,
                     'cpt': ope.compte.nom,
                     'date': utils.datetostr(ope.date),
                     'date_val': utils.datetostr(ope.date_val, defaut=""),
                     'montant': utils.floattostr(ope.montant, nb_digit=2)}
            # date
            # montant
            # rapp
            if ope.rapp is not None:
                ligne['r'] = ope.rapp.nom
            else:
                if ope.mere is not None and ope.mere.rapp is not None:
                    ligne['r'] = ope.mere.rapp.nom
                else:
                    ligne['r'] = ''
                # pointee
            ligne['p'] = utils.booltostr(ope.pointe)
            # moyen
            ligne['moyen'] = utils.idtostr(ope.moyen, defaut='', membre="nom")
            ligne['cat'] = utils.idtostr(ope.cat, defaut='', membre="nom")
            # tiers
            ligne['tiers'] = utils.idtostr(ope.tiers, defaut='', membre="nom")
            ligne['notes'] = ope.notes
            # phase de verif des notes
            # si c'est une ope jumelle pointe ou rapproche on rajoute une note
            if ope.jumelle is not None:
                if ope.jumelle.rapp is not None:  # jumelle rapprochee
                    if '>R' not in ligne['notes']:
                        ligne['notes'] = ligne['notes'] + '>R' + ope.jumelle.rapp.nom
                if ope.jumelle.pointe:  # jumelle pointee
                    if '>P' not in ligne['notes']:
                        ligne['notes'] += '>P'
                if ope.montant < 0:
                    ligne['tiers'] = "%s => %s" % (ope.compte.nom, ope.jumelle.compte.nom)
                else:
                    ligne['tiers'] = "%s => %s" % (ope.jumelle.compte.nom, ope.compte.nom)
            ligne['ib'] = utils.idtostr(ope.ib, defaut='', membre="nom")
            # le reste
            ligne['num_cheque'] = ope.num_cheque
            data.append(ligne)

        return self.export_csv_view(data=data)


class Exportform_cours(export_base.Exportform_ope):
    collection = export_base.forms.ModelMultipleChoiceField(models.Titre.objects.all(), required=False, label="Titres")
    date_min = gsb_field.DateFieldgsb(label='date minimum', localize=True, )
    date_max = gsb_field.DateFieldgsb(label='date maximum', localize=True, )
    model_initial = models.Cours
    model_collec = models.Titre

    def verif_collec(self, ensemble):
        return self.query.filter(titre__pk__in=ensemble)


class Export_cours_csv(Export_view_csv_base):
    model_initial = models.Cours
    form_class = Exportform_cours
    nomfich = "export_cours"
    fieldnames = ("id", "date", "nom", "isin", "cours")
    titre = "Export des cours pour des titres determinés"

    def export(self, query):
        """
        renvoie l'ensemble des cours.
        @param query: queryset des cours filtre avec les dates
        @return: object httpreponse se composant du fichier csv
        """
        data = []
        for objet in query.order_by('titre__nom', 'date').select_related('titre'):
            ligne = {'id': objet.titre.id,
                     'date': utils.datetostr(objet.date),
                     'nom': objet.titre.nom,
                     'isin': objet.titre.isin,
                     'cours': utils.floattostr(objet.valeur)}
            data.append(ligne)
        reponse = self.export_csv_view(data=data)
        return reponse


class Exportform_Compte_titre(export_base.Exportform_ope):
    collection = export_base.forms.ModelMultipleChoiceField(Compte.objects.filter(type='t'), required=False)
    date_min = gsb_field.DateFieldgsb(label='date minimum', localize=True, )
    date_max = gsb_field.DateFieldgsb(label='date maximum', localize=True, )
    model_initial = Ope_titre
    model_collec = Compte

    def verif_collec(self, ensemble):
        return self.query.filter(compte__pk__in=ensemble)


class Export_ope_titre_csv(Export_view_csv_base):

    """view pour exporter en csv les ope titres"""
    model_initial = models.Ope_titre
    form_class = Exportform_Compte_titre
    nomfich = "export_ope_titre"
    titre = "export des opérations-titres"
    fieldnames = ("id", "date", "compte", "nom", "isin", "sens", "nombre", "cours", "montant_ope")
    # debug = True

    def export(self, query):
        """
        renvoie l'ensemble des operations titres.
        @param query: filtre avec les dates
        @return: object httpreponse se composant du fichier csv
        """
        data = []
        for objet in query.order_by('compte__nom', 'date', 'titre__nom').select_related('compte', 'titre'):
            ligne = {
                'id': objet.id,
                'date': utils.datetostr(objet.date),
                'compte': objet.compte.nom,
                'nom': objet.titre.nom,
                'isin': objet.titre.isin}
            if objet.nombre > 0:
                ligne['sens'] = "achat"
            else:
                ligne['sens'] = "vente"
            ligne['cours'] = utils.floattostr(objet.cours)
            ligne['nombre'] = utils.floattostr(objet.nombre)
            ligne['montant_ope'] = utils.floattostr(objet.cours * objet.nombre)
            data.append(ligne)
        reponse = self.export_csv_view(data=data)
        return reponse
