# -*- coding: utf-8 -*-
from __future__ import absolute_import
from django.test import TestCase as Test_Case_django
from django.test.utils import override_settings
import logging


@override_settings(ID_CPT_M=1)
@override_settings(MD_CREDIT=1)
@override_settings(MD_DEBIT=1)
@override_settings(MD_CREDIT=4)
@override_settings(ID_CAT_COTISATION=3)
@override_settings(ID_TIERS_COTISATION=2)
@override_settings(ID_CAT_PMV=67)
class TestCase(Test_Case_django):
    def setUp(self):
        # supprime l'affichage des probleme de 404
        logger = logging.getLogger('django.request')
        logger.setLevel(logging.ERROR)
        super(TestCase, self).setUp()

    def assertQueryset(self, qs1, list1):
        # compare les id d'un query set avec une liste
        pk = qs1.values_list('pk', flat=True)
        return self.assertEqual(
            sorted(list(pk)),
            sorted(list(list1))
        )
