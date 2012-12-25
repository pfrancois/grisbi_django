# -*- coding: utf-8
from __future__ import absolute_import
from django.contrib.formtools.preview import FormPreview
# from mysite.gsb.models import Tiers, Titre, Cat, Ope, Banque, Cours, Ib, Exercice, Rapp, Moyen, Echeance,  Ope_titre, Compte
from django.http import HttpResponseRedirect


class SomeModelFormPreview(FormPreview):
    form_template = "form/form.html"
    preview_template = "form/preview.html"

    def done(self, request, cleaned_data):  # @UnusedVariable
        return  HttpResponseRedirect('/testform')
