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
        devise=Titre(nom='euro',isin='EUR',type='DEV',tiers=None)
        devise.save()
        tiers_SG=Tiers.objects.create(nom="SG", notes="123456789@ACT",is_titre=True)
        titre_SG=Titre.objects.create(nom="SG", isin="123456789", tiers=tiers_sg, type='ACT')
        Cours( valeur=decimal.Decimal('10.00'), isin=titre_SG, date=datetime.date(day=1, month=1, year=2010)).save()
        Cours( valeur=decimal.Decimal('1.00'), isin=devise, date=datetime.date(day=1, month=1, year=2010)).save()
        Generalite(devise_generale=devise).save()

    def compte_titre_test(self):
        c = Compte_titre(nom='test',devise=devise, type='a')
        c.save()
        self.assertEqual(obj.nom, u'test')