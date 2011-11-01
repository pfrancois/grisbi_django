# -*- coding: utf-8 -*
"""
test models
"""
from __future__ import absolute_import
from django.test import TestCase
from ..models import Generalite, Compte, Ope, Tiers, Cat, Moyen, Titre, Banque
from ..models import Compte_titre, Virement, Ope_titre, Ib, Exercice, Cours
from ..models import Rapp, Echeance, Gsb_exc
import datetime
import decimal
from django.conf import settings
from ..utils import strpdate

class test_models(TestCase):
    fixtures = ['test.json']

    def setUp(self):
        #gestion des parametres
        self.old_ID_CPT_M = settings.ID_CPT_M
        self.TAUX_VERSEMENT = settings.TAUX_VERSEMENT
        self.ID_CAT_COTISATION = settings.ID_CAT_COTISATION
        self.ID_TIERS_COTISATION = settings.ID_TIERS_COTISATION
        self.ID_CAT_OST = settings.ID_CAT_OST
        self.MD_CREDIT = settings.MD_CREDIT
        self.MD_DEBIT = settings.MD_DEBIT
        settings.ID_CPT_M = 1
        settings.TAUX_VERSEMENT = decimal.Decimal(str(1 / (1 - (0.08 * 0.97)) * (0.08 * 0.97)))
        #id et cat des operation speciales
        settings.ID_CAT_COTISATION = 23
        settings.ID_TIERS_COTISATION = 727
        settings.ID_CAT_OST = 64
        settings.MD_CREDIT = 6
        settings.MD_DEBIT = 7

    def tearDown(self):
        settings.ID_CPT_M = self.old_ID_CPT_M
        settings.TAUX_VERSEMENT = self.TAUX_VERSEMENT
        settings.ID_CAT_COTISATION = self.ID_CAT_COTISATION
        settings.ID_TIERS_COTISATION = self.ID_TIERS_COTISATION
        settings.ID_CAT_OST = self.ID_CAT_OST
        settings.MD_CREDIT = self.MD_CREDIT
        settings.MD_DEBIT = self.MD_DEBIT

    def test_models_unicode(self):
        self.assertEquals(Tiers.objects.get(nom="tiers1").__unicode__(), u"tiers1")
        self.assertEquals(Titre.objects.get(nom="t1").__unicode__(), u"t1 (1)")
        self.assertEquals(Banque.objects.get(nom="banque1").__unicode__(), u"banque1")
        self.assertEquals(Cours.objects.get(id=1).__unicode__(), u"le 2009-12-31, 1 t2 : 10")
        self.assertEquals(Cat.objects.get(nom="cat1").__unicode__(), u"cat1")
        self.assertEquals(Ib.objects.get(nom="ib1").__unicode__(), u"ib1")
        self.assertEquals(Exercice.objects.get(nom="exo1").__unicode__(), u"01/01/2010 au 31/10/2010")
        self.assertEquals(Compte.objects.get(nom="cpte1").__unicode__(), u"cpte1")
        self.assertEquals(Ope_titre.objects.get(id=1).__unicode__(), u"1")#TODO a inserer
        self.assertEquals(Moyen.objects.get(id=1).__unicode__(), u"moyen_rec1 (r)")
        self.assertEquals(Rapp.objects.get(id=1).__unicode__(), u"r1")
        self.assertEquals(Echeance.objects.get(id=1).__unicode__(), u"1")#TODO a inserer
        self.assertEquals(Generalite.objects.get(id=1).__unicode__(), u"1")
        self.assertEquals(Ope.objects.get(id=1).__unicode__(), u"(1) le 2011-08-11 : 10 EUR")

    def test_fusionne_error(self):
        self.assertRaises(TypeError, Tiers.objects.get(nom="tiers1").fusionne, Cat.objects.get(id=1))
        self.assertRaises(TypeError, Titre.objects.get(nom="t1").fusionne, Cat.objects.get(id=1))
        self.assertRaises(TypeError, Titre.objects.get(nom="t1").fusionne, Titre.objects.get(nom="autre"))
        self.assertRaises(Gsb_exc, Titre.objects.get(nom="t4").fusionne, Titre.objects.get(nom="autre"))
        self.assertRaises(TypeError, Cat.objects.get(id=1).fusionne, Banque.objects.get(id=1))
        self.assertRaises(TypeError, Banque.objects.get(id=1).fusionne, Cat.objects.get(id=1))
        self.assertRaises(TypeError, Cat.objects.get(id=3).fusionne, Cat.objects.get(id=1))
        self.assertRaises(TypeError, Ib.objects.get(id=3).fusionne, Ib.objects.get(id=1))
        self.assertRaises(TypeError, Ib.objects.get(id=1).fusionne, Banque.objects.get(id=1))
        self.assertRaises(TypeError, Exercice.objects.get(id=1).fusionne, Banque.objects.get(id=1))
        self.assertRaises(TypeError, Compte.objects.get(id=1).fusionne, Banque.objects.get(id=1))
        self.assertRaises(TypeError, Compte_titre.objects.get(id=4).fusionne, Banque.objects.get(id=1))
        self.assertRaises(TypeError, Moyen.objects.get(id=1).fusionne, Banque.objects.get(id=1))
        self.assertRaises(TypeError, Rapp.objects.get(id=1).fusionne, Banque.objects.get(id=1))
        self.assertRaises(TypeError, Rapp.objects.get(id=1).fusionne, Banque.objects.get(id=1))

    def test_investietnb(self):
        self.assertEqual(Titre.objects.get(id=1).investi(), 0)
        self.assertEqual(Titre.objects.get(id=2).investi(), 100)
        self.assertEqual(Titre.objects.get(id=2).investi(rapp=True),
                         0)#todo ajouter des operation afin que l'on trouv un chiffre
        self.assertEqual(Titre.objects.get(id=2).investi(datel=strpdate("2009-01-01")), 0)
        self.assertEqual(Titre.objects.get(id=1).nb(), 0)
        self.assertEqual(Titre.objects.get(id=2).nb(), 20)
        self.assertEqual(Titre.objects.get(id=2).nb(rapp=True),
                         0)#todo ajouter des operation afin que l'on trouv un chiffre
        self.assertEqual(Titre.objects.get(id=2).nb(datel=strpdate("2009-01-01")), 0)
        self.assertEqual(Titre.objects.get(id=2).encours(), 100)

    def test_tiers_fusionne(self):
        Tiers.objects.get(nom="tiers1").fusionne(Tiers.objects.get(nom="tiers2"))
        self.assertEqual(Tiers.objects.count(), 6)
        self.assertEqual(Ope.objects.get(id=1).tiers.nom, "tiers2")
        self.assertEqual(Echeance.objects.get(id=1).tiers.nom, "tiers2")

    def test_titre_last_cours_et_date(self):
        self.assertEquals(Titre.objects.get(nom="t1").last_cours, 1)
        self.assertEqual(Titre.objects.get(nom="t1").last_cours_date, datetime.date(day=30, month=1, year=2011))

    def test_titre_creation(self):
        tiers = Titre.objects.get(nom="t1").tiers
        self.assertNotEqual(tiers, None)
        self.assertEqual(tiers.nom, 'titre_ t1')
        self.assertEqual(tiers.notes, "1@ACT")
        self.assertEqual(tiers.is_titre, True)

    def test_titre_fusionne(self):
        Titre.objects.get(nom="t1").fusionne(Titre.objects.get(nom="t2"))
        self.assertEqual(Titre.objects.count(), 3)
        self.assertEqual(Tiers.objects.count(), 6)#verifie que la fusion des tiers sous jacent
        #verifier que les cours ont été fusionneés
        self.assertEquals(Titre.objects.get(nom='t2').cours_set.count(), 4)

    def test_titre_save_perso(self):
        t = Titre.objects.create(nom="t3", isin="4", type='ACT')
        self.assertEqual(Tiers.objects.count(), 8)
        self.assertEqual(Tiers.objects.filter(is_titre=True).count(), 5)
        self.assertEqual(Tiers.objects.get(nom="titre_ t3").nom, "titre_ t3")
        self.assertEqual(Tiers.objects.get(nom="titre_ t3").notes, "4@ACT")
        t.tiers.notes = ""
        t.save()
        self.assertEqual(Tiers.objects.get(nom="titre_ t3").notes, "4@ACT")

    def test_banque_fusionne(self):
        new_b = Banque.objects.get(cib="10001")
        Banque.objects.get(cib="99999").fusionne(new_b)
        self.assertEqual(Banque.objects.count(), 1)
        self.assertEqual(Compte.objects.get(id=1).banque.id, 1)

    def test_cat_fusionne(self):
        Cat.objects.get(nom="cat2").fusionne(Cat.objects.get(nom="cat1"))
        self.assertEqual(Cat.objects.count(), 4)
        self.assertEqual(Ope.objects.filter(cat__nom="cat1").count(), 4)
        self.assertEquals(Echeance.objects.filter(cat__nom="cat1").count(), 1)

    def test_ib_fusionne(self):
        Ib.objects.get(nom="ib2").fusionne(Ib.objects.get(nom="ib1"))
        self.assertEqual(Ib.objects.count(), 3)
        self.assertEqual(Ope.objects.filter(ib__nom="ib1").count(), 2)
        self.assertEquals(Echeance.objects.filter(ib__nom="ib1").count(), 1)

    def test_exo_fusionne(self):
        exo = Exercice.objects.get(id=1)
        Ope.objects.create(compte=Compte.objects.get(id=1), date='2010-01-01', montant=20,
                                       tiers=Tiers.objects.get(id=1),exercice=Exercice.objects.get(id=2))
        Exercice.objects.get(id=2).fusionne(exo)
        self.assertEqual(Exercice.objects.count(), 1)
        self.assertEquals(exo.date_debut,strpdate('2010-1-1'))
        self.assertEquals(exo.date_fin,strpdate('2011-12-31'))
        self.assertEqual(exo.echeance_set.count(),1)
        self.assertEqual(exo.ope_set.count(),1)

    def test_compte_solde_normal(self):
        self.assertEqual(Compte.objects.get(id=1).solde(), decimal.Decimal('20'))

    def test_compte_abolute_url(self):
        self.assertEqual(Compte.objects.get(id=1).get_absolute_url(), '/compte/1/')

    def test_ope_titre_achat_sans_virement(self):
        c = Compte_titre.objects.get(id=4)
        self.assertEqual(c.nom, u'cpt_titre1')
        t = Titre.objects.get(nom="t1")
        self.assertEqual(t.investi(c), 0)
        c.achat(titre=t, nombre=20, date='2011-01-01')
        self.assertEqual(t.investi(c), 20)
        tall = c.titre.all().distinct()
        self.assertEqual(tall.count(), 2)
        self.assertEqual(tall[0].last_cours, 1)
        self.assertEqual(c.solde(), 100)
        t.cours_set.create(date='2011-02-01', valeur=2)
        self.assertEqual(c.solde(), 120)
        c.vente(titre=t, nombre=10, prix=3, date='2011-06-30')
        self.assertEqual(c.solde(), 140)
        c.achat(titre=t, nombre=20, prix=2, date='2011-01-01')
        self.assertEqual(c.solde(), 160)

    def test_cpt_titre_achat_complet(self):
        c = Compte_titre.objects.get(id=5)
        t = Titre.objects.get(nom="t1")
        c.achat(titre=t, nombre=20, date='2011-01-01', virement_de=Compte.objects.get(id=1))
        self.assertEqual(t.investi(c), 20)
        self.assertEqual(c.solde(), 20)
        t.cours_set.create(date='2011-02-01', valeur=2)
        c.vente(t, 10, 3, '2011-06-30', virement_vers=Compte.objects.get(id=1))
        self.assertEqual(t.investi(c), -10)
        self.assertEqual(c.solde(), 30)

    def test_moyen_fusionne(self):
        Moyen.objects.get(id=2).fusionne(Moyen.objects.get(id=1))

    #    def test_rapp_compte(self):
    #    def test_rapp_solde(self):
    #    def test_rapp_fusionne(self):
    #    def test_echeance_save(self):
    def test_generalite_gen(self):
        self.assertEquals(Generalite.gen().id, 1)

    def test_generalite_dev_g(self):
        self.assertEqual(Generalite.dev_g(), 'EUR')

    def test_ope_absolute_url(self):
        self.assertEqual(0, 0)

    def test_ope_save(self):
        o = Ope.objects.create(compte=Compte.objects.get(id=1), date='2010-01-01', montant=20,
                               tiers=Tiers.objects.get(id=1))
        self.assertEquals(o.moyen, o.compte.moyen_credit_defaut)
        o = Ope.objects.create(compte=Compte.objects.get(id=1), date='2010-01-01', montant=-20,
                               tiers=Tiers.objects.get(id=1))
        self.assertEquals(o.moyen, o.compte.moyen_debit_defaut)
        o = Ope.objects.create(compte=Compte.objects.get(id=1), date='2010-01-01', montant=-20,
                               tiers=Tiers.objects.get(id=1), moyen=Moyen.objects.get(id=2))
        self.assertEquals(o.moyen, Moyen.objects.get(id=2))

    def test_virement_verif_property(self):
        Virement.create(Compte.objects.get(id=1), Compte.objects.get(id=2), 20, date='2010-01-01', notes='test_notes')
        v = Virement(Ope.objects.get(id=8))
        self.assertEquals(v.origine.id, 8)
        self.assertEquals(v.dest.id, 9)
        self.assertEquals(v.origine.compte, Compte.objects.get(nom='cpte1'))
        self.assertEquals(v.dest.compte, Compte.objects.get(nom='cptb2'))
        self.assertEquals(v.date, strpdate('2010-01-01'))
        self.assertEquals(v.montant, v.origine.montant * -1)
        self.assertEquals(v.montant, v.dest.montant)
        self.assertEquals(v.montant, 20)
        self.assertEquals(v.__unicode__(), u"cpte1 => cptb2")
        v.date_val = '2011-02-01'
        v.save()
        self.assertEquals(Virement(Ope.objects.get(id=8)).date_val, strpdate('2011-02-01'))

    def test_virement_create(self):
        v = Virement.create(Compte.objects.get(id=1), Compte.objects.get(id=2), 20)
        self.assertEqual(Compte.objects.get(id=1).solde(), 0)
        self.assertEquals(v.origine.compte, Compte.objects.get(nom='cpte1'))
        self.assertEquals(v.dest.compte, Compte.objects.get(nom='cptb2'))
        self.assertEquals(v.origine.id, 8)
        self.assertEquals(v.date, datetime.date.today())
        self.assertEquals(v.montant, v.origine.montant * -1)
        self.assertEquals(v.montant, v.dest.montant)
        self.assertEquals(v.montant, 20)
        v = Virement.create(Compte.objects.get(id=1), Compte.objects.get(id=2), 20,
                            '2010-01-01', 'test_notes')
        self.assertEqual(Compte.objects.get(id=1).solde(), -20)
        self.assertEqual(v.date, '2010-01-01')
        self.assertEqual(v.notes, 'test_notes')

    def test_virement_delete(self):
        v = Virement.create(Compte.objects.get(id=1), Compte.objects.get(id=2), 20)
        v.delete()
        self.assertEquals(Compte.objects.get(nom='cpte1').solde(), 20)
        self.assertEquals(Compte.objects.get(nom='cptb2').solde(), -90)

    def test_virement_init_form(self):
        v = Virement.create(Compte.objects.get(id=1), Compte.objects.get(id=2), 20,
                            '2010-01-01', 'test_notes')
        tab = {'compte_origine':1,
               'compte_destination':2,
               'montant':20,
               'date':"2010-01-01",
               'notes':'test_notes',
               'pointe':False,
               'moyen_origine':4,
               'moyen_destination':4
        }
        self.assertEquals(tab, v.init_form())
