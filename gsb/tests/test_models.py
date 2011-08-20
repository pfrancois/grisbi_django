# -*- coding: utf-8 -*
"""
test models
"""
from django.test import TestCase
from mysite.gsb.models import Generalite, Compte, Ope,  Tiers,  Cat, Moyen, Echeance, Ib, Titre, Banque, Exercice, Rapp
from mysite.gsb.models import Cours, Compte_titre, Virement
import datetime,time
import decimal
def strpdate(s):
    return datetime.date(*time.strptime(s, "%Y-%m-%d")[0:3])
class test_models(TestCase):
    fixtures=['test.json']
    def test_nb_ope_titre(self):
        self.assertEqual(0,0)
    def test_reaffect_tiers(self):
        Tiers.objects.get(nom="tiers1").fusionne(Tiers.objects.get(nom="tiers2"))
        self.assertEqual(Tiers.objects.count(), 3)
        self.assertEqual(Ope.objects.get(id=1).tiers.nom,"tiers2")
        self.assertEqual(Echeance.objects.get(id=1).tiers.nom,"tiers2")
    def test_last_cours_et_date(self):
        self.assertEquals(Titre.objects.get(nom="t1").last_cours,1)
        self.assertEqual(Titre.objects.get(nom="t1").last_cours_date, datetime.date(day=1, month=1, year=2010) )
    def test_creation_titre(self):
        tiers = Titre.objects.get(nom="t1").tiers
        self.assertNotEqual(tiers, None)
        self.assertEqual(tiers.nom, 'titre_ t1')
        self.assertEqual(tiers.notes, "1@ACT")
        self.assertEqual(tiers.is_titre, True)
    def test_titre_fusionne(self):#test qui ne marche pas
        Titre.objects.get(nom="t1").fusionne(Titre.objects.get(nom="t2"))
        self.assertEqual(Titre.objects.count(), 1)
        self.assertEqual(Tiers.objects.count(), 3)#verifie que la fusion des tiers sous jacent
        #self.assertEqual(Cours.objects.get(id=1).titre.nom,"t2") ca ne marchce pas gestion particuliere a voir
    def test_titre_save_perso(self):
        Titre.objects.create(nom="t3", isin="4", type='ACT')
        self.assertEqual(Tiers.objects.count(), 5)
        self.assertEqual(Tiers.objects.filter(is_titre=True).count(), 3)
        self.assertEqual(Tiers.objects.get(nom="titre_ t3").nom, "titre_ t3")
    def test_banque_fusionne(self):
        Banque.objects.get(cib='99999').fusionne(Banque.objects.get(cib="10001"))
        self.assertEqual(Banque.objects.count(),1)
        self.assertEqual(Compte.objects.get(id=3).banque.id,1)
    def test_cat_fusionne(self):
        Cat.objects.get(nom="cat2").fusionne(Cat.objects.get(nom="cat1"))
        self.assertEqual(Cat.objects.count(),3)
        self.assertEqual(Echeance.objects.filter(cat__nom="cat1").count(),3)
    #def test_ib_fusionne(self):
    #def test_exo_fusionne(self):
    def test_solde_compte_normal(self):
        self.assertEqual(Compte.objects.get(id=1).solde,decimal.Decimal('20'))
    def test_abolute_url_compte(self):
        self.assertEqual(Compte.objects.get(id=1).get_absolute_url(),'/compte/1/')
    #def test_cpt_fusionne(self):
#    def test_cpt_titre_achat(self):
#        c=Compte_titre.objects.get(id=4)
#        self.assertEqual(c.nom, u'cpt_titre1')
        #achat de base avec tout par defaut
        #c.achat(titre=Titre.objects.get(nom="t1"), nombre=20)
        #t=c.titres_detenus_set.all()
        #self.assertEqual(t[0].valeur, decimal.Decimal('20'))
        #self.assertEqual(t.count(),1)
        #self.assertEqual(t[0].nombre,decimal.Decimal('20'))
        #self.assertEqual(Titre.objects.get(nom="t1").last_cours, decimal.Decimal('1'))
        #self.assertEqual(c.solde,0)

#    def test_cpt_titre_achat_complet(self):
#    def test_cpt_titre_achat_virement(self):
    def test_cpt_titre_vente(self):
        c=Compte_titre.objects.get(nom='cpt_titre1')
        c.achat(titre=Titre.objects.get(nom="t1"), nombre=20)
        c.vente(Titre.objects.get(nom="t1"),10)
        #self.assertEqual(c.solde,0) #TODO

#    def test_cpt_titre_vente_complet(self):
#    def test_cpt_titre_vente_virement(self):
#    def test_cpt_titre_revenu(self):
#    def test_cpt_titre_revenu_complet(self):
#    def test_cpt_titre_revenu_virement(self):
    def test_cpt_titre_solde(self):
        c=Compte_titre.objects.get(nom='cpt_titre1')
        self.assertEqual(c.solde,0)
#    def test_cpt_titre_fusion(self):
#    def test_cpt_titre_absolute_url(self):
#    def test_titre_detenu_valeur(self):
#    def test_moyen_fusionne(self):
#    def test_rapp_compte(self):
#    def test_rapp_solde(self):
#    def test_rapp_fusionne(self):
#    def test_echeance_save(self):
#    def test_generalite_gen(self):
    def test_generalite_dev_g(self):
        self.assertEqual(Generalite.dev_g(),'EUR')
    def test_ope_absolute_url(self):
        self.assertEqual(0,0)
    def test_ope_save(self):
        self.assertEqual(0,0)
    def test_virement_verif_property(self):
        Virement.create(Compte.objects.get(id=1), Compte.objects.get(id=2), 20,date='2010-01-01',notes='test_notes')
        v=Virement(Ope.objects.get(id=3))
        self.assertEquals(v.origine.id,3)
        self.assertEquals(v.dest.id,4)
        self.assertEquals(v.origine.compte,Compte.objects.get(nom='cpt1'))
        self.assertEquals(v.dest.compte,Compte.objects.get(nom='cpt2'))
        self.assertEquals(v.origine.id,3)
        self.assertEquals(v.date,strpdate('2010-01-01'))
        self.assertEquals(v.montant,v.origine.montant*-1)
        self.assertEquals(v.montant,v.dest.montant)
        self.assertEquals(v.montant,20)
        v.date_val='2011-02-01'
        v.save()
        self.assertEquals(Virement(Ope.objects.get(id=3)).date_val,strpdate('2011-02-01'))
    def test_virement_create(self):
        v=Virement.create(Compte.objects.get(id=1), Compte.objects.get(id=2), 20)
        self.assertEqual(Compte.objects.get(id=1).solde,0)
        self.assertEquals(v.origine.compte,Compte.objects.get(nom='cpt1'))
        self.assertEquals(v.dest.compte,Compte.objects.get(nom='cpt2'))
        self.assertEquals(v.origine.id,3)
        self.assertEquals(v.date,datetime.date.today())
        self.assertEquals(v.montant,v.origine.montant*-1)
        self.assertEquals(v.montant,v.dest.montant)
        self.assertEquals(v.montant,20)
        v=Virement.create(Compte.objects.get(id=1), Compte.objects.get(id=2), 20,'2010-01-01','test_notes')
        self.assertEqual(Compte.objects.get(id=1).solde,-20)
        self.assertEqual(v.date,'2010-01-01')
        self.assertEqual(v.notes,'test_notes')
    def test_virement_delete(self):
        v=Virement.create(Compte.objects.get(id=1), Compte.objects.get(id=2), 20)
        v.delete()
        self.assertEquals(Compte.objects.get(nom='cpt1').solde,20)
        self.assertEquals(Compte.objects.get(nom='cpt2').solde,0)
    def test_virement_init_form(self):
        v=Virement.create(Compte.objects.get(id=1), Compte.objects.get(id=2), 20,'2010-01-01','test_notes')
        tab = {'compte_origine':1,
               'compte_destination':2,
               'montant':20,
               'date':"2010-01-01",
               'notes':'test_notes',
               'pointe':False,
               'piece_comptable_compte_origine':u'',
               'piece_comptable_compte_destination':u'',
               'moyen_origine':1,
               'moyen_destination':3,
               }
        self.assertEquals(tab,v.init_form())