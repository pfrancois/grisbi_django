# -*- coding: utf-8 -*-
"""
test models
"""
from django.test import TestCase
from mysite.gsb.models import *
import decimal

class reaffacte_test(TestCase):
    def test_reaffect_tiers():
        self.tiers1.re
        
    def toto(self):
        self.tiers1 = Tiers.objects.create(nom='tiers1')
        self.tiers2 = Tiers.objects.create(nom='tiers2')
        self.titre1 = Titre.objects.create(nom="t1", isin="1", type='ACT')
        self.titre2 = Titre.objects.create(nom="t2", isin="2", type='ACT')
        self.devise1 = Titre.objects.create(nom='euro', isin='EUR', type='DEV')
        self.devise2 = Titre.objects.create(nom='devise2', isin='USD', type='DEV')
        Cours(valeur=decimal.Decimal('10.00'), titre=self.titre1, date=datetime.date(day=1, month=1, year=2010)).save()
        Cours(valeur=decimal.Decimal('1.00'), titre=self.devise1, date=datetime.date(day=1, month=1, year=2010)).save()
        self.banque1 = Banque.objects.create(cib="10001", nom="banque1")
        self.banque2 = Banque.objects.create(cib="10001", nom="banque2")
        self.cat1 = Cat.objects.create(type='r', nom='cat1')
        self.cat2 = Cat.objects.create(type='r', nom='cat2')
        self.ib1 = Ib.objects.create(type='r', nom="ib1")
        self.ib2 = Ib.objects.create(type='r', nom="ib2")
        self.exercice1 = Exercice.objects.create(date_debut=datetime.date(day=1, month=1, year=2010), date_fin=datetime.date(day=31, month=12, year=2010))
        self.exercice1 = Exercice.objects.create(date_debut=datetime.date(day=1, month=1, year=2011), date_fin=datetime.date(day=31, month=12, year=2011))
        self.moyen1 = Moyen.objects.create(nom='moyen1', type="d")
        self.moyen2 = Moyen.objects.create(nom='moyen2', type="d")
        self.moyen3 = Moyen.objects.create(nom='moyen3', type="r")
        self.compte1 = Compte.objects.create(nom='cpt1', type='b', devise=self.devise1, banque=self.banque1, solde_init='0', moyen_credit_defaut=self.moyen3, moyen_debit_defaut=self.moyen1)
        self.compte2 = Compte.objects.create(nom='cpt2', type='b', devise=self.devise1, banque=self.banque1, solde_init='0', moyen_credit_defaut=self.moyen3, moyen_debit_defaut=self.moyen1)
        self.compte3 = Compte.objects.create(nom='cpt3', type='b', devise=self.devise1, banque=self.banque1, solde_init='0', moyen_credit_defaut=self.moyen3, moyen_debit_defaut=self.moyen1)
        self.compte_titre1 = Compte_titre.objects.create(nom='cpt3', type='t', devise=self.devise1, banque=self.banque1, solde_init='0', moyen_credit_defaut=self.moyen3, moyen_debit_defaut=self.moyen1)
        self.compte_titre2 = Compte_titre.objects.create(nom='cpt4', type='t', devise=self.devise1, banque=self.banque1, solde_init='0', moyen_credit_defaut=self.moyen3, moyen_debit_defaut=self.moyen1)
        self.rapp1 = Rapp.objects.create(nom='r1')
        self.rapp2 = Rapp.objects.create(nom='r2')
        self.ech1 = Echeance.objects.create(compte=self.compte1, montant='10', devise=self.devise1, tiers=self.tiers1, cat=self.cat1, compte_virement=self.compte3, notes='1')
        self.ech2 = Echeance.objects.create(compte=self.compte1, montant='10', devise=self.devise1, tiers=self.tiers1, cat=self.cat1, compte_virement=self.compte3, notes='2')
        self.ope1 = Ope.objects.create(compte=self.compte1, montant='10', devise=self.devise1, tiers=self.tiers1, cat=self.cat1, notes='1')
        self.ope2 = Ope.objects.create(compte=self.compte1, montant='10', devise=self.devise1, tiers=self.tiers1, cat=self.cat1, notes='2')
