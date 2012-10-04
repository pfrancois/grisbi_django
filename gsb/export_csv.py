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


from django.core.exceptions import ObjectDoesNotExist

class Export_view_csv_base(ex.ExportViewBase):
    model_initial = None
    model_collec = None
    nom_collec_form = None
    form_class = None

    def export_csv_view(self,data,nomfich="export",debug=False):
        csv_file = ex.UnicodeWriter( encoding='iso-8859-15')
        for ligne in data:
            csv_file.writerow(ligne)
        reponse = HttpResponse(csv_file.getvalue(), mimetype="text/plain")
        if not debug:
            reponse["Cache-Control"] = "no-cache, must-revalidate"
            reponse["Content-Disposition"] = "attachment; filename=%s_%s.csv" % (nomfich,
                                                                                 time.strftime("%d_%m_%Y-%H_%M_%S",
                                                                                               time.localtime()
                                                                                              )
                                                                                 )
        return reponse

    def form_valid(self, form):
        """si le form est valid"""
        data = form.cleaned_data
        ensemble = [objet.id for objet in data[self.nom_collec_form]]
        query = self.model_initial.objects.filter( date__gte=data['date_min'], date__lte=data['date_max'])
        if ensemble == [] or len(ensemble) == self.model_collec.objects.all().count():
            extra=None
        else:
            extra=ensemble
        if query.count() > 0:#si des operations existent
            reponse = self.export(query=query,extra=extra)#dans ce cas la on appelle la fonction d'export
            return reponse
        else:
            ex.messages.error(self.request, u"attention pas d'opérations pour la selection demandée")
            return self.render_to_response({'form':form, })


class Exportform_ope(ex.gsb_forms.Baseform):
    compte = ex.forms.ModelMultipleChoiceField(models.Compte.objects.all(), required=False)
    date_min = ex.forms.DateField(label='date minimum', widget=ex.forms.DateInput)
    date_max = ex.forms.DateField(label='date maximum', widget=ex.forms.DateInput)

class Export_ope_csv(Export_view_csv_base):
    form_class = Exportform_ope
    model_initial = models.Ope
    model_collec = models.Compte
    nom_collec_form = 'compte'
    def export(self, query=None,extra=None):
        """
        fonction principale
        """
        logger = logging.getLogger('gsb.export')
        data=[(u'id;account name;date;montant;p;m;moyen;cat;tiers;notes;projet;n chq;id jumelle lie;fille;num op vent m;mois'.split(';')),]
        if query:
            opes = query.order_by('date').select_related('cat', "compte", "tiers", "ib")
        else:
            opes = models.Ope.objects.all().order_by('date').select_related('cat', "compte", "tiers", "ib").filter(filles_set__isnull=True)
        for ope in opes:
            ligne = [ope.id, ope.compte.nom, fmt.date(ope.date), fmt.float(ope.montant)]
            if ope.rapp is None:
                ligne.append(0)
            else:
                ligne.append(1)
            ligne.append(fmt.bool(ope.pointe))
            try:
                ligne.append(fmt.str(ope.moyen, '', 'nom'))
            except ObjectDoesNotExist:
                ligne.append("")
            try:
                cat_g = fmt.str(ope.cat, "", "nom").split(":")
                if cat_g[0]:
                    ligne.append("(%s)%s" % (fmt.str(ope.cat, "", "type"), cat_g[0].strip()))
                else:
                    ligne.append("")
            except ObjectDoesNotExist:
                ligne.append("")
            ligne.append(fmt.str(ope.tiers, '','nom'))
            ligne.append(ope.notes)
            try:
                ligne.append(fmt.str(ope.ib, '', 'nom'))
            except ObjectDoesNotExist:
                ligne.append("")
            ligne.append(ope.num_cheque)
            ligne.append(fmt.str(ope.jumelle, ''))
            ligne.append(fmt.bool(ope.mere))
            ligne.append(fmt.str(ope.mere, ''))
            ligne.append(ope.date.strftime('%Y_%m'))
            data.append(ligne)
        logger.info('export ope csv')
        return self.export_csv_view(data=data,nomfich="export_ope")

class Exportform_cours(ex.gsb_forms.Baseform):
    titre = ex.forms.ModelMultipleChoiceField(models.Titre.objects.all(), required=False)
    date_min = ex.forms.DateField(label='date minimum', widget=ex.forms.DateInput)
    date_max = ex.forms.DateField(label='date maximum', widget=ex.forms.DateInput)


class Export_cours_csv(Export_view_csv_base):
    model_initial = models.Cours
    model_collec = models.Titre
    nom_collec_form = 'titre'
    form_class = Exportform_cours

    def export(self, query=None,extra=None):
        """
        renvoie l'ensemble des cours.
        @param query: queryset des cours filtre avec les dates
        @param extra liste des titre a filtrer
        @return: object httpreposne se composant du fichier csv
        """
        data=[["id","date","nom","value"]]
        if extra is not None:
            query = self.model_initial.objects.filter(titre__pk__in=extra)
        for objet in query.select_related('titre'):
            ligne=[objet.titre.isin,objet.date,objet.titre.nom,objet.valeur]
            data.append(ligne)
        reponse = self.export_csv_view(data=data,nomfich="export_cours",debug=True)
        return reponse

class Exportform_Compte_titre(ex.gsb_forms.Baseform):
    compte_titre = ex.forms.ModelMultipleChoiceField(models.Compte_titre.objects.all(), required=False)
    date_min = ex.forms.DateField(label='date minimum', widget=ex.forms.DateInput)
    date_max = ex.forms.DateField(label='date maximum', widget=ex.forms.DateInput)


class Export_ope_titre_csv(Export_view_csv_base):
    model_initial = models.Ope_titre
    form_class = Exportform_Compte_titre
    nom_collec_form = 'compte_titre'
    model_collec = models.Compte_titre

    def export(self, query=None,extra=None):
        """
        renvoie l'ensemble des operations titres.
        @param query: filtre avec les dates
        @param extra: liste des compte titre a filtrer
        @return: object httpreposne se composant du fichier csv
        """
        if extra is not None:
            query = self.model_initial.objects.filter(compte_titre__pk__in=extra)

        data=[["id","date","nom","value"]]
        for objet in query.select_related('compte','titre'):
            ligne=[objet.id,objet.date,objet.compte.nom,objet.titre.nom,objet.titre.isin]
            if objet.nombre>0:
                ligne.append("achat")
            else:
                ligne.append("vente")
            ligne.append(objet.nombre)
            ligne.append(objet.invest)
            data.append(ligne)
        reponse = self.export_csv_view(data=data,nomfich="export_ope_titre")
        return reponse

