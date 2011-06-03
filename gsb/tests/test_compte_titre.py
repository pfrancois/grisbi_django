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

    def compte_titre_test(self):
        devise=Titre(nom='euro',isin='EUR',type='DEV',tiers=None)
        devise.save()
        Cours( valeur=decimal.Decimal('1.00'), isin=devise, date=datetime.date(day=1, month=1, year=2010)).save()
        c = Compte_titre(nom='test',devise=devise, type='a')
        self.assertEqual(obj.nom, u'premier')
        self.assertEqual(obj.notes, u'')
        self.assertEqual(obj.is_titre, False)

