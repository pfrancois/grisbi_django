# -*- coding: utf-8 -*-
"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""
from __future__ import absolute_import
from .test_base import TestCase as Tcd
from ..models import Titre, Cours, Tiers, Banque, Ope, Echeance, Compte, Cat, Ib, Exercice, Moyen, Rapp
from ..io.import_gsb import import_gsb_050
from ..io.import_base import ImportException
import decimal
import datetime
import os
import glob
from django.db import models
#from operator import attrgetter
from django.conf import settings
import os.path
import mock

__all__ = ['Test_import_gsb050', 'Test_import_gsb050_post']


class Test_import_gsb050(Tcd):
    def test_mauvais_format(self):
        self.assertRaises(ImportException, import_gsb_050, os.path.join(settings.PROJECT_PATH, "gsb", "test_files", "mauvais.gsb"), self.request_post('toto'))
        self.assertRaises(ImportException, import_gsb_050, os.path.join(settings.PROJECT_PATH, "gsb", "test_files", "mauvais3.gsb"), self.request_post('toto'))
        for name in glob.glob(os.path.join(settings.PROJECT_PATH, 'upload', 'mauvais*')):
                os.remove(name)


class Test_import_gsb050_post(Tcd):
    @mock.patch('gsb.utils.today')
    def setUp(self, today_mock):
        today_mock.return_value = datetime.date(2013, 1, 1)
        super(Test_import_gsb050_post, self).setUp()
        import_gsb_050("%s/../test_files/test_original.gsb" % (os.path.dirname(os.path.abspath(__file__))), self.request_post('toto'))
        Cours(valeur=decimal.Decimal('10.00'), titre=Titre.objects.get(nom=u'SG'), date=datetime.date(day=1, month=1, year=2010)).save()

    @classmethod
    def teardownClass(cls):
        for name in glob.glob(os.path.join(settings.PROJECT_PATH, 'upload', 'test_original*')):
                os.remove(name)

    def test_tiers_properties(self):
        obj = Tiers.objects.get(id=1)
        self.assertEqual(obj.nom, u'premier')
        self.assertEqual(obj.notes, u'')
        self.assertEqual(obj.is_titre, False)
        self.assertEqual(Tiers.objects.count(), 9)
        self.assertEqual(9, Tiers.objects.all().aggregate(max=models.Max('id'))['max'])
        self.assertQueryset_list(Tiers.objects.all(), [1, 2, 3, 4, 5, 6, 7, 8, 9])
        self.assertQueryset_list(Tiers.objects.filter(is_titre=True).all().order_by('id'), [5, 6, 7, 8, 9])

    @mock.patch('gsb.utils.today')
    def test_titre_normal(self, today_mock):
        today_mock.return_value = datetime.date(2013, 1, 1)
        obj = Titre.objects.get(id=1)
        self.assertEquals(obj.nom, u'SG')
        self.assertEquals(obj.isin, u'FR0000130809')
        self.assertEquals(obj.tiers.id, 5)
        self.assertEquals(obj.tiers.nom, 'titre_ SG')
        self.assertEquals(obj.type, u'ACT')
        obj = Titre.objects.get(id=2)
        self.assertEquals(obj.nom, u'test1')
        self.assertEquals(obj.isin, "ZZ%sN%s" % (datetime.date(2013, 1, 1).strftime('%d%m%Y'), 2))
        self.assertEquals(obj.tiers.id, 6)
        self.assertEquals(obj.type, u'ZZZ')
        obj = Titre.objects.get(id=3)
        self.assertEquals(obj.nom, u'test2')
        self.assertEquals(obj.isin, u'DE0000130809')
        self.assertEquals(obj.tiers.id, 7)
        self.assertEquals(obj.type, u'ZZZ')
        obj = Titre.objects.get(id=4)
        self.assertEquals(obj.nom, u'test3')
        self.assertEquals(obj.isin, "XX%sN%s" % (datetime.date(2013, 1, 1).strftime('%d%m%Y'), 4))
        self.assertEquals(obj.tiers.id, 8)
        self.assertEquals(obj.type, u'ACT')
        obj = Titre.objects.get(id=5)
        self.assertEquals(obj.nom, u'test4')
        self.assertEquals(obj.isin, "XX%sN%s" % (datetime.date(2013, 1, 1).strftime('%d%m%Y'), 5))
        self.assertEquals(obj.tiers.id, 9)
        self.assertEquals(obj.type, u'ZZZ')
        self.assertEquals(Titre.objects.get(isin=u'FR0000130809').nom, u'SG')
        self.assertQueryset_list(Titre.objects.all(), [1, 2, 3, 4, 5])
        obj = Titre.objects.get(isin=u'FR0000130809').cours_set.get(date=datetime.date(day=1, month=1, year=2010))
        self.assertEquals(obj.valeur, decimal.Decimal('10.00'))
        self.assertEquals(obj.titre, Titre.objects.get(id=1))
        self.assertEquals(obj.date, datetime.date(day=1, month=1, year=2010))

    def test_banque(self):
        obj = Banque.objects.get(id=1)
        self.assertEqual(obj.nom, u'banque test')
        self.assertEqual(obj.cib, u'30003')
        self.assertEqual(obj.notes, u'voici qq remarques')
        self.assertEqual(Banque.objects.get(id=2).cib, u'12345')
        self.assertQueryset_list(Banque.objects.all(), [1, 2])

    def test_cat(self):
        obj = Cat.objects.get(id=1)
        self.assertEqual(obj.nom, u'Revenus divers')
        self.assertEqual(obj.type, 'r')
        obj = Cat.objects.get(id=3)
        self.assertEqual(obj.nom, u'Alimentation:Bar')
        self.assertEqual(obj.type, 'd')
        self.assertEqual(Cat.objects.count(), 27)
        self.assertEqual(Cat.objects.all().aggregate(max=models.Max('id'))['max'], 27)

    def test_ib(self):
        obj = Ib.objects.get(id=1)
        self.assertEqual(obj.nom, u'imputation_credit')
        self.assertEqual(obj.type, 'r')
        obj = Ib.objects.get(id=3)
        self.assertEqual(obj.nom, u'imputation_debit:sous_imputation')
        self.assertEqual(obj.type, 'd')
        self.assertEqual(Ib.objects.count(), 6)
        self.assertEqual(Ib.objects.all().aggregate(max=models.Max('id'))['max'], 6)

    def test_exercice(self):
        obj = Exercice.objects.get(id=1)
        self.assertEqual(obj.date_debut, datetime.date(day=1, month=1, year=2010))
        self.assertEqual(obj.date_fin, datetime.date(day=31, month=12, year=2010))
        self.assertEqual(obj.nom, u'2010')
        self.assertEqual(Exercice.objects.count(), 2)
        self.assertEqual(Exercice.objects.all().aggregate(max=models.Max('id'))['max'], 2)

    def test_compte(self):
        self.assertEqual(Compte.objects.get(id=2).ouvert, False)
        obj = Compte.objects.get(id=1)
        self.assertEqual(obj.nom, u'compte bancaire ouvert')
        self.assertEqual(obj.titulaire, 'test')
        self.assertEqual(Compte.objects.get(id=2).titulaire, '')
        self.assertEqual(obj.type, 'b')
        self.assertIsInstance(obj.banque, Banque)
        self.assertEqual(obj.guichet, u'12345')
        self.assertEqual(obj.num_compte, u'12345766b76')
        self.assertEqual(obj.cle_compte, 47)
        self.assertEqual(obj.solde_init, 0.0)
        self.assertEqual(obj.solde_mini_voulu, 0.0)
        self.assertEqual(obj.solde_mini_autorise, 0.0)
        self.assertEqual(obj.ouvert, True)
        self.assertEqual(obj.notes, 'ceci est un commentaire')
        self.assertEqual(Compte.objects.get(id=2).notes, '')
        self.assertEqual(obj.moyen_debit_defaut.nom, u'Carte de credit')
        self.assertEqual(obj.moyen_credit_defaut.nom, u'Depot')
        self.assertEqual(Compte.objects.get(id=1).solde(), decimal.Decimal('-216'))
        self.assertEqual(Compte.objects.count(), 7)
        self.assertEqual(7, Compte.objects.all().aggregate(max=models.Max('id'))['max'])

    def test_moyen(self):
        obj = Moyen.objects.get(id=1)
        self.assertEqual(obj.nom, u'Virement')
        self.assertEqual(obj.type, 'v')

    def test_rapp(self):
        obj = Rapp.objects.get(id=1)
        self.assertEquals(obj.nom, 'CBO1')
        self.assertEquals(obj.compte, 1)
        self.assertEquals(obj.date, datetime.date(2010, 5, 31))
        self.assertEquals(obj.solde, 10)
        self.assertEquals(obj.ope_set.all().count(), 1)
        self.assertEquals(obj.ope_set.all()[0], Ope.objects.get(id=5))
        self.assertEqual(Rapp.objects.all().count(), 1)
        self.assertEqual(Rapp.objects.all().aggregate(max=models.Max('id'))['max'], 1)
        self.assertEqual(Echeance.objects.all().count(), 5)
        self.assertEqual(Echeance.objects.all().aggregate(max=models.Max('id'))['max'], 5)

    def test_ech(self):
        obj = Echeance.objects.get(id=2)
        self.assertEquals(obj.date, datetime.date(2012, 12, 31))
        self.assertEquals(obj.compte.id, 1)
        self.assertEquals(obj.montant, decimal.Decimal('-123'))
        self.assertEquals(obj.notes, u"automatique")
        self.assertEquals(obj.periodicite, 'm')
        self.assertEquals(obj.intervalle, 1)
        obj = Echeance.objects.get(id=5)
        self.assertEquals(obj.compte_virement.id, 4)
        self.assertEquals(obj.moyen_virement.id, 2)
        obj = Echeance.objects.get(id=4)
        self.assertEquals(obj.periodicite[0], 'm')
        self.assertEquals(obj.intervalle, 1)
        obj = Echeance.objects.get(id=4)
        self.assertEquals(obj.date_limite, datetime.date(2013, 1, 1))
        obj = Echeance.objects.get(id=1)
        self.assertEquals(obj.date, datetime.date(2012, 12, 31))
        self.assertEquals(obj.compte.id, 1)
        self.assertEquals(obj.montant, decimal.Decimal('-123'))
        self.assertEquals(obj.tiers.id, 3)
        self.assertEquals(obj.cat.id, 24)
        self.assertEquals(obj.ib, None)
        self.assertEquals(obj.moyen_virement, None)
        self.assertEquals(obj.compte_virement, None)
        self.assertEquals(obj.exercice.id, 1)
        self.assertEquals(obj.notes, u"echeance")
        self.assertEquals(obj.periodicite[0], 'u')

    def test_ope(self):
        self.assertEqual(Ope.objects.all().count(), 13)
        self.assertEqual(Ope.objects.all().aggregate(max=models.Max('id'))['max'], 13)
        obj = Ope.objects.get(id=1)
        self.assertEquals(obj.compte.id, 1)
        self.assertEquals(obj.date, datetime.date(2010, 05, 28))
        self.assertEquals(obj.date_val, None)
        self.assertEquals(obj.montant, decimal.Decimal('-123'))
        self.assertEquals(obj.tiers.id, 1)
        self.assertEquals(obj.cat.id, 4)
        self.assertEquals(obj.notes, u'ope avec type avec numero')
        self.assertEquals(obj.moyen.id, 5)
        self.assertEquals(obj.num_cheque, "12345")
        self.assertEquals(obj.pointe, False)
        self.assertEquals(obj.rapp, None)
        self.assertEquals(obj.exercice.id, 1)
        self.assertEquals(obj.ib.id, 3)
        self.assertEquals(obj.jumelle, None)
        self.assertEquals(obj.mere, None)
        self.assertEquals(Ope.objects.get(id=2).date_val, datetime.date(2010, 05, 31))
        self.assertEquals(Ope.objects.get(id=11).ib, None)
        self.assertEquals(Ope.objects.get(id=6).pointe, True)
        self.assertEquals(Ope.objects.get(id=9).automatique, True)
        self.assertEquals(Ope.objects.get(id=1).piece_comptable, "1")
