# -*- coding: utf-8 -*
"""
test models
"""
from __future__ import absolute_import
import os
from .test_base import TestCase
from ..models import Generalite, Compte, Ope, Tiers, Cat, Moyen, Titre, Banque
from ..models import Compte_titre, Virement, Ope_titre, Ib, Exercice, Cours
from ..models import Rapp, Echeance, Gsb_exc, Ex_jumelle_neant
from django.core.exceptions import ValidationError
from django.db import IntegrityError
import datetime
import decimal
from django.conf import settings
from ..utils import strpdate
from operator import attrgetter
from dateutil.relativedelta import relativedelta
from django.db import models
from django.test.client import Client

class test_2(TestCase):
    fixtures = ['test.json', 'auth.json']
    def setUp(self):
        self.client.login(username='admin', password='mdp')

    def test_404(self):
        self.assertEqual(self.client.get('/ope/2200/').status_code, 404)
        self.assertEqual(self.client.get('/gestion_bdd/gsb/ope/49810/').status_code, 404)
    def test_normaux(self):
        self.assertEqual(self.client.get('/').status_code, 200)