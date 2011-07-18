# -*- coding: utf-8 -*-
"""
test en rapport avec les titres
"""

from django.test import TestCase
from mysite.gsb.import_gsb import *
import decimal
from django.conf import settings

class titre_test(TestCase):
    def setUp(self):
        self.tiers1=Tiers.objects.create(nom='tiers1')
        self.tiers2=Tiers.objects.create(nom='tiers2')
        self.titre1=Titre.objects.create(nom="t1", isin="1", type='ACT')
        self.titre2=Titre.objects.create(nom="t2", isin="2", type='ACT')
        self.devise1=Titre.objects.create(nom='euro',isin='EUR',type='DEV')
        self.devise2=Titre.objects.create(nom='devise2',isin='USD',type='DEV')
        Cours( valeur=decimal.Decimal('10.00'), titre=self.titre1, date=datetime.date(day=1, month=1, year=2010)).save()
        Cours( valeur=decimal.Decimal('1.00'), titre=self.devise1, date=datetime.date(day=1, month=1, year=2010)).save()
        self.banque1=Banques.objects.create(

    def test_creation_devise(self):
        self.assertEqual(self.devise1.tiers, None)
    def test_creation_titre_tiers(self):
        tiers=self.titre1.tiers
        self.assertNotEqual(tiers, None)
        self.assertEqual(tiers.nom,'titre_ t1')
        self.assertEqual(tiers.notes,"1@ACT")
        self.assertEqual(tiers.is_titre,True)
    def test_last_cours(self):
        self.assertEquals(self.titre1.last_cours_valeur,decimal.Decimal('10.00'))
    def test_nb_devises(self):
        self.assertEqual(Titre.devises().count(),2)

class compte_titretest(TestCase):
    def setUp(self):
        self.devise=Titre(nom='euro',isin='EUR',type='DEV',tiers=None)
        self.devise.save()
        self.tiers_sg=Tiers.objects.create(nom="titre_ SG", notes="123456789@ACT",is_titre=True)
        self.titre_sg=Titre.objects.create(nom="SG", isin="123456789", tiers=self.tiers_sg, type='ACT')
        Cours( valeur=decimal.Decimal('10.00'), titre=self.titre_sg, date=datetime.date(day=1, month=1, year=2010)).save()
        Cours( valeur=decimal.Decimal('1.00'), titre=self.devise, date=datetime.date(day=1, month=1, year=2010)).save()

    def test_1(self):
        devise=self.devise
        titre_sg=self.titre_sg
        c = Compte_titre(nom='test',devise=devise, type='t')
        c.save()
        self.assertEqual(c.nom, u'test')
        c.achat(titre=titre_sg,nombre=20)
        self.assertEqual

class reaffacte_test(TestCase):
    def setUp(self):
        self.tiers1=Tiers.objects.create(nom='tiers1')
        self.tiers2=Tiers.objects.create(nom='tiers2')
        self.titre1=Titre.objects.create(nom="t1", isin="1", type='ACT')
        self.titre2=Titre.objects.create(nom="t2", isin="2", type='ACT')
        self.devise1=Titre(nom='euro',isin='EUR',type='DEV')
        self.devise2=Titre(nom='devise2',isin='USD',type='DEV')

