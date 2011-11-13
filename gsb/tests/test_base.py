# -*- coding: utf-8 -*-
from __future__ import absolute_import
from django.test import TestCase as Test_Case_django
from django.conf import settings
import decimal
class TestCase(Test_Case_django):
    def setUp(self):
        super(Test_Case_django,self).setUp()
        #gestion des parametres
        self.old_ID_CPT_M = settings.ID_CPT_M
        self.TAUX_VERSEMENT = settings.TAUX_VERSEMENT
        self.ID_CAT_COTISATION = settings.ID_CAT_COTISATION
        self.ID_TIERS_COTISATION = settings.ID_TIERS_COTISATION
        self.ID_CAT_OST = settings.ID_CAT_OST
        self.MD_CREDIT = settings.MD_CREDIT
        self.MD_DEBIT = settings.MD_DEBIT
        settings.ID_CPT_M = 1
        settings.TAUX_VERSEMENT = decimal.Decimal(str(1 / (1 - (0.08 * 0.97)) * (0.08 * 0.97)))
        #id et cat des operation speciales
        settings.ID_CAT_COTISATION = 23
        settings.ID_TIERS_COTISATION = 727
        settings.ID_CAT_OST = 64
        settings.MD_CREDIT = 1
        settings.MD_DEBIT = 2

    def tearDown(self):
        #on remet les settings comme avant
        settings.ID_CPT_M = self.old_ID_CPT_M
        settings.TAUX_VERSEMENT = self.TAUX_VERSEMENT
        settings.ID_CAT_COTISATION = self.ID_CAT_COTISATION
        settings.ID_TIERS_COTISATION = self.ID_TIERS_COTISATION
        settings.ID_CAT_OST = self.ID_CAT_OST
        settings.MD_CREDIT = self.MD_CREDIT
        settings.MD_DEBIT = self.MD_DEBIT
        super(Test_Case_django,self).tearDown()
