# -*- coding: utf-8 -*-
"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
from django.db import models
import datetime, time
from mysite.gsb.import_gsb import *

class SimpleTest(TestCase):
    def setUp(self):
        import_gsb("{}/fichier_test.gsb".format(os.path.dirname(os.path.abspath(__file__))))
    def test_compte_properties_cloture(self):
        self.assertEqual(Compte.objects.get(id=1).cloture,True)
    def test_compte_properties_devise_particuliere(self):
        self.assertEqual(Compte.objects.get(id=0).devise.isocode,'ZAR')
    def test_compte_properties(self):
        obj=Compte.objects.get(id=0)
        self.assertEqual(obj.nom,u'compte bancaire ouvert')
        self.assertEqual(obj.titulaire,'')
        self.assertEqual(obj.type,'b')
        self.assertIsInstance(obj.devise,Devise)
        self.assertIsInstance(obj.banque,Banque)
        self.assertEqual(obj.guichet,u'12345')
        self.assertEqual(obj.num_compte,u'12345766b76')
        self.assertEqual(obj.cle_compte,47)
        self.assertEqual(obj.solde_init,0.0)
        self.assertEqual(obj.solde_mini_voulu,0.0)
        self.assertEqual(obj.solde_mini_autorise,0.0)
        self.assertEqual(obj.cloture,False)
        self.assertEqual(obj.notes,'')
        self.assertEqual(obj.moyen_credit_defaut.nom,u'Carte de credit')
        self.assertEqual(obj.moyen_debit_defaut.nom,u'Depot')
    def test_compte_solde(self):
        self.assertEqual(Compte.objects.get(id=2).solde(),-94.2)
    def test_compte_solde_devise(self):
        self.assertEqual(Compte.objects.get(id=3).solde(),246.0)
        self.assertEqual(Compte.objects.get(id=3).solde(devise_generale=True),24.6)
    def test_compte_global(self):
        self.assertEqual(Compte.objects.count(),7)
        self.assertEqual(6,Compte.objects.all().aggregate(max=models.Max('id'))['max'])
    def test_tiers_properties(self):
        obj=Tiers.objects.get(id=1)
        self.assertEqual(obj.nom,u'premier')
        self.assertEqual(obj.notes,u'')
        self.assertEqual(obj.is_titre,False)
    def test_tiers_count(self):
        self.assertEqual(Tiers.objects.count(),5)
        self.assertEqual(5,Tiers.objects.all().aggregate(max=models.Max('id'))['max'])  
    def test_devise_properties(self):
        obj=Devise.objects.get(id=0)
        self.assertEqual(obj.nom,u'Euro')
        self.assertEqual(obj.isocode,u'EUR')
        self.assertEqual(obj.dernier_tx_de_change,1)
        self.assertEqual(obj.date_dernier_change,None)
    def test_devise_etrangere(self):
        obj=Devise.objects.get(id=1)
        self.assertEqual(obj.nom,u'Rand')
        self.assertEqual(obj.isocode,u'ZAR')
        self.assertEqual(obj.dernier_tx_de_change,10.0)
        self.assertEqual(obj.date_dernier_change,'2010-1-1')
    def test_banques_properties(self):
        obj=Banque.objects.get(id=1)
        self.assertEqual(obj.nom,u'banque test')
        self.assertEqual(obj.cib,u'30003')
        self.assertEqual(obj.notes,u'voici qq remarques')
    def test_seconde_bq(self):
        self.assertEqual(Banque.objects.get(id=2).cib,u'12345')
    def test_cat(self):
        obj=Cat.objects.get(id=5)
        self.assertEqual(obj.nom,u'Revenus divers')
        self.assertEqual(obj.type,'r')
    def test_cat_global(self):
        self.assertEqual(Cat.objects.count(),5)
        self.assertEqual(Cat.objects.all().aggregate(max=models.Max('id'))['max'],21)
    def test_sous_cat(self):
        obj=Banque.objects.get(id=6)
        self.assertEqual(obj.scat_set.count(),9)
        self.assertEqual(obj.scat_set.aggregate(max=models.Max('id'))['max'],9)
        sous=obj.scat_set.get(id=0)
        self.assertEqual(sous.nom,u'Bar')
        self.assertEqual(sous.grisbi_id,1)
    def test_ib(self):
        obj=Banque.objects.get(id=1)
        self.assertEqual(obj.nom,u'imputation_credit')
        self.assertEqual(obj.type,'r')
    def test_ib_global(self):
        self.assertEqual(Ib.objects.count(),4)
        self.assertEqual(Ib.objects.all().aggregate(max=models.Max('id'))['max'],4)
    def test_sous_ib(self):
        obj=Banque.objects.get(id=2)
        self.assertEqual(obj.sib_set.count(),9)
        self.assertEqual(obj.sib_set.aggregate(max=models.Max('id'))['max'],1)
        sous=obj.sib_set.get(id=0)
        self.assertEqual(sous.nom,u'sous_imputation')
        self.assertEqual(sous.grisbi_id,1)    
    def test_exercice(self):
        obj=Exercice.objects.get(id=0)
        self.assertEqual(obj.date_debut,'2010-1-1')
        self.assertEqual(obj.date_fin,'2010-12-31')
        self.assertEqual(obj.nom,u'2010')
        self.assertEqual(Exercice.objects.all().aggregate(max=models.Max('id'))['max'],2)
    def test_moyen(self):
        obj=Compte.objects.get(id=0).Moyen_set.get(grisbi_id=1)
        self.assertEqual(obj.nom,u'Virement')
        self.assertEqual(obj.signe,'v')
        self.assertEqual(obj.affiche_numero,True)
        self.assertEqual(obj.num_auto,False)
        self.assertEqual(obj.num_en_cours,0)
    def test_moyen_avec_numero(self):
        obj=Compte.objects.get(id=0).Moyen_set.get(grisbi_id=5)
        self.assertEqual(obj.nom,u'chèque')
        self.assertEqual(obj.signe,'d')
        self.assertEqual(obj.affiche_numero,True)
        self.assertEqual(obj.num_auto,True)
        self.assertEqual(obj.num_en_cours,12345)    
    def test_nb_moyens_dans_compte(self):
        self.assertEqual(Compte.objects.get(id=0).Moyen_set.count(),5)
    
