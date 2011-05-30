# -*- coding: utf-8 -*-
"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
from mysite.gsb.import_gsb import *
import decimal
from django.conf import settings

class compte_titretest(TestCase):
    def setUp(self):
        import_gsb("%s/../test_files/test_original.gsb"%(os.path.dirname(os.path.abspath(__file__))))
        Cours( valeur=decimal.Decimal('10.00'), isin=Titre.objects.get(nom=u'SG'), date=datetime.date(day=1, month=1, year=2010)).save()

    def test_tiers_properties(self):
        obj = Tiers.objects.get(id=1)
        self.assertEqual(obj.nom, u'premier')
        self.assertEqual(obj.notes, u'')
        self.assertEqual(obj.is_titre, False)

