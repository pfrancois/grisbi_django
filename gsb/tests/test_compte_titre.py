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
        self.devise=Titre(nom='euro',isin='EUR',type='DEV',tiers=None)
        self.devise.save()
        self.tiers_sg=Tiers.objects.create(nom="titre_ SG", notes="123456789@ACT",is_titre=True)
        self.titre_sg=Titre.objects.create(nom="SG", isin="123456789", tiers=self.tiers_sg, type='ACT')
        Cours( valeur=decimal.Decimal('10.00'), titre=self.titre_sg, date=datetime.date(day=1, month=1, year=2010)).save()
        Cours( valeur=decimal.Decimal('1.00'), titre=self.devise, date=datetime.date(day=1, month=1, year=2010)).save()
        Generalite(devise_generale=self.devise).save()

    def test_1(self):
        devise=self.devise
        titre_sg=self.titre_sg
        c = Compte_titre(nom='test',devise=devise, type='a')
        c.save()
        self.assertEqual(c.nom, u'test')
        c.achat(titre=titre_sg,nombre=20)
        self.assertEqual
