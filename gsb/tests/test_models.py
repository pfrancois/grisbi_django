# -*- coding: utf-8 -*
"""
test models
"""
from django.test import TestCase
from mysite.gsb.models import Generalite, Compte, Ope,  Tiers,  Cat, Moyen, Echeance, Ib, Titre, Banque, Exercice, Rapp
from mysite.gsb.models import Cours, Compte_titre
import datetime
import decimal #@Reimport

msg=None
class test_models(TestCase):
    fixtures=['test.json']
    def test_reaffect_tiers(self):
        Tiers.objects.get(nom="tiers1").fusionne(Tiers.objects.get(nom="tiers2"))
        self.assertEqual(Tiers.objects.count(), 3)
        self.assertEqual(Ope.objects.get(id=1).tiers.nom,"tiers2")
        self.assertEqual(Echeance.objects.get(id=1).tiers.nom,"tiers2")
    def test_last_cours_et_date(self):
        self.assertEquals(Titre.objects.get(nom="t1").last_cours,10)
        self.assertEqual(Titre.objects.get(nom="t1").last_cours_date, datetime.date(day=1, month=1, year=2010) )
    def test_creation_titre(self):
        tiers = Titre.objects.get(nom="t1").tiers
        self.assertNotEqual(tiers, None)
        self.assertEqual(tiers.nom, 'titre_ t1')
        self.assertEqual(tiers.notes, "1@ACT")
        self.assertEqual(tiers.is_titre, True)
    def test_titre_fusionne(self):
        Titre.objects.get(nom="t1").fusionne(Titre.objects.get(nom="t2"))
        self.assertEqual(Titre.objects.count(), 3)
        self.assertEqual(Tiers.objects.count(), 3)#verifie que la fusion des tiers sous jacent
        self.assertEqual(Cours.objects.get(id=1).titre.nom,"t2")
        #TODO gerer la fusion des tiers sous jacents
        #TODO titre detenus non verifies
        #self.assertEqual(Tiers.objects.get(id=1).titre.nom,"t2")
    def test_titre_save_perso(self):
        Titre.objects.create(nom="t3", isin="4", type='ACT')
        self.assertEqual(Tiers.objects.count(), 5)
        self.assertEqual(Tiers.objects.filter(is_titre=True).count(), 3)
        self.assertEqual(Tiers.objects.get(nom="titre_ t3").nom, "titre_ t3")
    def test_banque_fusionne(self):
        pass
    def test_cat_fusionne(self):
        pass
    def test_ib_fusionne(self):
        pass
    def test_exo_fusionne(self):
        pass
    def test_solde_compte_normal(self):
        self.assertEqual(Compte.objects.get(id=1).solde(),decimal.Decimal('20'))
    def test_abolute_url_compte(self):
        self.assertEqual(Compte.objects.get(id=1).get_absolute_url(),'/compte/1/')
    def test_cpt_fusionne(self):
        self.assertEqual(0,0)
    def test_cpt_titre_achat(self):
        c=Compte_titre.objects.get(id=4)
        self.assertEqual(c.nom, u'cpt_titre1')
        #achat de base avec tout par defaut
        c.achat(titre=Titre.objects.get(nom="t1"), nombre=20)
        t=c.titres_detenus_set.all()
        self.assertEqual(t[0].valeur, decimal.Decimal('20'))
        self.assertEqual(t.count(),1)
        self.assertEqual(t[0].nombre,decimal.Decimal('20'))
        self.assertEqual(Titre.objects.get(nom="t1").last_cours, decimal.Decimal('1'))
        self.assertEqual(c.solde(),0)

    def test_cpt_titre_achat_complet(self):
        self.assertEqual(0,0)
    def test_cpt_titre_achat_virement(self):
        self.assertEqual(0,0)
    def test_cpt_titre_vente(self):
        c=Compte_titre.objects.get(id=4)
        c.achat(titre=Titre.objects.get(nom="t1"), nombre=20)
        c.vente(Titre.objects.get(nom="t1"),10)
        self.assertEqual(c.solde(),0)

    def test_cpt_titre_vente_complet(self):
        self.assertEqual(0,0)
    def test_cpt_titre_vente_virement(self):
        self.assertEqual(0,0)
    def test_cpt_titre_revenu(self):
        self.assertEqual(0,0)
    def test_cpt_titre_revenu_complet(self):
        self.assertEqual(0,0)
    def test_cpt_titre_revenu_virement(self):
        self.assertEqual(0,0)
    def test_cpt_titre_solde(self):
        self.assertEqual(0,0)
    def test_cpt_titre_fusion(self):
        self.assertEqual(0,0)
    def test_cpt_titre_absolute_url(self):
        self.assertEqual(0,0)
    def titre_detenu_valeur(self):
        self.assertEqual(0,0)
    def moyen_fusionne(self):
        self.assertEqual(0,0)
    def rapp_compte(self):
        self.assertEqual(0,0)
    def rapp_solde(self):
        self.assertEqual(0,0)
    def rapp_fusionne(self):
        self.assertEqual(0,0)
    def echeance_save(self):
        self.assertEqual(0,0)
    def generalite_gen(self):
        self.assertEqual(0,0)
    def generalite_dev_g(self):
        self.assertEqual(Generalite.dev_g(),'EUR')
    def ope_absolute_url(self):
        self.assertEqual(0,0)
    def ope_save(self):
        self.assertEqual(0,0)
    def virement_verif_property(self):
        self.assertEqual(0,0)
    def virement_create(self):
        self.assertEqual(0,0)
    def virement_delete(self):
        self.assertEqual(0,0)
    def virement_init_form(self):
        self.assertEqual(0,0)        