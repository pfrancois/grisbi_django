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
        settings.MD_CREDIT = 1
        settings.MD_DEBIT = 2

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
        self.assertRaises(TypeError, Tiers.objects.get(nom="tiers1").fusionne, Cat.objects.get(id=1))#fusion avec un autre type
        self.assertRaises(ValueError, Tiers.objects.get(nom="tiers1").fusionne, Tiers.objects.get(nom="tiers1"))#fusion sur lui meme
        self.assertRaises(TypeError, Titre.objects.get(nom="t1").fusionne, Cat.objects.get(id=1))#fusion avec un autre type
        self.assertRaises(ValueError, Titre.objects.get(nom="t1").fusionne, Titre.objects.get(nom="t1"))#fusion sur lui meme
        self.assertRaises(TypeError, Titre.objects.get(nom="t1").fusionne, Titre.objects.get(nom="autre"))
        self.assertRaises(Gsb_exc, Titre.objects.get(nom="t4").fusionne, Titre.objects.get(nom="autre"))#fusion entre deux compte de type difference
        self.assertRaises(TypeError, Banque.objects.get(id=1).fusionne, Cat.objects.get(id=1))#fusion avec un autre type
        self.assertRaises(ValueError, Banque.objects.get(id=1).fusionne, Banque.objects.get(id=1))#fusion sur lui meme
        self.assertRaises(TypeError, Cat.objects.get(id=1).fusionne, Banque.objects.get(id=1))#fusion avec un autre type
        self.assertRaises(TypeError, Cat.objects.get(id=3).fusionne, Cat.objects.get(id=1))#fusion entre deux cat de type difference
        self.assertRaises(ValueError, Cat.objects.get(id=1).fusionne, Cat.objects.get(id=1))#fusion sur lui meme
        self.assertRaises(TypeError, Ib.objects.get(id=3).fusionne, Ib.objects.get(id=1))#fusion entre deux ib de type difference
        self.assertRaises(TypeError, Ib.objects.get(id=1).fusionne, Banque.objects.get(id=1))#fusion avec un autre type
        self.assertRaises(ValueError, Ib.objects.get(id=1).fusionne, Ib.objects.get(id=1))#fusion sur lui meme
        self.assertRaises(TypeError, Exercice.objects.get(id=1).fusionne, Banque.objects.get(id=1))#fusion avec un autre type
        self.assertRaises(ValueError, Exercice.objects.get(id=1).fusionne, Exercice.objects.get(id=1))#fusion sur lui meme
        self.assertRaises(TypeError, Compte.objects.get(id=1).fusionne, Banque.objects.get(id=1))#fusion avec un autre type
        self.assertRaises(ValueError, Compte.objects.get(id=1).fusionne, Compte.objects.get(id=1))#fusion sur lui meme
        self.assertRaises(Gsb_exc, Compte.objects.get(id=1).fusionne, Compte.objects.get(id=2))#fusion entre deux compte de type difference
        self.assertRaises(TypeError, Compte_titre.objects.get(id=4).fusionne, Banque.objects.get(id=1))#fusion avec un autre type
        self.assertRaises(ValueError, Compte_titre.objects.get(id=4).fusionne, Compte_titre.objects.get(id=4))#fusion sur lui meme
        self.assertRaises(TypeError, Moyen.objects.get(id=1).fusionne, Banque.objects.get(id=1))#fusion avec un autre type
        self.assertRaises(ValueError, Moyen.objects.get(id=1).fusionne, Moyen.objects.get(id=2))#fusion avec un autre type
        self.assertRaises(ValueError, Moyen.objects.get(id=2).fusionne, Moyen.objects.get(id=3))#probleme si fusion d'un moyen settings
        self.assertRaises(ValueError, Moyen.objects.get(id=4).fusionne, Moyen.objects.get(id=4))#fusion sur lui meme
        self.assertRaises(TypeError, Rapp.objects.get(id=1).fusionne, Banque.objects.get(id=1))#fusion avec un autre type
        self.assertRaises(TypeError, Rapp.objects.get(id=1).fusionne, Banque.objects.get(id=1))#fusion avec un autre type

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

    def test_titre_investi(self):
        c = Compte_titre.objects.get(id=4)
        t = Titre.objects.get(nom="t2")
        Compte_titre.objects.get(id=5).achat(titre=t, nombre=20, date='2011-01-01')
        self.assertEquals(t.investi(), 120)
        self.assertEquals(t.investi(c), 100)
        self.assertEquals(t.investi(datel='2011-07-01'), 20)
        self.assertEquals(t.investi(compte=c, datel='2011-07-01'), 0)

    def test_titre_nb(self):
        c = Compte_titre.objects.get(id=4)
        t = Titre.objects.get(nom="t2")
        Compte_titre.objects.get(id=5).achat(titre=t, nombre=20, date='2011-01-01')
        o = Ope.objects.filter(compte=Compte_titre.objects.get(id=5), date='2011-01-01')[0]
        o.rapp = Rapp.objects.get(id=1)
        o.save()
        self.assertEquals(t.nb(), 40)
        self.assertEquals(t.nb(c), 20)
        self.assertEquals(t.nb(datel='2011-07-01'), 20)
        self.assertEquals(t.nb(compte=c, datel='2011-07-01'), 0)
        self.assertEquals(t.nb(rapp=True), 20)
        self.assertEquals(t.nb(rapp=True, datel='2010-07-01'), 0)
        self.assertEquals(t.nb(rapp=True, compte=Compte_titre.objects.get(id=5), datel='2010-07-01'), 0)

    def test_titre_encours(self):
        c = Compte_titre.objects.get(id=4)
        t = Titre.objects.get(nom="t2")
        Compte_titre.objects.get(id=5).achat(titre=t, nombre=20, date='2011-01-01')
        o = Ope.objects.filter(compte=Compte_titre.objects.get(id=5), date='2011-01-01')[0]
        o.rapp = Rapp.objects.get(id=1)
        o.save()
        self.assertEquals(t.encours(), 200)
        self.assertEquals(t.encours(c), 100)
        self.assertEquals(t.encours(datel='2011-07-01'), 20)
        self.assertEquals(t.encours(compte=c, datel='2011-07-01'), 0)
        self.assertEquals(t.encours(rapp=True), 100)
        self.assertEquals(t.encours(rapp=True, datel='2010-07-01'), 0)
        self.assertEquals(t.encours(rapp=True, compte=Compte_titre.objects.get(id=4)), 0)
        self.assertEquals(t.encours(rapp=True, compte=Compte_titre.objects.get(id=4), datel='2010-07-01'), 0)

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
        Exercice.objects.get(id=2).fusionne(exo)
        self.assertEqual(Exercice.objects.count(), 1)
        self.assertEquals(exo.date_debut, strpdate('2010-1-1'))
        self.assertEquals(exo.date_fin, strpdate('2011-12-31'))
        self.assertEqual(exo.echeance_set.count(), 1)
        self.assertEqual(exo.ope_set.count(), 1)

    def test_compte_solde_normal(self):
        self.assertEqual(Compte.objects.get(id=1).solde(), 40)
        self.assertEqual(Compte.objects.get(id=6).solde(), 0)
        self.assertEqual(Compte.objects.get(id=1).solde(rapp=True), 20)
        self.assertEqual(Compte.objects.get(id=1).solde(datel=strpdate('2009-01-01')), 0)

    def test_creation_compte_compte_titre(self):
        Compte.objects.create(nom="toto", type="t")
        Compte.objects.create(nom="hjhghj", type="b")
        self.assertIsInstance(Compte_titre.objects.get(nom="toto"), Compte_titre)
        self.assertIsInstance(Compte.objects.get(nom="hjhghj"), Compte)

    def test_compte_abolute_url(self):
        self.assertEqual(Compte.objects.get(id=1).get_absolute_url(), '/compte/1/')

    def test_compte_fusion(self):
        n = Compte.objects.get(id=3)
        o = Compte.objects.get(id=2)
        self.assertRaises(Gsb_exc, lambda:o.fusionne(Compte.objects.get(id=6)))
        self.assertRaises(Gsb_exc, lambda:Compte.objects.get(id=6).fusionne(o))
        o.fusionne(n)
        self.assertEquals(n.ope_set.count(), 3)
        self.assertEquals(Echeance.objects.get(id=1).compte_virement_id, 3)
        self.assertEquals(Ope.objects.get(id=3).compte_id, 3)
        Compte.objects.get(id=4).fusionne(Compte.objects.get(id=5))
        self.assertEquals(Ope.objects.get(id=5).compte_id,5)
        self.assertEquals(Ope_titre.objects.get(id=1).compte_id,5)

    def test_compte_titre_error(self):
        c1 = Compte_titre.objects.get(id=4)
        c2 = Compte_titre.objects.get(id=5)
        #probleme si on utilise pas un titre dans le param titre
        self.assertRaises(TypeError, c1.achat, c2, 20, '2011-01-01')
        self.assertRaises(TypeError, c1.vente, c2, 20, '2011-01-01')
        self.assertRaises(TypeError, c1.revenu, c2, 20, '2011-01-01')

    def test_compte_titre_solde(self):
        c = Compte_titre.objects.get(id=4)
        t = Titre.objects.get(nom="t2")
        self.assertEqual(c.solde(), 100)
        t.cours_set.create(date='2011-11-01', valeur=2)
        self.assertEqual(c.solde(), 40)
        self.assertEqual(c.solde(datel=strpdate('2011-01-01')), 0)

    def test_compte_titre_achat_sans_virement(self):
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
        c.achat(titre=t, nombre=20, prix=2, date='2011-01-01')
        self.assertEqual(c.solde(), 80)

    def test_compte_titre_achat_avec_frais(self):
        c = Compte_titre.objects.get(id=4)
        t = Titre.objects.get(nom="t1")
        #utilisation des cat et tiers par defaut
        c.achat(titre=t, nombre=20, frais=20, date='2011-07-01')
        self.assertEqual(c.solde(), 80)
        self.assertEqual(t.investi(c), 40)
        o = Ope.objects.filter(compte=c, date='2011-07-01', notes__icontains='frais')[0]
        self.assertEqual(o.cat_id, 65)
        self.assertEqual(o.montant, -20)
        self.assertEquals(o.notes, u"frais 20@1")
        self.assertEquals(o.moyen_id, 2)
        #"utilisa des cat et tiers donnes
        c.achat(titre=t, nombre=20, frais=20,
                cat_frais=Cat.objects.get(id=3),
                tiers_frais=Tiers.objects.get(id=2),
                date='2011-07-02')
        self.assertEqual(c.solde(), 60)
        self.assertEqual(t.investi(c), 60)
        o = Ope.objects.filter(compte=c, date='2011-07-02', notes__icontains='frais')[0]
        self.assertEqual(o.tiers_id, 2)
        self.assertEqual(o.cat_id, 3)
        self.assertEqual(o.montant, -20)
        self.assertEquals(o.notes, u"frais 20@1")
        self.assertEquals(o.moyen_id, 2)

    def test_cpt_titre_achat_avec_virement(self):
        c = Compte_titre.objects.get(id=5)
        t = Titre.objects.get(nom="t1")
        c.achat(titre=t, nombre=20, date='2011-01-01', virement_de=Compte.objects.get(id=1))
        self.assertEqual(t.investi(c), 20)
        self.assertEqual(c.solde(), 20)
        self.assertEquals(Ope.objects.filter(compte=c).count(), 2)
        self.assertEqual(Compte.objects.get(id=1).solde(), 20)

    def test_compte_titre_vente_sans_virement(self):
        c = Compte_titre.objects.get(id=4)
        self.assertEqual(c.nom, u'cpt_titre1')
        t = Titre.objects.get(nom="t2")
        self.assertEqual(t.investi(c), 100)
        self.assertRaises(Titre.DoesNotExist, lambda:c.vente(titre=t, nombre=20, date='2011-01-01'))#trop tot
        self.assertRaises(Titre.DoesNotExist, lambda:c.vente(titre=t, nombre=40, date='2011-11-02'))#montant trop eleve
        c.vente(titre=t, nombre=20, date='2011-11-01')
        self.assertEqual(t.investi(c), 80)
        tall = c.liste_titre()
        self.assertEqual(len(tall), 0)
        self.assertRaises(Titre.DoesNotExist, lambda:c.vente(titre=t, nombre=20, date='2011-11-01'))#a pu de titre
        self.assertEqual(c.solde(), 20)


    def test_compte_titre_vente_avec_frais(self):
        c = Compte_titre.objects.get(id=4)
        t = Titre.objects.get(nom="t2")
        #utilisation des cat et tiers par defaut
        c.vente(titre=t, nombre=10, frais=20, date='2011-11-01')
        self.assertEqual(c.solde(), 0)
        self.assertEqual(t.investi(c), 110)
        o = Ope.objects.filter(compte=c, date='2011-11-01', notes__icontains='frais')[0]
        self.assertEqual(o.cat_id, 65)
        self.assertEqual(o.montant, -20)
        self.assertEquals(o.notes, u"frais -10@1")
        self.assertEquals(o.moyen_id, 2)
        #"utilisa des cat et tiers donnes
        c.vente(titre=t, nombre=10, frais=20,
                cat_frais=Cat.objects.get(id=3),
                tiers_frais=Tiers.objects.get(id=2),
                date='2011-11-02')
        self.assertEqual(c.solde(), -20)
        self.assertEqual(t.investi(c), 100)
        o = Ope.objects.filter(compte=c, date='2011-11-02', notes__icontains='frais')[0]
        self.assertEqual(o.tiers_id, 2)
        self.assertEqual(o.cat_id, 3)
        self.assertEqual(o.montant, -20)
        self.assertEquals(o.notes, u"frais -10@1")
        self.assertEquals(o.moyen_id, 2)

    def test_cpt_titre_vente_avec_virement(self):
        c = Compte_titre.objects.get(id=4)
        t = Titre.objects.get(nom="t2")
        c.vente(titre=t, nombre=20, date='2011-11-02', virement_vers=Compte.objects.get(id=1))
        self.assertEqual(t.investi(c), 80)
        self.assertEqual(c.solde(), 0)
        self.assertEquals(Ope.objects.filter(compte=c).count(), 4)
        self.assertEqual(Compte.objects.get(id=1).solde(), 60)

    def test_cpt_titre_revenu_simple(self):
        c = Compte_titre.objects.get(id=4)
        t = Titre.objects.get(nom="t2")
        self.assertRaises(Titre.DoesNotExist, lambda:c.revenu(titre=t, montant=20, date='2011-01-01'))#trop tot
        c.revenu(titre=t, montant=20, date='2011-11-02')
        self.assertEqual(t.investi(c), 80)
        self.assertEqual(c.solde(), 120)
        c.vente(titre=t, nombre=20, date='2011-11-01')
        self.assertRaises(Titre.DoesNotExist, lambda:c.revenu(titre=t, montant=20, date='2011-01-01'))#a pu

    def test_cpt_titre_revenu_frais(self):
        c = Compte_titre.objects.get(id=4)
        t = Titre.objects.get(nom="t2")
        c.revenu(titre=t, montant=20, date='2011-11-02', frais=10)
        self.assertEqual(t.investi(c), 90)
        self.assertEqual(c.solde(), 110)
        cat=Cat.objects.get(id=3)
        tiers=Tiers.objects.get(id=2)
        c.revenu(titre=t,montant=20, frais=20,
                        cat_frais=cat,
                        tiers_frais=tiers,
                        date='2011-11-02')
        self.assertEqual(t.investi(c), 90)
        self.assertEqual(c.solde(), 110)
        self.assertEquals(Ope.objects.filter(compte=c).count(), 4)

    def test_cpt_titre_revenu_virement(self):
        c = Compte_titre.objects.get(id=4)
        t = Titre.objects.get(nom="t2")
        c.revenu(titre=t, montant=20, date='2011-11-02', virement_vers=Compte.objects.get(id=1))
        self.assertEqual(c.solde(), 100)
        self.assertEquals(Ope.objects.filter(compte=c).count(), 4)
        self.assertEqual(Compte.objects.get(id=1).solde(), 60)

    def test_moyen_fusionne(self):
        Moyen.objects.get(id=3).fusionne(Moyen.objects.get(id=2))

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
        v = Virement(Ope.objects.get(id=9))
        self.assertEquals(v.origine.id, 9)
        self.assertEquals(v.dest.id, 10)
        self.assertEquals(v.origine.compte, Compte.objects.get(nom='cpte1'))
        self.assertEquals(v.dest.compte, Compte.objects.get(nom='cptb2'))
        self.assertEquals(v.date, strpdate('2010-01-01'))
        self.assertEquals(v.montant, v.origine.montant * -1)
        self.assertEquals(v.montant, v.dest.montant)
        self.assertEquals(v.montant, 20)
        self.assertEquals(v.__unicode__(), u"cpte1 => cptb2")
        v.date_val = '2011-02-01'
        v.save()
        self.assertEquals(Virement(Ope.objects.get(id=9)).date_val, strpdate('2011-02-01'))

    def test_virement_create(self):
        v = Virement.create(Compte.objects.get(id=1), Compte.objects.get(id=2), 20)
        self.assertEqual(Compte.objects.get(id=1).solde(), 20)
        self.assertEquals(v.origine.compte, Compte.objects.get(nom='cpte1'))
        self.assertEquals(v.dest.compte, Compte.objects.get(nom='cptb2'))
        self.assertEquals(v.origine.id, 9)
        self.assertEquals(v.date, datetime.date.today())
        self.assertEquals(v.montant, v.origine.montant * -1)
        self.assertEquals(v.montant, v.dest.montant)
        self.assertEquals(v.montant, 20)
        v = Virement.create(Compte.objects.get(id=1), Compte.objects.get(id=2), 20,
                            '2010-01-01', 'test_notes')
        self.assertEqual(Compte.objects.get(id=1).solde(), 0)
        self.assertEqual(v.date, '2010-01-01')
        self.assertEqual(v.notes, 'test_notes')

    def test_virement_delete(self):
        v = Virement.create(Compte.objects.get(id=1), Compte.objects.get(id=2), 20)
        v.delete()
        self.assertEquals(Compte.objects.get(nom='cpte1').solde(), 40)
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
