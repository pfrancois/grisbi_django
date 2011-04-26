# -*- coding: utf-8 -*-
"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
from mysite.gsb.import_gsb import *
import decimal

class SimpleTest(TestCase):
    def setUp(self):
        import_gsb("{}/../test_files/test_original.gsb".format(os.path.dirname(os.path.abspath(__file__))))
        Cours(id=1, valeur=decimal.Decimal('10.00'), isin=Titre.objects.get(id=1),
              date=datetime.date(day=1, month=1, year=2010)).save()

    def test_tiers_properties(self):
        obj = Tiers.objects.get(id=1)
        self.assertEqual(obj.nom, u'premier')
        self.assertEqual(obj.notes, u'')
        self.assertEqual(obj.is_titre, False)

    def test_tiers_count(self):
        self.assertEqual(Tiers.objects.count(), 5)
        self.assertEqual(6, Tiers.objects.all().aggregate(max=models.Max('id'))['max'])

    def test_tiers_is_titre(self):
        self.assertEquals(Tiers.objects.get(id=6).is_titre, True)

    def test_devise_properties(self):
        obj = Devise.objects.get(id=1)
        self.assertEqual(obj.nom, u'Euro')
        self.assertEqual(obj.isocode, u'EUR')
        self.assertEqual(obj.dernier_tx_de_change, 1)
        self.assertEqual(obj.date_dernier_change, datetime.date.today())

    def test_devise_etrangere(self):
        obj = Devise.objects.get(id=2)
        self.assertEqual(obj.nom, u'Rand')
        self.assertEqual(obj.isocode, u'ZAR')
        self.assertEqual(obj.dernier_tx_de_change, decimal.Decimal('10.0'))
        self.assertEqual(obj.date_dernier_change, datetime.date(day=1, month=1, year=2010))

    def test_titre(self):
        obj = Titre.objects.all()[0]
        self.assertEquals(obj.nom, u'SG')
        self.assertEquals(obj.isin, u'FR0000130809')
        self.assertEquals(obj.tiers.id, 6)
        self.assertEquals(obj.type, u'ACT')

    def test_cours(self):
        obj = Cours.objects.get(id=1)
        self.assertEquals(obj.valeur, decimal.Decimal('10.00'))
        self.assertEquals(obj.isin, Titre.objects.get(id=1))
        self.assertEquals(obj.date, datetime.date(day=1, month=1, year=2010))

    def test_banques_properties(self):
        obj = Banque.objects.get(id=1)
        self.assertEqual(obj.nom, u'banque test')
        self.assertEqual(obj.cib, u'30003')
        self.assertEqual(obj.notes, u'voici qq remarques')

    def test_seconde_bq(self):
        self.assertEqual(Banque.objects.get(id=2).cib, u'12345')

    def test_cat(self):
        obj = Cat.objects.get(id=5)
        self.assertEqual(obj.nom, u'Revenus divers')
        self.assertEqual(obj.type, 'r')

    def test_cat_global(self):
        self.assertEqual(Cat.objects.count(), 5)
        self.assertEqual(Cat.objects.all().aggregate(max=models.Max('id'))['max'], 21)

    def test_sous_cat(self):
        obj = Cat.objects.get(id=6)
        self.assertEqual(obj.scat_set.count(), 9)
        self.assertEqual(obj.scat_set.aggregate(max=models.Max('id'))['max'], 9)
        sous = obj.scat_set.get(grisbi_id=1)
        self.assertEqual(sous.nom, u'Bar')
        self.assertEqual(sous.grisbi_id, 1)

    def test_ib(self):
        obj = Ib.objects.get(id=1)
        self.assertEqual(obj.nom, u'imputation_credit')
        self.assertEqual(obj.type, 'r')

    def test_ib_global(self):
        self.assertEqual(Ib.objects.count(), 4)
        self.assertEqual(Ib.objects.all().aggregate(max=models.Max('id'))['max'], 4)

    def test_sous_ib(self):
        obj = Ib.objects.get(id=2)
        self.assertEqual(obj.sib_set.count(), 1)
        self.assertEqual(obj.sib_set.aggregate(max=models.Max('id'))['max'], 1)
        sous = obj.sib_set.get(grisbi_id=1)
        self.assertEqual(sous.nom, u'sous_imputation')
        self.assertEqual(sous.grisbi_id, 1)

    def test_exercice(self):
        obj = Exercice.objects.get(id=5)
        self.assertEqual(obj.date_debut, datetime.date(day=1, month=1, year=2010))
        self.assertEqual(obj.date_fin, datetime.date(day=31, month=12, year=2010))
        self.assertEqual(obj.nom, u'2010')
        self.assertEqual(Exercice.objects.all().aggregate(max=models.Max('id'))['max'], 6)

    def test_compte_properties_cloture(self):
        self.assertEqual(Compte.objects.get(id=1).cloture, True)

    def test_compte_properties_devise_particuliere(self):
        self.assertEqual(Compte.objects.get(id=3).devise.isocode, 'ZAR')

    def test_compte_properties(self):
        obj = Compte.objects.get(id=0)
        self.assertEqual(obj.nom, u'compte bancaire ouvert')
        self.assertEqual(obj.titulaire, '')
        self.assertEqual(obj.type, 'b')
        self.assertIsInstance(obj.devise, Devise)
        self.assertIsInstance(obj.banque, Banque)
        self.assertEqual(obj.guichet, u'12345')
        self.assertEqual(obj.num_compte, u'12345766b76')
        self.assertEqual(obj.cle_compte, 47)
        self.assertEqual(obj.solde_init, 0.0)
        self.assertEqual(obj.solde_mini_voulu, 0.0)
        self.assertEqual(obj.solde_mini_autorise, 0.0)
        self.assertEqual(obj.cloture, False)
        self.assertEqual(obj.notes, '')
        self.assertEqual(obj.moyen_debit_defaut.nom, u'Carte de credit')
        self.assertEqual(obj.moyen_credit_defaut.nom, u'Depot')

    def test_compte_solde(self):
        self.assertEqual(Compte.objects.get(id=0).solde(), decimal.Decimal('-100.92'))

    def test_compte_solde_devise(self):
        self.assertEqual(Compte.objects.get(id=3).solde(), decimal.Decimal('246.0'))
        self.assertEqual(Compte.objects.get(id=3).solde(devise_generale=True), decimal.Decimal('24.6'))

    def test_compte_global(self):
        self.assertEqual(Compte.objects.count(), 7)
        self.assertEqual(6, Compte.objects.all().aggregate(max=models.Max('id'))['max'])

    def test_moyen(self):
        obj = Compte.objects.get(id=0).moyen_set.get(grisbi_id=1)
        self.assertEqual(obj.nom, u'Virement')
        self.assertEqual(obj.signe, 'v')
        self.assertEqual(obj.affiche_numero, True)
        self.assertEqual(obj.num_auto, False)
        self.assertEqual(obj.num_en_cours, 0)

    def test_moyen_avec_numero(self):
        obj = Compte.objects.get(id=0).moyen_set.get(grisbi_id=5)
        self.assertEqual(obj.nom, u'Chèque')
        self.assertEqual(obj.signe, 'd')
        self.assertEqual(obj.affiche_numero, True)
        self.assertEqual(obj.num_auto, True)
        self.assertEqual(obj.num_en_cours, 12345)

    def test_nb_moyens_dans_compte(self):
        self.assertEqual(Compte.objects.get(id=0).moyen_set.count(), 5)

    def test_rapp(self):
        obj = Rapp.objects.get(id=1)
        self.assertEquals(obj.nom, 'CBO1')
        self.assertEquals(obj.compte(), 0)
        self.assertEquals(obj.date, datetime.date(2010, 5, 31))
        self.assertEquals(obj.solde, 0)
        self.assertEquals(obj.ope_set.all().count(), 1)
        self.assertEquals(obj.ope_set.all()[0], Ope.objects.get(id=5))

    def test_ech(self):
        obj = Echeance.objects.get(id=3)
        self.assertEquals(obj.date, datetime.date(2012, 12, 31))
        self.assertEquals(obj.compte.id, 0)
        self.assertEquals(obj.montant, decimal.Decimal('0'))
        self.assertEquals(obj.devise.id, 2)
        self.assertEquals(obj.tiers.id, 4)
        self.assertEquals(obj.cat.id, 6)
        self.assertEquals(obj.scat.grisbi_id, 2)
        self.assertEquals(obj.moyen, 3)
        self.assertEquals(obj.exercice.id, 5)
        self.assertEquals(obj.notes, u"automatique")
        self.assertEquals(obj.inscription_automatique, True)
        self.assertEquals(obj.intervalle, 0)

    def test_ech(self):
        obj = Echeance.objects.get(id=2)
        self.assertEquals(obj.date, datetime.date(2012, 12, 31))
        self.assertEquals(obj.compte.id, 0)
        self.assertEquals(obj.montant, decimal.Decimal('-123'))
        self.assertEquals(obj.devise.id, 2)
        self.assertEquals(obj.tiers.id, 4)
        self.assertEquals(obj.cat.id, 21)
        self.assertEquals(obj.scat.grisbi_id, 6)
        self.assertEquals(obj.moyen.id, 1)
        self.assertEquals(obj.exercice.id, 5)
        self.assertEquals(obj.notes, u"echeance")
        self.assertEquals(obj.inscription_automatique, false)
        self.assertEquals(obj.intervalle, 0)

    def test_ope(self):
        obj=Ope.objects.get(id=1)
        self.assertEquals(obj.compte.id, 0)
        