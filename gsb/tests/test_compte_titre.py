# -*- coding: utf-8 -*-
"""
test en rapport avec les titres
"""
    
from django.test import TestCase
from mysite.gsb.models import * #@UnusedWildImport
#import decimal

class test_titre(TestCase):
    def setUp(self):
        self.tiers1 = Tiers.objects.create(nom='tiers1')
        self.tiers2 = Tiers.objects.create(nom='tiers2')
        self.titre1 = Titre.objects.create(nom="t1", isin="1", type='ACT')
        self.titre2 = Titre.objects.create(nom="t2", isin="2", type='ACT')
        self.devise1 = Titre.objects.create(nom='euro', isin='EUR', type='DEV')
        self.devise2 = Titre.objects.create(nom='devise2', isin='USD', type='DEV')
        Cours(valeur=decimal.Decimal('10.00'), titre=self.titre1, date=datetime.date(day=1, month=1, year=2010)).save()
        Cours(valeur=decimal.Decimal('1.00'), titre=self.devise1, date=datetime.date(day=1, month=1, year=2010)).save()

    def test_creation_devise(self):
        self.assertEqual(self.devise1.tiers, None)
    def test_creation_titre_tiers(self):
        tiers = self.titre1.tiers
        self.assertNotEqual(tiers, None)
        self.assertEqual(tiers.nom, 'titre_ t1')
        self.assertEqual(tiers.notes, "1@ACT")
        self.assertEqual(tiers.is_titre, True)
    def test_last_cours(self):
        self.assertEquals(self.titre1.last_cours, decimal.Decimal('10.00'))
        self.assertEquals(self.titre1.last_cours_date, datetime.date(day=1, month=1, year=2010))
    def test_nb_devises(self):
        self.assertEqual(Titre.devises().count(), 2)

class compte_titretest(TestCase):
    def setUp(self):
        self.tiers1 = Tiers.objects.create(nom='tiers1')
        self.tiers2 = Tiers.objects.create(nom='tiers2')
        self.titre1 = Titre.objects.create(nom="t1", isin="1", type='ACT')
        self.titre2 = Titre.objects.create(nom="t2", isin="2", type='ACT')
        self.devise1 = Titre.objects.create(nom='euro', isin='EUR', type='DEV')

    def test_1(self):
        devise = self.devise1
        titre_sg = self.titre1
        c = Compte_titre(nom='test', devise=devise, type='t')
        c.save()
        self.assertEqual(c.nom, u'test')
        c.achat(titre=titre_sg, nombre=20)

