# -*- coding: utf-8 -*-
"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
import mysite.gsb.models as models_gsb
from mysite.gsb.import_gsb import * #@UnusedWildImport
import decimal, datetime #@Reimport
from django.db import models
import os.path #@Reimport



class importtest(TestCase):
    def setUp(self):
        logger.setLevel(40)#change le niveau de log (10 = debug, 20=info)
        import_gsb("%s/../test_files/test_original.gsb" % (os.path.dirname(os.path.abspath(__file__))))
        models_gsb.Cours(valeur=decimal.Decimal('10.00'), titre=Titre.objects.get(nom=u'SG'), date=datetime.date(day=1, month=1, year=2010)).save()
        logger.setLevel(30)#change le niveau de log (10 = debug, 20=info)


    def test_tiers_properties(self):
        obj = Tiers.objects.get(id=1)
        self.assertEqual(obj.nom, u'premier')
        self.assertEqual(obj.notes, u'')
        self.assertEqual(obj.is_titre, False)

    def test_tiers_count(self):
        self.assertEqual(Tiers.objects.count(), 5)
        self.assertEqual(5, Tiers.objects.all().aggregate(max=models.Max('id'))['max'])

    def test_tiers_is_titre(self):
        self.assertEquals(Tiers.objects.get(id=5).is_titre, True)

    def test_titre_normal(self):
        obj = Titre.objects.get(id=1)
        self.assertEquals(obj.nom, u'SG')
        self.assertEquals(obj.isin, u'FR0000130809')
        self.assertEquals(obj.tiers.id, 5)
        self.assertEquals(obj.type, u'ACT')

    def test_get_titre_normal(self):
        self.assertEquals(Titre.objects.get(isin=u'FR0000130809').nom, u'SG')

    def test_titre_devise(self):
        obj = Titre.objects.get(id=2)
        self.assertEquals(obj.nom, u'Euro')
        self.assertEquals(obj.isin, u'EUR')
        self.assertEquals(obj.tiers, None)
        self.assertEquals(obj.type, u'DEV')

    def test_get_titre_devise(self):
        self.assertEquals(Titre.objects.get(isin=u'ZAR').nom, u'Rand')

    def test_titre_count(self):
        self.assertEqual(Titre.objects.count(), 3)

    def test_cours_sg(self):
        obj = Titre.objects.get(isin=u'FR0000130809').cours_set.get(date=datetime.date(day=1, month=1, year=2010))
        self.assertEquals(obj.valeur, decimal.Decimal('10.00'))
        self.assertEquals(obj.titre, Titre.objects.get(id=1))
        self.assertEquals(obj.date, datetime.date(day=1, month=1, year=2010))

    def test_cours_zar(self):
        obj = Titre.objects.get(isin=u'ZAR').cours_set.get(date=datetime.date(day=1, month=1, year=2010))
        self.assertEquals(obj.valeur, decimal.Decimal('10'))
        self.assertEquals(obj.titre, Titre.objects.get(id=3))
        self.assertEquals(obj.date, datetime.date(day=1, month=1, year=2010))

    def test_banques_properties(self):
        obj = Banque.objects.get(id=1)
        self.assertEqual(obj.nom, u'banque test')
        self.assertEqual(obj.cib, u'30003')
        self.assertEqual(obj.notes, u'voici qq remarques')

    def test_seconde_bq(self):
        self.assertEqual(Banque.objects.get(id=2).cib, u'12345')

    def test_bq_count(self):
        self.assertEqual(Banque.objects.count(), 2)
        self.assertEqual(2, Banque.objects.all().aggregate(max=models.Max('id'))['max'])

    def test_cat(self):
        obj = Cat.objects.get(id=1)
        self.assertEqual(obj.nom, u'Revenus divers :')
        self.assertEqual(obj.type, 'r')

    def test_cat2(self):
        obj = Cat.objects.get(id=3)
        self.assertEqual(obj.nom, u'Alimentation : Bar')
        self.assertEqual(obj.type, 'd')

    def test_cat_global(self):
        self.assertEqual(Cat.objects.count(), 27)
        self.assertEqual(Cat.objects.all().aggregate(max=models.Max('id'))['max'], 27)

    def test_ib(self):
        obj = Ib.objects.get(id=1)
        self.assertEqual(obj.nom, u'imputation_credit:')
        self.assertEqual(obj.type, 'r')

    def test_ib2(self):
        obj = Ib.objects.get(id=3)
        self.assertEqual(obj.nom, u'imputation_debit:sous_imputation')
        self.assertEqual(obj.type, 'd')

    def test_ib_global(self):
        self.assertEqual(Ib.objects.count(), 6)
        self.assertEqual(Ib.objects.all().aggregate(max=models.Max('id'))['max'], 6)

    def test_exercice(self):
        obj = Exercice.objects.get(id=1)
        self.assertEqual(obj.date_debut, datetime.date(day=1, month=1, year=2010))
        self.assertEqual(obj.date_fin, datetime.date(day=31, month=12, year=2010))
        self.assertEqual(obj.nom, u'2010')
        self.assertEqual(Exercice.objects.count(), 2)
        self.assertEqual(Exercice.objects.all().aggregate(max=models.Max('id'))['max'], 2)

    def test_compte_properties_cloture(self):
        self.assertEqual(Compte.objects.get(id=2).ouvert, False)

    def test_compte_properties_devise_particuliere(self):
        self.assertEqual(Compte.objects.get(id=4).devise.isin, 'ZAR')

    def test_compte_properties(self):
        obj = Compte.objects.get(id=1)
        self.assertEqual(obj.nom, u'compte bancaire ouvert')
        self.assertEqual(obj.titulaire, '')
        self.assertEqual(obj.type, 'b')
        self.assertIsInstance(obj.devise, Titre)
        self.assertIsInstance(obj.banque, Banque)
        self.assertEqual(obj.guichet, u'12345')
        self.assertEqual(obj.num_compte, u'12345766b76')
        self.assertEqual(obj.cle_compte, 47)
        self.assertEqual(obj.solde_init, 0.0)
        self.assertEqual(obj.solde_mini_voulu, 0.0)
        self.assertEqual(obj.solde_mini_autorise, 0.0)
        self.assertEqual(obj.ouvert, True)
        self.assertEqual(obj.notes, '')
        self.assertEqual(obj.moyen_debit_defaut.nom, u'Carte de credit')
        self.assertEqual(obj.moyen_credit_defaut.nom, u'Depot')

    def test_compte_solde(self):
        self.assertEqual(Compte.objects.get(id=1).solde(), decimal.Decimal('-100.92'))

    def test_compte_solde_devise(self):
        self.assertEqual(Compte.objects.get(id=4).solde(), decimal.Decimal('246.0'))
        self.assertEqual(Compte.objects.get(id=4).solde(devise_generale=True), decimal.Decimal('24.6'))

    def test_compte_global(self):
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
        self.assertEquals(obj.solde(), 10)
        self.assertEquals(obj.ope_set.all().count(), 1)
        self.assertEquals(obj.ope_set.all()[0], Ope.objects.get(id=5))

    def test_nb_rapp(self):
        self.assertEqual(Rapp.objects.all().count(), 1)
        self.assertEqual(Rapp.objects.all().aggregate(max=models.Max('id'))['max'], 1)

    def test_nb_ech(self):
        self.assertEqual(Echeance.objects.all().count(), 5)
        self.assertEqual(Echeance.objects.all().aggregate(max=models.Max('id'))['max'], 5)

    def test_ech_automatique(self):
        obj = Echeance.objects.get(id=2)
        self.assertEquals(obj.date, datetime.date(2012, 12, 31))
        self.assertEquals(obj.compte.id, 1)
        self.assertEquals(obj.montant, decimal.Decimal('-123'))
        self.assertEquals(obj.notes, u"automatique")
        self.assertEquals(obj.inscription_automatique, True)
        self.assertEquals(obj.periodicite, 'm')

    def test_ech_virement(self):
        obj = Echeance.objects.get(id=5)
        self.assertEquals(obj.compte_virement.id, 4)
        self.assertEquals(obj.moyen_virement.id, 2)

    def test_ech_period_perso(self):
        obj = Echeance.objects.get(id=4)
        self.assertEquals(obj.periodicite[0], 'p')
        self.assertEquals(obj.periode_perso[0], 'm')
        self.assertEquals(obj.intervalle, 1)

    def test_ech_date_limite(self):
        obj = Echeance.objects.get(id=4)
        self.assertEquals(obj.date_limite, datetime.date(2013, 1, 1))

    def test_ech_standart(self):
        obj = Echeance.objects.get(id=1)
        self.assertEquals(obj.date, datetime.date(2012, 12, 31))
        self.assertEquals(obj.compte.id, 1)
        self.assertEquals(obj.montant, decimal.Decimal('-123'))
        self.assertEquals(obj.devise.id, 2)
        self.assertEquals(obj.tiers.id, 3)
        self.assertEquals(obj.cat.id, 24)
        self.assertEquals(obj.ib, None)
        self.assertEquals(obj.moyen_virement, None)
        self.assertEquals(obj.compte_virement, None)
        self.assertEquals(obj.exercice.id, 1)
        self.assertEquals(obj.notes, u"echeance")
        self.assertEquals(obj.inscription_automatique, False)
        self.assertEquals(obj.periodicite[0], 'u')

    def test_generalites(self):
        obj = Generalite.gen()
        self.assertIsInstance(obj, Generalite)
        self.assertEquals(obj.titre, 'tiitre du fichier')
        self.assertEquals(obj.utilise_exercices, True)
        self.assertEquals(obj.utilise_ib, True)
        self.assertEquals(obj.utilise_pc, True)

    def test_nb_ope(self):
        self.assertEqual(Ope.objects.all().count(), 13)
        self.assertEqual(Ope.objects.all().aggregate(max=models.Max('id'))['max'], 13)

    def test_ope(self):
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

    def test_ope_date_valeur(self):
        self.assertEquals(Ope.objects.get(id=2).date_val, datetime.date(2010, 05, 31))

    def test_ope_devise(self):
        self.assertEquals(Ope.objects.get(id=8).compte.devise.id, 2)

    def test_ope_virement_etranger(self):
        self.assertEquals(Ope.objects.get(id=8).montant, decimal.Decimal('-7.92'))
        self.assertEquals(Ope.objects.get(id=13).montant, decimal.Decimal('123'))
        self.assertEquals(Ope.objects.get(id=13).notes, u'virement en zar')
        self.assertEquals(Ope.objects.get(id=13).compte.devise.isin, 'ZAR')
        self.assertEquals(Ope.objects.get(id=13).jumelle.compte.devise.isin, 'EUR')
        self.assertEquals(Ope.objects.get(id=13).jumelle.id, 8)
        self.assertEquals(Ope.objects.get(id=13).cat, None)

    def test_ope_ib_none(self):
        self.assertEquals(Ope.objects.get(id=11).ib, None)

    def test_ope_pointee(self):
        self.assertEquals(Ope.objects.get(id=6).pointe, True)

    def test_ope_auto(self):
        self.assertEquals(Ope.objects.get(id=9).automatique, True)

    def test_ope_pc(self):
        self.assertEquals(Ope.objects.get(id=1).piece_comptable, "1")
