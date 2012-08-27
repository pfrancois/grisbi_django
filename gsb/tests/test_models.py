# -*- coding: utf-8 -*
"""
test models
"""
from __future__ import absolute_import
import os
from .test_base import TestCase
from ..models import Generalite, Compte, Ope, Tiers, Cat, Moyen, Titre, Banque
from ..models import Compte_titre, Virement, Ope_titre, Ib, Exercice, Cours
from ..models import Rapp, Echeance, Gsb_exc, Ex_jumelle_neant
from django.core.exceptions import ValidationError
from django.db import IntegrityError
import datetime
import decimal
from django.conf import settings
from ..utils import strpdate
from operator import attrgetter
from dateutil.relativedelta import relativedelta
from django.db import models

class test_models(TestCase):
    fixtures = ['test.json', 'auth.json']

    def test_models_unicode(self):
        #on test les sortie unicode
        self.assertEquals(Tiers.objects.get(nom="tiers1").__unicode__(), u"tiers1")
        self.assertEquals(Titre.objects.get(nom="t1").__unicode__(), u"t1 (1)")
        self.assertEquals(Banque.objects.get(nom="banque1").__unicode__(), u"banque1")
        self.assertEquals(Cours.objects.get(id=1).__unicode__(), u"le 2009-12-31, 1 t2 : 10")
        self.assertEquals(Cat.objects.get(nom="cat1").__unicode__(), u"cat1(r)")
        self.assertEquals(Ib.objects.get(nom="ib1").__unicode__(), u"ib1")
        self.assertEquals(Exercice.objects.get(nom="exo1").__unicode__(), u"01/01/2010 au 31/10/2010")
        self.assertEquals(Compte.objects.get(nom="cpte1").__unicode__(), u"cpte1")
        self.assertEquals(Ope_titre.objects.get(id=1).__unicode__(), u"1")
        self.assertEquals(Moyen.objects.get(id=1).__unicode__(), u"moyen_rec1 (r)")
        self.assertEquals(Rapp.objects.get(id=1).__unicode__(), u"r1")
        self.assertEquals(Echeance.objects.get(id=1).__unicode__(), u"cpte1=>cptb2 pour 10")
        self.assertEquals(Echeance.objects.get(id=3).__unicode__(), u"20 pour tiers1")
        self.assertEquals(Generalite.objects.get(id=1).__unicode__(), u"1")
        self.assertEquals(Ope.objects.get(id=1).__unicode__(), u"(1) le 2011-08-11 : 10 EUR a tiers1 cpt: cpte1")

    def test_mul(self):
        self.assertEquals(Cours.objects.get(id=4).valeur * Cours.objects.get(id=4).valeur, 25)

    def test_fusionne_error(self):
        #fusion avec un autre type
        self.assertRaises(TypeError, Tiers.objects.get(nom="tiers1").fusionne, Cat.objects.get(id=1))
        #fusion sur lui meme
        self.assertRaises(ValueError, Tiers.objects.get(nom="tiers1").fusionne, Tiers.objects.get(nom="tiers1"))
        #fusion avec un autre type
        self.assertRaises(TypeError, Titre.objects.get(nom="t1").fusionne, Cat.objects.get(id=1))
        #fusion sur lui meme
        self.assertRaises(ValueError, Titre.objects.get(nom="t1").fusionne, Titre.objects.get(nom="t1"))
        #fusion entre deux types de compte different
        self.assertRaises(TypeError, Titre.objects.get(nom="t1").fusionne, Titre.objects.get(nom="autre"))
        #fusion entre deux compte de type difference de cours
        self.assertRaises(Gsb_exc, Titre.objects.get(nom="t4").fusionne, Titre.objects.get(nom="autre"))
        #fusion avec un autre type
        self.assertRaises(TypeError, Banque.objects.get(id=1).fusionne, Cat.objects.get(id=1))
        #fusion sur lui meme
        self.assertRaises(ValueError, Banque.objects.get(id=1).fusionne, Banque.objects.get(id=1))
        #fusion avec un autre type
        self.assertRaises(TypeError, Cat.objects.get(id=1).fusionne, Banque.objects.get(id=1))
        #fusion entre deux cat de type different
        self.assertRaises(TypeError, Cat.objects.get(id=3).fusionne, Cat.objects.get(id=1))
        #fusion sur lui meme
        self.assertRaises(ValueError, Cat.objects.get(id=1).fusionne, Cat.objects.get(id=1))
        #fusion entre deux ib de type different
        self.assertRaises(TypeError, Ib.objects.get(id=3).fusionne, Ib.objects.get(id=1))
        #fusion avec un autre type
        self.assertRaises(TypeError, Ib.objects.get(id=1).fusionne, Banque.objects.get(id=1))
        #fusion sur lui meme
        self.assertRaises(ValueError, Ib.objects.get(id=1).fusionne, Ib.objects.get(id=1))
        #fusion avec un autre type
        self.assertRaises(TypeError, Exercice.objects.get(id=1).fusionne, Banque.objects.get(id=1))
        #fusion sur lui meme
        self.assertRaises(ValueError, Exercice.objects.get(id=1).fusionne, Exercice.objects.get(id=1))
        #fusion avec un autre type
        self.assertRaises(TypeError, Compte.objects.get(id=1).fusionne, Banque.objects.get(id=1))
        #fusion sur lui meme
        self.assertRaises(ValueError, Compte.objects.get(id=1).fusionne, Compte.objects.get(id=1))
        #fusion entre deux compte de type difference
        self.assertRaises(Gsb_exc, Compte.objects.get(id=1).fusionne, Compte.objects.get(id=2))
        #fusion avec un autre type
        self.assertRaises(TypeError, Compte_titre.objects.get(id=4).fusionne, Banque.objects.get(id=1))
        #fusion sur lui meme
        self.assertRaises(ValueError, Compte_titre.objects.get(id=4).fusionne, Compte_titre.objects.get(id=4))
        #fusion avec un autre type
        self.assertRaises(TypeError, Moyen.objects.get(id=1).fusionne, Banque.objects.get(id=1))
        #fusion avec un autre type
        self.assertRaises(ValueError, Moyen.objects.get(id=1).fusionne, Moyen.objects.get(id=2))
        #probleme si fusion d'un moyen settings
        self.assertRaises(ValueError, Moyen.objects.get(id=2).fusionne, Moyen.objects.get(id=3))
        #fusion sur lui meme
        self.assertRaises(ValueError, Moyen.objects.get(id=4).fusionne, Moyen.objects.get(id=4))
        #fusion avec un autre type
        self.assertRaises(TypeError, Rapp.objects.get(id=1).fusionne, Banque.objects.get(id=1))
        #fusion avec lui meme
        self.assertRaises(ValueError, Rapp.objects.get(id=1).fusionne, Rapp.objects.get(id=1))

    def test_tiers_fusionne(self):
        Tiers.objects.get(nom="tiers1").fusionne(Tiers.objects.get(nom="tiers2"))
        #un tiers de moins
        self.assertQuerysetEqual(Tiers.objects.all().order_by('id'), [2, 3, 4, 5, 6, 7, 8, 9], attrgetter("id"))
        #verifie sur les dependance que c'est bien le nouveau tiers
        t = Tiers.objects.get(nom="tiers2")
        #id des operations
        self.assertQuerysetEqual(Ope.objects.filter(tiers=t).order_by('id'), [1, 2, 3, 4, 8], attrgetter("id"))
        #id des echeances
        self.assertQuerysetEqual(Echeance.objects.filter(tiers=t).order_by('id'), [1, 2, 3, 4], attrgetter("id"))

    def test_titre_last_cours(self):
        t = Titre.objects.get(nom="t1")
        self.assertEquals(t.last_cours(), 1)
        self.assertEquals(t.last_cours(rapp=True), 0)
        t = Titre.objects.get(nom="t2")
        self.assertEquals(t.last_cours(), 10)
        self.assertEquals(t.last_cours(rapp=True), 10)

    def test_titre_last_date(self):
        t = Titre.objects.get(nom="t2")
        self.assertEqual(t.last_cours_date(), datetime.date(2011, 12, 17))
        self.assertEqual(t.last_cours_date(rapp=True),  datetime.date(2011, 12, 17))
        t = Titre.objects.get(nom="t1")
        self.assertEqual(t.last_cours_date(rapp=True),  None)
        self.assertEqual(t.last_cours_date(),  datetime.date(2011, 12, 18))


    def test_titre_creation(self):
        #on cree le titre
        t = Titre.objects.create(nom='ceci_est_un_titre', isin="123456789", type='ACT')
        #un titre de plus
        tiers = t.tiers
        self.assertEqual(Tiers.objects.count(), 10)
        self.assertEqual(tiers.nom, 'titre_ ceci_est_un_titre')
        self.assertEqual(tiers.notes, "123456789@ACT")
        self.assertEqual(tiers.is_titre, True)

    def test_titre_fusionne(self):
        Titre.objects.get(nom="t2").fusionne(Titre.objects.get(nom="t1"))
        self.assertQuerysetEqual(Titre.objects.all().order_by('id'), [1, 3, 4], attrgetter("id"))
        #verifie que la fusion des tiers sous jacent
        self.assertQuerysetEqual(Tiers.objects.all().order_by('id'), [1, 2, 3, 5, 6, 7, 8, 9], attrgetter("id"))
        # ce tiers n'existe plus
        self.assertRaises(Tiers.DoesNotExist, lambda:Tiers.objects.get(nom='Titre_ t2'))
        #ok pour les ope (et les tiers sous jacent)
        self.assertQuerysetEqual(Ope.objects.filter(tiers__nom='titre_ t1').order_by('id'), [5, 9, 12, 13], attrgetter("id"))
        #ok pour les ope titre
        self.assertQuerysetEqual(Ope_titre.objects.filter(titre__nom='t1').order_by('id'), [1, 2, 3], attrgetter("id"))
        self.assertQuerysetEqual(Titre.objects.get(nom="t1").ope_titre_set.all(), [3, 2, 1], attrgetter("id"))
        #verifier que les cours ont été fusionneés
        self.assertEquals(Titre.objects.get(nom='t1').cours_set.count(), 6)

    def test_titre_save_perso(self):
        #creation d'un nouveau titre
        t = Titre.objects.create(nom="t3", isin="4", type='ACT')
        self.assertEqual(Tiers.objects.count(), 10)
        self.assertEqual(Tiers.objects.filter(is_titre=True).count(), 5)
        self.assertEqual(Tiers.objects.get(nom="titre_ t3").nom, "titre_ t3")
        self.assertEqual(Tiers.objects.get(nom="titre_ t3").notes, "4@ACT")
        t.tiers.notes = ""
        t.save()
        self.assertEqual(Tiers.objects.get(nom="titre_ t3").notes, "4@ACT")

    def test_titre_investi(self):
        c = Compte_titre.objects.get(id=4)
        t = Titre.objects.get(nom="t2")
        self.assertEquals(t.investi(c, rapp=True), 100)
        Compte_titre.objects.get(id=5).achat(titre=t, nombre=20, date='2011-01-01')
        self.assertEquals(t.investi(), 1620)
        self.assertEquals(t.investi(c), 1600)
        self.assertEquals(t.investi(datel='2011-07-01'), 20)
        self.assertEquals(t.investi(compte=c, datel='2011-07-01'), 0)
        self.assertEquals(t.investi(compte= Compte_titre.objects.get(id=5), exclude_id=16), 0)


    def test_titre_nb(self):
        c = Compte_titre.objects.get(id=4)
        t = Titre.objects.get(nom="t2")
        Compte_titre.objects.get(id=5).achat(titre=t, nombre=20, date='2011-01-01')
        o = Ope.objects.filter(compte=Compte_titre.objects.get(id=5), date='2011-01-01')[0]
        o.rapp = Rapp.objects.get(id=1)
        o.save()
        self.assertEquals(t.nb(), 190)
        self.assertEquals(t.nb(c), 170)
        self.assertEquals(t.nb(datel='2011-07-01'), 20)
        self.assertEquals(t.nb(compte=c, datel='2011-07-01'), 0)
        self.assertEquals(t.nb(rapp=True), 40)
        self.assertEquals(t.nb(rapp=True, datel='2010-07-01'), 0)
        self.assertEquals(t.nb(rapp=True, compte=Compte_titre.objects.get(id=5), datel='2010-07-01'), 0)
        self.assertEquals(t.nb( compte=Compte_titre.objects.get(id=5), exclude_id=4), 0)

    def test_titre_encours(self):
        c = Compte_titre.objects.get(id=4)
        t = Titre.objects.get(nom="t2")
        self.assertEquals(t.encours(datel='1900-01-01'), 0)
        self.assertEquals(t.encours(), 1700)
        self.assertEquals(t.encours(rapp=True, compte=c), 1500)
        Compte_titre.objects.get(id=5).achat(titre=t, nombre=20, date='2011-01-01', prix=20)
        o = Ope.objects.filter(compte=Compte_titre.objects.get(id=5), date='2011-01-01')[0]
        self.assertEquals(t.encours(rapp=True), 1500)
        o.rapp = Rapp.objects.get(id=1)
        o.save()
        self.assertEquals(t.encours(rapp=True), 1700)
        self.assertEquals(t.encours(), 1900)
        self.assertEquals(t.encours(c), 1700)
        self.assertEquals(t.encours(datel='2011-07-01'), 400)
        self.assertEquals(t.encours(compte=c, datel='2011-07-01'), 0)
        self.assertEquals(t.encours(compte=c, datel='2011-11-01'), 100)
        self.assertEquals(t.encours(rapp=True, datel='2011-07-01'), 400)
        self.assertEquals(t.encours(rapp=True, compte=c), 1500)
        self.assertEquals(t.encours(rapp=True, compte=c, datel='2011-11-01'), 0)


    #pas de test specifique pour cours

    def test_banque_fusionne(self):
        new_b = Banque.objects.get(cib="10001")
        Banque.objects.get(cib="99999").fusionne(new_b)
        self.assertQuerysetEqual(Banque.objects.all().order_by('id'), [1], attrgetter("id"))
        self.assertQuerysetEqual(Compte.objects.filter(banque__cib='10001').order_by('id'), [1, 2, 3, 4, 5, 6], attrgetter("id"))

    def test_cat_fusionne(self):
        Cat.objects.get(nom="cat2").fusionne(Cat.objects.get(nom="cat1"))
        self.assertQuerysetEqual(Cat.objects.all().order_by('id'), [1, 3, 4, 64, 65], attrgetter("id"))
        self.assertQuerysetEqual(Ope.objects.filter(cat__nom="cat1").all().order_by('id'), [1, 2, 3, 4], attrgetter("id"))
        self.assertQuerysetEqual(Echeance.objects.filter(cat__nom="cat1").all().order_by('id'), [1, 2, 3, 4], attrgetter("id"))

    def test_ib_fusionne(self):
        Ib.objects.get(nom="ib2").fusionne(Ib.objects.get(nom="ib1"))
        self.assertQuerysetEqual(Ib.objects.all().order_by('id'), [1, 3, 4], attrgetter("id"))
        self.assertQuerysetEqual(Ope.objects.filter(ib__nom="ib1").all().order_by('id'), [3, 4], attrgetter("id"))
        self.assertQuerysetEqual(Echeance.objects.filter(ib__nom="ib1").all().order_by('id'), [1, 2], attrgetter("id"))

    def test_exo_fusionne(self):
        exo = Exercice.objects.get(id=1)
        Exercice.objects.get(id=2).fusionne(exo)
        self.assertQuerysetEqual(Exercice.objects.all().order_by('id'), [1], attrgetter("id"))
        #on verifie qu'il prend la totalite de la duration
        exo = Exercice.objects.get(id=1)
        self.assertEquals(exo.date_debut, strpdate('2010-1-1'))
        self.assertEquals(exo.date_fin, strpdate('2011-12-31'))
        #verification des liens
        self.assertQuerysetEqual(Ope.objects.filter(exercice__id=1).all().order_by('id'), [8], attrgetter("id"))
        self.assertQuerysetEqual(Echeance.objects.filter(exercice__id=1).all().order_by('id'), [1, 2], attrgetter("id"))

    def test_compte_solde_normal(self):
        #version de base
        self.assertEqual(Compte.objects.get(id=1).solde(), -1460)
        #si pas d'operation en stock dans le compte
        self.assertEqual(Compte.objects.get(id=6).ope_set.count(), 0)
        self.assertEqual(Compte.objects.get(id=6).solde(), 0)
        #seulement les operations rapproches
        self.assertEqual(Compte.objects.get(id=1).solde(rapp=True), 20)
        #a une date anterieur
        self.assertEqual(Compte.objects.get(id=1).solde(datel=strpdate('2009-01-01')), 0)
        #solde rappro
        self.assertEqual(Compte.objects.get(id=1).solde_rappro(), 20)
        self.assertEqual(Compte.objects.get(id=1).date_rappro(), strpdate('2011-08-11'))
        self.assertEqual(Compte.objects.get(id=3).date_rappro(), None)

    def test_creation_compte_compte_titre(self):
        #on cree un compte titre via compte
        Compte.objects.create(nom="toto", type="t")
        self.assertIsInstance(Compte_titre.objects.get(nom="toto"), Compte_titre)
        #on cree un compte normal
        Compte.objects.create(nom="hjhghj", type="b")
        self.assertIsInstance(Compte.objects.get(nom="hjhghj"), Compte)

    def test_compte_absolute_url(self):
        c = Compte.objects.get(id=1)
        absolute = c.get_absolute_url()
        self.assertEqual(absolute, '/compte/1/')

    def test_compte_titre_absolute_url(self):
        self.assertEqual(Compte_titre.objects.get(id=4).get_absolute_url(), '/compte/4/')

    def test_compte_fusion(self):
        n = Compte.objects.get(id=3)
        o = Compte.objects.get(id=2)
        #fusion avec un compte ferme
        self.assertRaises(Gsb_exc, lambda:o.fusionne(Compte.objects.get(id=6)))
        #fusion ferme
        self.assertRaises(Gsb_exc, lambda:Compte.objects.get(id=6).fusionne(o))
        #fusion effective
        o.fusionne(n)
        #les ope relatives
        self.assertQuerysetEqual(Ope.objects.filter(compte__id=3).all().order_by('id'), [3, 4, 6, 14], attrgetter("id"))
        self.assertQuerysetEqual(Echeance.objects.filter(compte__id=3).all().order_by('id'), [2], attrgetter("id"))
        self.assertQuerysetEqual(Echeance.objects.filter(compte_virement__id=3).all().order_by('id'), [1], attrgetter("id"))
        #fusion de compte_titre
        Compte.objects.get(id=4).fusionne(Compte.objects.get(id=5))
        self.assertEquals(Ope.objects.get(id=5).compte_id, 5)
        self.assertEquals(Ope_titre.objects.get(id=1).compte_id, 5)

    def test_compte_titre_achat_vente_error(self):
        c1 = Compte_titre.objects.get(id=4)
        c2 = Compte_titre.objects.get(id=5)
        #probleme si on utilise pas un titre dans le param titre
        self.assertRaises(TypeError, c1.achat, c2, 20, '2011-01-01')
        self.assertRaises(TypeError, c1.vente, c2, 20, '2011-01-01')
        self.assertRaises(TypeError, c1.revenu, c2, 20, '2011-01-01')

    def test_compte_titre_solde(self):
        c = Compte_titre.objects.get(id=4)
        t = Titre.objects.get(nom="t2")
        self.assertEqual(c.solde(), 1701)
        #variation des cours (et donc du solde)
        t.cours_set.create(date='2011-12-18', valeur=2)
        self.assertEqual(c.solde(), 341)
        #solde a une date anterieur
        self.assertEqual(c.solde(datel=strpdate('2011-01-01')), 0)
        self.assertEqual(c.solde(rapp=True), 0)
        self.assertEqual(c.solde_titre(rapp=True), 100)

    def test_compte_titre_achat_sans_virement(self):
        c = Compte_titre.objects.get(id=4)
        self.assertEqual(c.nom, u'cpt_titre1')
        t = Titre.objects.get(nom="t1")
        self.assertEqual(t.investi(c), 2)
        c.achat(titre=t, nombre=20, date='2011-01-01')
        self.assertEqual(t.investi(c), 22)
        tall = c.titre.all().distinct()
        self.assertEqual(tall.count(), 2)
        self.assertEqual(tall[0].last_cours, 1)
        self.assertEqual(c.solde(), 1701)
        c.achat(titre=t, nombre=20, prix=2, date='2011-01-01')
        self.assertEqual(c.solde(), 1681)

    def test_compte_titre_achat_avec_frais(self):
        c = Compte_titre.objects.get(id=4)
        t = Titre.objects.get(nom="t1")
        #utilisation des cat et tiers par defaut
        c.achat(titre=t, nombre=20, frais=20, date='2011-07-01')
        self.assertEqual(c.solde(), 1681)
        self.assertEqual(t.investi(c), 42)
        o = Ope.objects.filter(compte=c, date='2011-07-01', notes__icontains='frais')[0]
        self.assertEqual(o.cat_id, 65)
        self.assertEqual(o.montant, -20)
        self.assertEquals(o.notes, u"frais 20@1")
        self.assertEquals(o.moyen_id, 2)
        #utilisa des cat et tiers donnes
        c.achat(titre=t, nombre=20, frais=20,
                cat_frais=Cat.objects.get(id=3),
                tiers_frais=Tiers.objects.get(id=2),
                date='2011-07-02')
        self.assertEqual(c.solde(), 1661)
        self.assertEqual(t.investi(c), 62)
        o = Ope.objects.filter(compte=c, date='2011-07-02', notes__icontains='frais')[0]
        self.assertEqual(o.tiers_id, 2)
        self.assertEqual(o.cat_id, 3)
        self.assertEqual(o.montant, -20)
        self.assertEquals(o.notes, u"frais 20@1")
        self.assertEquals(o.moyen_id, 2)

    def test_compte_titre_achat_avec_virement(self):
        c = Compte_titre.objects.get(id=5)
        t = Titre.objects.get(nom="t1")
        c.achat(titre=t, nombre=20, date='2011-01-01', virement_de=Compte.objects.get(id=1))
        self.assertEqual(t.investi(c), 20)
        self.assertEqual(c.solde(), 20)
        self.assertEquals(Ope.objects.filter(compte=c).count(), 2)
        self.assertEqual(Compte.objects.get(id=1).solde(), -1480)

    def test_compte_titre_vente_simple(self):
        c = Compte_titre.objects.get(id=4)
        self.assertEqual(c.nom, u'cpt_titre1')
        t = Titre.objects.get(nom="t2")
        self.assertEqual(t.investi(c), 1600)
        self.assertRaises(Titre.DoesNotExist, lambda:c.vente(titre=t, nombre=20, date='2011-01-01'))#trop tot
        self.assertRaises(Titre.DoesNotExist, lambda:c.vente(titre=t, nombre=40, date='2011-11-02'))#montant trop eleve car entre les deux operations
        self.assertRaises(Titre.DoesNotExist, lambda:c.vente(titre=t, nombre=2000, date='2011-12-31'))#montant trop eleve car entre les deux operations
        c.vente(titre=t, nombre=20, date='2011-11-01')
        a_test = t.investi(c)
        self.assertEqual(a_test, decimal.Decimal('1500'))
        tall = c.liste_titre()
        self.assertEqual(len(tall), 2)
        self.assertRaises(Titre.DoesNotExist, lambda:c.vente(titre=t, nombre=20, date='2011-11-01'))#a pu de titre
        self.assertEqual(c.solde(), 1521)


    def test_compte_titre_vente_avec_frais(self):
        #on cree le compte
        c = Compte_titre.objects.create(type="t", nom="c_test", moyen_credit_defaut=Moyen.objects.get(id=1), moyen_debit_defaut=Moyen.objects.get(id=2))
        #on cree le titre
        t = Titre.objects.create(nom="t3", isin="xxxxxxx")
        #utilisation des cat et tiers par defaut
        Ope_titre.objects.create(titre=t, compte=c, nombre=15, date=strpdate('2011-01-01'), cours=10)
        c.vente(titre=t, nombre=5, frais=20, date='2011-11-01', prix=5)
        self.assertEqual(c.solde_espece(), -145)
        self.assertEqual(c.solde_titre(), 50)
        self.assertEqual(c.solde(), -95)
        self.assertEqual(t.investi(c), 120)#attention, on prend le cmup avec les frais
        o = Ope.objects.filter(compte=c, date='2011-11-01', notes__icontains='frais')[0]
        self.assertEqual(o.cat_id, 65)
        self.assertEqual(o.montant, -20)
        self.assertEquals(o.notes, u"frais -5@5")
        self.assertEquals(o.moyen_id, 2)
        #"utilisa des cat et tiers donnes
        c.vente(titre=t, nombre=10, frais=20,
                cat_frais=Cat.objects.get(id=3),
                tiers_frais=Tiers.objects.get(id=2),
                date='2011-11-02', prix=10)
        self.assertEqual(c.solde(), -65)
        self.assertEqual(t.investi(c), 0)
        o = Ope.objects.filter(compte=c, date='2011-11-02', notes__icontains='frais')[0]
        self.assertEqual(o.tiers_id, 2)
        self.assertEqual(o.cat_id, 3)
        self.assertEqual(o.montant, -20)
        self.assertEquals(o.notes, u"frais -10@10")
        self.assertEquals(o.moyen_id, 2)

    def test_compte_titre_vente_avec_virement(self):
    #on cree le compte
        c = Compte_titre.objects.create(type="t", nom="c_test", moyen_credit_defaut=Moyen.objects.get(id=1), moyen_debit_defaut=Moyen.objects.get(id=2))
        #on cree le titre
        t = Titre.objects.create(nom="t_test", isin="xxxxxxx")
        #Ope_titre.objects.create(titre=t, compte=c, nombre=15, date=strpdate('2011-01-01'), cours=10)
        c.achat(titre=t, prix=10, nombre=15, date='2011-11-01')
        c.vente(titre=t, prix=5, nombre=5, date='2011-11-02', virement_vers=Compte.objects.get(id=1))
        self.assertEqual(t.investi(c), decimal.Decimal('100'))
        self.assertEqual(t.nb(c), 10)
        self.assertEqual(c.solde(), -100)
        self.assertEquals(Ope.objects.filter(compte=c).count(), 4)
        self.assertEqual(Compte.objects.get(id=1).solde(), -1460 + 25)#montant de l'operation

    def test_compte_titre_revenu_simple(self):
        c = Compte_titre.objects.get(id=4)
        t = Titre.objects.get(nom="t2")
        self.assertRaises(Titre.DoesNotExist, lambda:c.revenu(titre=t, montant=20, date='2011-01-01'))#trop tot
        c.revenu(titre=t, montant=20, date='2011-11-02')
        self.assertEqual(t.investi(c), 1580)
        self.assertEqual(c.solde(), 1721)
        c.vente(titre=t, nombre=20, date='2011-11-01')
        self.assertRaises(Titre.DoesNotExist, lambda:c.revenu(titre=t, montant=20, date='2011-01-01'))#a pu

    def test_compte_titre_revenu_frais(self):
        c = Compte_titre.objects.get(id=4)
        t = Titre.objects.get(nom="t2")
        #on cree un revenu avec des frais
        c.revenu(titre=t, montant=20, date='2011-11-02', frais=10)
        self.assertEqual(t.investi(c), 1590)
        self.assertEqual(c.solde(), 1711)
        cat = Cat.objects.get(id=3)
        tiers = Tiers.objects.get(id=2)
        #second revenu avec des frais mais ratache a autre chose que le titre
        c.revenu(titre=t, montant=20, frais=20,
                 cat_frais=cat,
                 tiers_frais=tiers,
                 date='2011-11-02')
        self.assertEqual(t.investi(c), 1570)
        self.assertEqual(c.solde(), 1711)
        self.assertEquals(Ope.objects.filter(compte=c).count(), 11)

    def test_compte_titre_revenu_virement(self):
        c = Compte_titre.objects.get(id=4)
        t = Titre.objects.get(nom="t2")
        c.revenu(titre=t, montant=20, date='2011-11-02', virement_vers=Compte.objects.get(id=1))
        self.assertEqual(c.solde(), 1701)
        self.assertEquals(Ope.objects.filter(compte=c).count(), 9)
        self.assertEqual(Compte.objects.get(id=1).solde(), -1440)

    def test_compte_titre_liste_titre(self):
        c = Compte_titre.objects.get(id=4)
        self.assertQuerysetEqual(c.liste_titre(), [u't1', u't2'], attrgetter("nom"))
        self.assertQuerysetEqual(c.liste_titre(rapp=True), ['t2'], attrgetter("nom"))
        self.assertQuerysetEqual(c.liste_titre(datel='2010-01-01'), [], attrgetter("nom"))

    def test_compte_titre_save(self):
        c = Compte_titre.objects.get(id=4)
        c.type = 'b'
        c.save()
        self.assertEqual(Compte_titre.objects.get(id=4).type, 't')

    def test_compte_titre_date_rappro(self):
        self.assertEqual(Compte_titre.objects.get(id=4).date_rappro(), strpdate('2011-11-30'))
        self.assertEqual(Compte_titre.objects.get(id=5).date_rappro(), None)

    def test_ope_titre_save(self):
        t = Titre.objects.create(nom="t3", isin="xxxxxxx")
        c = Compte_titre.objects.create(type="t", nom="c_test", moyen_credit_defaut=Moyen.objects.get(id=1), moyen_debit_defaut=Moyen.objects.get(id=2))
        #creation d'une nouvelle operation
        Ope_titre.objects.create(titre=t, compte=c, nombre=15, date=strpdate('2011-01-01'), cours=10)
        Ope_titre.objects.create(titre=t, compte=c, nombre=5, date='2011-01-02', cours=20)
        o = Ope_titre.objects.get(id=5)
        self.assertEqual(o.ope.montant, -100)#juste verification
        self.assertEqual(t.nb(c), 20)
        self.assertEqual(t.investi(c), 250)
        self.assertEqual(t.encours(c), 20 * 20)
        #en fait on s'est trompé, c'est une vente
        o.nombre = -5
        o.save()
        o = Ope_titre.objects.get(id=5)
        self.assertEqual(o.ope.id, 17)
        self.assertEqual(o.ope_pmv.id, 18)
        self.assertEqual(t.nb(c), 10)
        self.assertEqual(t.investi(c), 100)
        self.assertEqual(t.encours(c), 10 * 20)
        #finalement c'etait vraiment ca
        o = Ope_titre.objects.get(id=5)
        o.nombre = 10
        o.save()
        self.assertEqual(t.nb(c), 25)
        self.assertEqual(t.investi(c), 350)
        self.assertEqual(t.encours(c), 25*20)

    def test_ope_titre_moins_value(self):
        t = Titre.objects.create(nom="t3", isin="xxxxxxx")
        c = Compte_titre.objects.create(type="t", nom="c_test", moyen_credit_defaut=Moyen.objects.get(id=1), moyen_debit_defaut=Moyen.objects.get(id=2))
        Ope_titre.objects.create(titre=t, compte=c, nombre=15, date=strpdate('2011-01-01'), cours=10)
        Ope_titre.objects.create(titre=t, compte=c, nombre=-5, date='2011-01-02', cours=5)
        o = Ope.objects.filter(compte=c).filter(date='2011-01-02')[0]
        self.assertEqual(o.id, 17)
        self.assertEqual(o.montant, 50)#desinvestissement
        o = Ope.objects.filter(compte=c).filter(date='2011-01-02')[1]
        self.assertEqual(o.id, 18)
        self.assertEqual(o.montant, -25)#desinves!


    def test_ope_titre_save2(self):
        t = Titre.objects.create(nom="t3", isin="xxxxxxx")
        c = Compte_titre.objects.create(type="t", nom="c_test", moyen_credit_defaut=Moyen.objects.get(id=1), moyen_debit_defaut=Moyen.objects.get(id=2))
        #creation d'une nouvelle operation
        o = Ope_titre.objects.create(titre=t, compte=c, nombre=15, date=strpdate('2011-01-01'), cours=10)
        o_id = o.id
        self.assertEqual(o.ope.id, 16)
        self.assertEqual(o.ope.montant, -150)
        self.assertEqual(o.ope.moyen_id, 2)
        self.assertEqual(t.investi(c), 150)
        self.assertEqual(o. ope.notes, "15@10")
        #on verifie qu'il creer bien un cours a la date
        self.assertEqual(Cours.objects.get(date=strpdate('2011-01-01'), titre=t).valeur, 10)
        #on vend
        o = Ope_titre.objects.create(titre=t, compte=c, nombre=-10, date='2011-01-02', cours=15)
        self.assertEqual(o.ope.id, 17)
        self.assertEqual(o.ope.montant, 100)
        self.assertEqual(o.ope.moyen_id, 1)
        self.assertEqual(o.ope_pmv.id, 18)
        self.assertEqual(o.ope_pmv.montant, 50)
        self.assertEqual(o.ope_pmv.moyen_id, 1)
        self.assertEqual(o.ope_pmv.cat.nom, 'Revenus de placement:Plus-values')
        self.assertEqual(o. ope.notes, "-10@15")
        self.assertEqual(t.investi(c), 50)
        self.assertEqual(t.encours(c), 5 * 15)
        #on vend cez qui reste
        o = Ope_titre.objects.create(titre=t, compte=c, nombre=-5, date='2011-01-03', cours=20)
        self.assertEqual(t.investi(c), 0)
        self.assertEqual(o.ope.montant, 50)
        self.assertEqual(o.ope_pmv.montant, 50)
        self.assertEqual(t.encours(c), 0)


    def test_ope_titre_get_absolute_url(self):
        self.assertEqual(Ope_titre.objects.get(id=1).get_absolute_url(), '/ope_titre/1/')

    def test_moyen_fusionne(self):
        Moyen.objects.get(id=3).fusionne(Moyen.objects.get(id=2))
        self.assertQuerysetEqual(Moyen.objects.all().order_by('id'), [1, 2, 4, 5], attrgetter("id"))
        self.assertQuerysetEqual(Compte.objects.filter(moyen_credit_defaut__id=2).all().order_by('id'), [], attrgetter("id"))
        self.assertQuerysetEqual(Compte.objects.filter(moyen_debit_defaut__id=2).all().order_by('id'), [1, 2, 3, 4, 5], attrgetter("id"))
        self.assertQuerysetEqual(Echeance.objects.filter(moyen__id=2).all().order_by('id'), [1, 2], attrgetter("id"))
        self.assertQuerysetEqual(Echeance.objects.filter(moyen_virement__id=2).all().order_by('id'), [], attrgetter("id"))
        self.assertQuerysetEqual(Ope.objects.filter(moyen__id=2).all().order_by('id'), [2, 3, 4, 12], attrgetter("id"))

    def test_rapp_compte(self):
        self.assertEquals(Rapp.objects.get(id=1).compte, 2)
        self.assertEquals(Rapp.objects.get(id=2).compte, None)

    def test_rapp_solde(self):
        self.assertEquals(Rapp.objects.get(id=1).solde, 30)
        self.assertEquals(Rapp.objects.get(id=2).solde, 0)

    def test_rapp_fusionne(self):
        Rapp.objects.get(id=1).fusionne(Rapp.objects.get(id=2))
        self.assertQuerysetEqual(Ope.objects.filter(rapp__id=2).all().order_by('id'), [3, 8], attrgetter("id"))

    def test_echeance_save(self):
        #on ne peut sauver une echeance avec un virement sur un meme compte
        self.assertRaises(ValidationError, lambda:Echeance.objects.create(date=strpdate('2011-01-01'),
                                                                          compte=Compte.objects.get(id=1),
                                                                          montant=2,
                                                                          tiers=Tiers.objects.get(id=2),
                                                                          compte_virement=Compte.objects.get(id=1)))

    def test_echeance_calculnext(self):
        self.assertEquals(Echeance.objects.get(id=1).calcul_next(), None)
        self.assertEquals(Echeance.objects.get(id=3).calcul_next(), strpdate('2011-11-01'))
        self.assertEquals(Echeance.objects.get(id=4).calcul_next(), strpdate('2011-11-13'))
        self.assertEquals(Echeance.objects.get(id=5).calcul_next(), strpdate('2011-12-30'))
        self.assertEquals(Echeance.objects.get(id=6).calcul_next(), strpdate('2013-10-30'))
        self.assertEquals(Echeance.objects.get(id=7).calcul_next(), None)
        self.assertEquals(Echeance.objects.get(id=8).calcul_next(), None)

    def test_generalite_gen(self):
        self.assertEquals(Generalite.gen().id, 1)
        #on efface afin de le recreer
        Generalite.gen().delete()
        self.assertEquals(Generalite.gen().id, 1)
        self.assertEquals(Generalite.gen().titre, "isbi")

    def test_generalite_dev_g(self):
        self.assertEqual(Generalite.dev_g(), 'EUR')

    def test_generalite_save(self):
        Generalite.objects.create()
        self.assertEquals(Generalite.objects.count(), 1)

    def test_ope_absolute_url(self):
        self.assertEqual(Ope.objects.get(id=1).get_absolute_url(), '/ope/1/')

    def test_ope_non_mere(self):
        self.assertQuerysetEqual(Ope.non_meres().order_by('id'), [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15], attrgetter("id"))

    def test_ope_save(self):
        c = Compte.objects.get(id=1)
        t = Tiers.objects.get(id=1)
        #test pas defaut
        o = Ope.objects.create(compte=c, date='2010-01-01', montant=20, tiers=t)
        self.assertEquals(o.moyen_id, 1)
        o = Ope.objects.create(compte=c, date='2010-01-01', montant=-20, tiers=t)
        self.assertEquals(o.moyen_id, 2)
        o = Ope.objects.create(compte=c, date='2010-01-01', montant=-20, tiers=t, moyen=Moyen.objects.get(id=2))
        self.assertEquals(o.moyen_id, 2)
        c.moyen_credit_defaut = None
        o = Ope.objects.create(compte=c, date='2010-01-01', montant=20, tiers=t)
        self.assertEquals(o.moyen_id, 1)
        c.moyen_debit_defaut = None
        o = Ope.objects.create(compte=c, date='2010-01-01', montant=-20, tiers=t)
        self.assertEquals(o.moyen_id, 2)

    def test_pre_delete_ope_rapp(self):
        #ope rapp
        self.assertRaises(IntegrityError, Ope.objects.get(id=3).delete)

    def test_pre_delete_ope_mere(self):
        o = Ope.objects.get(id=8)
        #on transforme l'ope 1 en ope mere
        o.mere_id = 4
        o.save()
        #on ne peut effacer un mere qui a encore des filles
        self.assertRaises(IntegrityError, Ope.objects.get(id=4).delete)

    def test_pre_delete_ope_rapp_mere(self):
        o = Ope.objects.get(id=8)
        o.rapp_id = None
        o.save()
        #on transforme l'ope 3 en ope mere
        o.mere_id = 3
        o.save()
        o = Ope.objects.get(id=3)
        o.rapp_id = 1
        o.save()
        #on ne peut effacer fille qui a une mere rapp
        o = Ope.objects.get(id=8)
        self.assertRaises(IntegrityError, o.delete)

    def test_pre_delete_ope_rapp_jumelle(self):
        o = Ope.objects.get(id=7)
        o.rapp_id = 1
        o.save()
        self.assertRaises(IntegrityError, Ope.objects.get(id=6).delete)

    def test_pre_delete_ope_titre_rapp(self):
        Compte_titre.objects.get(id=5).achat(titre=Titre.objects.get(id=1), nombre=20, date='2011-01-01')
        o = Ope.objects.filter(compte=Compte_titre.objects.get(id=5), date='2011-01-01')[0]
        o.rapp = Rapp.objects.get(id=1)
        o.save()
        self.assertRaises(IntegrityError, Ope_titre.objects.get(id=o.ope_titre.id).delete)

    def test_virement_error(self):
        #_non_ope
        self.assertRaises(TypeError, lambda:Virement(Generalite.gen()))
        #creation avec autre que ope
        c = Compte.objects.get(id=1)
        nc = Generalite.gen()
        v = Virement()
        self.assertRaises(TypeError, lambda:v.create(compte_origine=nc, compte_dest=c, montant=2))
        self.assertRaises(TypeError, lambda:v.create(compte_origine=c, compte_dest=nc, montant=2))
        #save non init
        self.assertRaises(Gsb_exc, lambda:Virement().save())
        #form unbound
        self.assertRaises(Gsb_exc, lambda:Virement().init_form())

    def test_virement_verif_property(self):
        Virement.create(Compte.objects.get(id=1), Compte.objects.get(id=2), 20, date='2010-01-01', notes='test_notes')
        v = Virement(Ope.objects.get(id=16))
        self.assertEquals(v.origine.id, 16)
        self.assertEquals(v.dest.id, 17)
        self.assertEquals(v.origine.compte, Compte.objects.get(nom='cpte1'))
        self.assertEquals(v.dest.compte, Compte.objects.get(nom='cptb2'))
        self.assertEquals(v.date, strpdate('2010-01-01'))
        self.assertEquals(v.montant, v.origine.montant * -1)
        self.assertEquals(v.montant, v.dest.montant)
        self.assertEquals(v.montant, 20)
        self.assertEquals(v.__unicode__(), u"cpte1 => cptb2")
        v.date_val = '2011-02-01'
        v.pointe = True
        v.save()
        self.assertEquals(Virement(Ope.objects.get(id=16)).date_val, strpdate('2011-02-01'))

        self.assertEquals(v.pointe, True)


    def test_virement_create(self):
        v = Virement.create(Compte.objects.get(id=1), Compte.objects.get(id=2), 20)
        self.assertEqual(Compte.objects.get(id=1).solde(), -1480)
        self.assertEquals(v.origine.compte, Compte.objects.get(nom='cpte1'))
        self.assertEquals(v.dest.compte, Compte.objects.get(nom='cptb2'))
        self.assertEquals(v.origine.id, 16)
        self.assertEquals(v.date, datetime.date.today())
        self.assertEquals(v.montant, v.origine.montant * -1)
        self.assertEquals(v.montant, v.dest.montant)
        self.assertEquals(v.montant, 20)
        v = Virement.create(Compte.objects.get(id=1), Compte.objects.get(id=2), 20,
                            '2010-01-01', 'test_notes')
        self.assertEqual(Compte.objects.get(id=1).solde(), -1500)
        self.assertEqual(v.date, '2010-01-01')
        self.assertEqual(v.notes, 'test_notes')

    def test_virement_delete(self):
        v = Virement.create(Compte.objects.get(id=1), Compte.objects.get(id=2), 20)
        v.delete()
        self.assertEquals(Compte.objects.get(nom='cpte1').solde(), -1460)
        self.assertEquals(Compte.objects.get(nom='cptb2').solde(), -92)

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
