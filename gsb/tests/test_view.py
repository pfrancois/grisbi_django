# -*- coding: utf-8 -*
"""
test models
"""
from __future__ import absolute_import
import os
from .test_base import TestCase
from ..models import Compte, Ope, Tiers, Cat, Moyen, Titre, Banque
from ..models import Compte_titre, Virement, Ope_titre, Ib, Exercice, Cours
from ..models import Rapp, Echeance, Gsb_exc, Ex_jumelle_neant
from django.core.exceptions import ValidationError
from django.db import IntegrityError
import datetime
import decimal
from django.conf import settings
from ..utils import strpdate
from gsb import forms as gsb_forms
from operator import attrgetter
from dateutil.relativedelta import relativedelta
from django.db import models
from django.test.client import Client

class test_views(TestCase):
    fixtures = ['test.json', 'auth.json']
    def setUp(self):
        self.client.login(username='admin', password='mdp')

    def test_404(self):
        self.assertEqual(self.client.get('/ope/2200/').status_code, 404)
        self.assertEqual(self.client.get('/gestion_bdd/gsb/ope/49810/').status_code, 404)
    def test_normaux(self):
        self.assertEqual(self.client.get('/').status_code, 200)

    def test_form_ope_normal(self):
        #self.client.post(path="/ope/15/", data=, follow=True)
        self.assertEqual(self.client.get('/ope/1/').status_code, 200)
        form_data = { 'compte': "1",
                      'date': "02/09/2012",
                      'date_val': "",
                      'montant': decimal.Decimal(24),
                      'tiers':"1" ,
                      'cat': "3",
                      "notes": "",
                      'moyen': "1",
                      "num_cheque": "",
                      'rapp': "",
                      "exercice": "",
                      "ib": "",
                      "piece_comptable": "",
                      "nouveau_tiers": "",
                      "operation_mere": "",
                      }
        form = gsb_forms.OperationForm(data=form_data,initial=form_data)
        r=form.is_valid()
        self.assertTrue(r)
        r=form.cleaned_data['montant']
        self.assertEqual(r, decimal.Decimal(-24))
    def test_form_ope_clean(self):
        """pas de tiers  ni de nouveau tiers"""
        form_data = { 'compte': "1",
                      'date': "02/09/2012",
                      'date_val': "",
                      'montant': "24",
                      'tiers':"" ,
                      'cat': "3",
                      "notes": "",
                      'moyen': "1",
                      "num_cheque": "",
                      'rapp': "",
                      "exercice": "",
                      "ib": "",
                      "piece_comptable": "",
                      "nouveau_tiers": "",
                      "operation_mere": "",
                      }
        form = gsb_forms.OperationForm(data=form_data)
        self.assertEqual(form.is_valid(), False)
        form.is_valid()
        self.assertEqual(form._errors, {'nouveau_tiers': [u'si vous ne choisissez pas un tiers, vous devez taper le nom du nouveau'], 'tiers': [u"si vous ne choisissez pas un tiers, vous devez taper le nom du nouveau dans le champs 'nouveau tiers'"]})
