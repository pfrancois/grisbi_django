# -*- coding: utf-8 -*-
from __future__ import absolute_import

from gsb import models
from . import utils

import logging
from django.http import HttpResponse
# from django.conf import settings
# pour les vues
import gsb.export_base as ex
from .models import Ope_titre, Compte
from django.core import exceptions as django_exceptions

class Export_view_csv_base(ex.ExportViewBase):
    extension_file = "csv"
    fieldnames = None

    def export_csv_view(self, data, nomfich="export"):
        """machinerie commune aux classes filles"""
        csv_file = ex.Csv_unicode_writer(encoding='iso-8859-15', fieldnames=self.fieldnames)
        csv_file.writeheader()
        csv_file.writerows(data)
        if self.debug:
            return HttpResponse(csv_file.getvalue(), mimetype="text/plain")
        else:
            return HttpResponse(csv_file.getvalue(), content_type='text/csv')


class Export_ope_csv(Export_view_csv_base):
    form_class = ex.Exportform_ope
    model_initial = models.Ope
    nomfich = "export_ope"
    fieldnames = ('id', 'account name', 'date', 'montant', 'r', 'p', 'moyen', 'cat', 'tiers', 'notes', 'projet', 'n chq', 'id jumelle lie', 'has fille', 'num op vent m', 'ope_titre', 'ope_pmv', 'mois')

    def export(self, query):
        """
        fonction principale
        """
        logger = logging.getLogger('gsb.export')
        data = []
        query = query.order_by('date','id').select_related('cat', "compte", "tiers", "ib","rapp","ope","ope_pmv","moyen") 
        liste_ope=query.values_list('id')
        ope_mere=query.filter(mere_id__in=liste_ope).values_list('id',flat=True)
        
        for ope in query:
            # id compte date montant
            # print ope
            ligne = {'id': ope.id, 'account name': ope.compte.nom}
            #date
            ligne['date']=ope.date.strftime('%d/%m/%Y')

            #montant
            montant = "%10.2f" % ope.montant
            montant = montant.replace('.', ',').strip()
            ligne['montant'] = montant
            # rapp
            if ope.rapp is not None:
                ligne['r'] = ope.rapp.nom
            else:
                ligne['r'] = ''
            # pointee
            ligne['p'] = utils.booltostr(ope.pointe)

            # moyen
            try:
                ligne['moyen'] = utils.idtostr(ope.moyen, '', 'nom')
            except django_exceptions.ObjectDoesNotExist:
                ligne['moyen'] = ""
            # cat
            ligne['cat'] = utils.idtostr(ope.cat, "", "nom")
            # tiers
            ligne['tiers'] = utils.idtostr(ope.tiers, '', 'nom')
            ligne['notes'] = ope.notes
            try:
                ligne['projet'] = utils.idtostr(ope.ib, '', 'nom')
            except django_exceptions.ObjectDoesNotExist:
                ligne['projet'] = ""

            # le reste
            ligne['n chq'] = ope.num_cheque
            ligne['id jumelle lie'] = utils.idtostr(ope.jumelle_id, '') 
            ligne['has fille'] = utils.booltostr(ope.id in ope_mere)
            ligne['num op vent m'] = utils.idtostr(ope.mere_id, '')
            if ope.ope is not None:
                ligne['ope_titre'] = ope.ope.id
            else:
                ligne['ope_titre'] = ''
            if ope.ope_pmv is not None:
                ligne['ope_pmv'] = ope.ope_pmv.id
            else:
                ligne['ope_pmv'] = ''
            ligne['mois'] = ope.date.strftime('%m')
            data.append(ligne)

        logger.info('export ope csv')
        return self.export_csv_view(data=data)


class Exportform_cours(ex.Exportform_ope):
    collection = ex.forms.ModelMultipleChoiceField(models.Titre.objects.all(), required=False)
    date_min = ex.forms.DateField(label='date minimum', widget=ex.forms.DateInput)
    date_max = ex.forms.DateField(label='date maximum', widget=ex.forms.DateInput)
    model_initial = models.Cours
    model_collec = models.Titre

    def verif_collec(self, query, ensemble):
        return query.filter(titre__pk__in=ensemble)


class Export_cours_csv(Export_view_csv_base):
    model_initial = models.Cours
    form_class = Exportform_cours
    nomfich = "export_cours"
    fieldnames = ("id", "date", "nom", "isin", "value")

    def export(self, query):
        """
        renvoie l'ensemble des cours.
        @param query: queryset des cours filtre avec les dates
        @return: object httpreponse se composant du fichier csv
        """
        data = []
        for objet in query.order_by('date').select_related('titre'):
            ligne = {'id': objet.titre.isin,
                     'date': objet.date,
                     'nom': objet.titre.nom,
                     'isin': objet.titre.isin,
                     'value': objet.valeur}
            data.append(ligne)
        reponse = self.export_csv_view(data=data, nomfich="export_cours")
        return reponse


class Exportform_Compte_titre(ex.Exportform_ope):
    collection = ex.forms.ModelMultipleChoiceField(Compte.objects.filter(type='t'), required=False)
    date_min = ex.forms.DateField(label='date minimum', widget=ex.forms.DateInput)
    date_max = ex.forms.DateField(label='date maximum', widget=ex.forms.DateInput)
    model_initial = Ope_titre
    model_collec = Compte

    def verif_collec(self, query, ensemble):
        return query.filter(compte__pk__in=ensemble)


class Export_ope_titre_csv(Export_view_csv_base):
    model_initial = models.Ope_titre
    form_class = Exportform_Compte_titre
    nomfich = "export_ope_titre"
    fieldnames = ("id", "date", "compte", "nom", "isin", "sens", "cours", "nombre", "montant")

    def export(self, query):
        """
        renvoie l'ensemble des operations titres.
        @param query: filtre avec les dates
        @return: object httpreposne se composant du fichier csv
        """
        data = []
        for objet in query.order_by('date').select_related('compte', 'titre'):
            ligne = {
                'id': objet.id,
                'date': objet.date,
                'nom': objet.compte.nom,
                'compte': objet.titre.nom,
                'isin': objet.titre.isin}
            if objet.nombre > 0:
                ligne['sens'] = u"achat"
            else:
                ligne['sens'] = u"vente"
            ligne['cours'] = objet.nombre
            ligne['montant'] = objet.invest
            data.append(ligne)
        reponse = self.export_csv_view(data=data, nomfich="export_ope_titre")
        return reponse
