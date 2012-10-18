# -*- coding: utf-8 -*-
from __future__ import absolute_import

from gsb import models
from .utils import Format as fmt
import time
#from .utils import strpdate

import logging
from django.http import HttpResponse
#from django.conf import settings
#pour les vues
import gsb.export_base as ex

from django.core import exceptions as django_exceptions

class Export_view_csv_base(ex.ExportViewBase):
    extension_file = "csv"

    def export_csv_view(self, data, nomfich="export", debug=False):
        """machinerie commune aux classes filles"""
        csv_file = ex.Csv_unicode_writer(encoding='iso-8859-15')
        csv_file.writerows(data)
        if debug:
            reponse = HttpResponse(csv_file.getvalue(), mimetype="text/plain")
        else:
            reponse = HttpResponse(csv_file.getvalue(), content_type='text/csv')
            reponse["Cache-Control"] = "no-cache, must-revalidate"
            reponse['Pragma']="public"
            reponse["Content-Disposition"] = "attachment; filename=%s_%s.csv" % (nomfich,
                                                                     time.strftime("%d_%m_%Y-%H_%M_%S",
                                                                                   time.localtime()
                                                                     )
                    )

        return reponse



class Export_ope_csv(Export_view_csv_base):
    form_class = ex.Exportform_ope
    model_initial = models.Ope
    nomfich = "export_ope"

    def export(self, query):
        """
        fonction principale
        """
        logger = logging.getLogger('gsb.export')
        data = [(
                u'id;account name;date;montant;p;m;moyen;cat;tiers;notes;projet;n chq;id jumelle lie;fille;num op vent m;mois'.split(
                    ';')), ]
        query = query.order_by('date').filter(mere__isnull=True).select_related('cat', "compte", "tiers",
                                                                                "ib")#on enleve les ope mere
        for ope in query:
            #id compte date montant
            ligne = [ope.id, ope.compte.nom, fmt.date(ope.date), fmt.float(ope.montant)]
            #rapp
            if ope.rapp is None:
                ligne.append(0)
            else:
                ligne.append(1)
            #pointee
            ligne.append(fmt.bool(ope.pointe))
            #moyen
            try:
                ligne.append(fmt.str(ope.moyen, '', 'nom'))
            except django_exceptions.ObjectDoesNotExist:
                ligne.append("")
            #cat
            try:
                cat_g = fmt.str(ope.cat, "", "nom").split(":")
                if cat_g[0]:
                    ligne.append("(%s)%s" % (fmt.str(ope.cat, "", "type"), cat_g[0].strip()))
                else:
                    ligne.append("")
            except django_exceptions.ObjectDoesNotExist:
                ligne.append("")
            #tiers
            ligne.append(fmt.str(ope.tiers, '', 'nom'))
            ligne.append(ope.notes)
            try:
                ligne.append(fmt.str(ope.ib, '', 'nom'))
            except django_exceptions.ObjectDoesNotExist:
                ligne.append("")
            #le reste
            ligne.append(ope.num_cheque)
            ligne.append(fmt.str(ope.jumelle, ''))
            ligne.append(fmt.bool(ope.mere))
            ligne.append(fmt.str(ope.mere, ''))
            ligne.append(ope.date.strftime('%Y_%m'))
            data.append(ligne)
        logger.info('export ope csv')
        return self.export_csv_view(data=data,debug=True)


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

    def export(self, query):
        """
        renvoie l'ensemble des cours.
        @param query: queryset des cours filtre avec les dates
        @return: object httpreponse se composant du fichier csv
        """
        data = [["id", "date", "nom", "isin", "value"]]
        for objet in query.order_by('date').select_related('titre'):
            ligne = [objet.titre.isin, objet.date, objet.titre.nom, objet.titre.isin, objet.valeur]
            data.append(ligne)
        reponse = self.export_csv_view(data=data, nomfich="export_cours")
        return reponse


class Exportform_Compte_titre(ex.Exportform_ope):
    collection = ex.forms.ModelMultipleChoiceField(models.Compte_titre.objects.all(), required=False)
    date_min = ex.forms.DateField(label='date minimum', widget=ex.forms.DateInput)
    date_max = ex.forms.DateField(label='date maximum', widget=ex.forms.DateInput)
    model_initial = models.Ope_titre
    model_collec = models.Compte_titre

    def verif_collec(self, query, ensemble):
        return query.filter(compte__pk__in=ensemble)


class Export_ope_titre_csv(Export_view_csv_base):
    model_initial = models.Ope_titre
    form_class = Exportform_Compte_titre
    nomfich = "export_ope_titre"

    def export(self, query):
        """
        renvoie l'ensemble des operations titres.
        @param query: filtre avec les dates
        @return: object httpreposne se composant du fichier csv
        """
        data = [["id", "date", "compte", "nom", "isin", "sens", "cours", "nombre", "montant"]]
        for objet in query.order_by('date').select_related('compte', 'titre'):
            ligne = [objet.id, objet.date, objet.compte.nom, objet.titre.nom, objet.titre.isin]
            if objet.nombre > 0:
                ligne.append(u"achat")
            else:
                ligne.append(u"vente")
            ligne.append(objet.nombre)
            ligne.append(objet.invest)
            data.append(ligne)
        reponse = self.export_csv_view(data=data, nomfich="export_ope_titre")
        return reponse
