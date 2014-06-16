# -*- coding: utf-8 -*
"""
test models
"""
from __future__ import absolute_import
import datetime
import time
import decimal
from operator import attrgetter

import mock
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db import transaction
from django.conf import settings

from .test_base import TestCase
from .. import models
from ..io import import_base
from .. import utils
from .. import forms


__all__ = ['Test_models', 'Test_models2']


class Test_models(TestCase):
    fixtures = ['test.yaml']

    def setUp(self):
        super(Test_models, self).setUp()
        # on cree les elements indispensables
        import_base.Cat_cache(self.request_get('toto'))
        import_base.Moyen_cache(self.request_get('toto'))
        import_base.Tiers_cache(self.request_get('toto'))

    def test_models_unicode(self):
        """on test les sortie unicode"""
        self.assertEquals(models.Config.objects.get(id=1).__unicode__(), u"1")
        self.assertEquals(models.Tiers.objects.get(nom="tiers1").__unicode__(), u"tiers1")
        self.assertEquals(models.Titre.objects.get(nom="t1").__unicode__(), u"t1 (1)")
        self.assertEquals(models.Banque.objects.get(nom="banque1").__unicode__(), u"banque1")
        self.assertEquals(models.Cours.objects.get(id=1).__unicode__(), u"le 18/12/2011, 1 t1 : 1 EUR")
        self.assertEquals(models.Cat.objects.get(nom="cat1").__unicode__(), u"cat1(r)")
        self.assertEquals(models.Ib.objects.get(nom="ib1").__unicode__(), u"ib1")
        self.assertEquals(models.Exercice.objects.get(nom="exo1").__unicode__(), u"01/01/2010 au 31/12/2010")
        self.assertEquals(models.Compte.objects.get(nom="cpte1").__unicode__(), u"cpte1")
        self.assertEquals(models.Ope_titre.objects.get(id=1).__unicode__(), u"(1) achat de 1 t1 (1) à 1 EUR le 18/12/2011 cpt:cpt_titre1")
        self.assertEquals(models.Moyen.objects.get(id=1).__unicode__(), u"moyen_dep1 (d)")
        self.assertEquals(models.Rapp.objects.get(id=1).__unicode__(), u"cpte1201101")
        self.assertEquals(models.Echeance.objects.get(id=1).__unicode__(), u"(1) cpte1=>cptb2 de 10 (ech:30/10/2011)")
        self.assertEquals(models.Echeance.objects.get(id=3).__unicode__(), u"(3) cpte1 à tiers1 de -20 (ech:30/10/2011)")
        self.assertEquals(models.Ope.objects.get(id=1).__unicode__(), u"(1) le 18/12/2011 : -1 EUR a titre_ t1 cpt: cpt_titre1")

    def test_models_unicode2(self):
        """sortie unicode d'une vente de titre"""
        models.Compte.objects.get(nom="cpt_titre1").vente(titre=models.Titre.objects.get(nom="t1"), nombre=1, date='2011-12-20')
        self.assertEquals(models.Ope_titre.objects.get(id=5).__unicode__(), u"(5) vente de 1 t1 (1) à 1 EUR le 20/12/2011 cpt:cpt_titre1")

    def test_fusionne_error(self):
        """les erreur de fusions, toutes en un seul test"""
        # fusion avec un autre type
        self.assertRaises(TypeError, models.Tiers.objects.get(nom="tiers1").fusionne, models.Cat.objects.get(id=1))
        # fusion sur lui meme
        self.assertRaises(ValueError, models.Tiers.objects.get(nom="tiers1").fusionne, models.Tiers.objects.get(nom="tiers1"))
        # fusion entre deu tiers differents
        self.assertRaises(ValueError, models.Tiers.objects.get(nom="titre_ t1").fusionne, models.Tiers.objects.get(nom="tiers1"))
        # fusion avec un autre  d'objet
        self.assertRaises(TypeError, models.Titre.objects.get(nom="t1").fusionne, models.Cat.objects.get(id=1))
        # fusion sur lui meme
        self.assertRaises(ValueError, models.Titre.objects.get(nom="t1").fusionne, models.Titre.objects.get(nom="t1"))
        # fusion entre deux types de titre different
        self.assertRaises(TypeError, models.Titre.objects.get(nom="t1").fusionne, models.Titre.objects.get(nom="autre"))
        # fusion avec un autre type
        self.assertRaises(TypeError, models.Banque.objects.get(id=1).fusionne, models.Cat.objects.get(id=1))
        # fusion sur lui meme
        self.assertRaises(ValueError, models.Banque.objects.get(id=1).fusionne, models.Banque.objects.get(id=1))
        # fusion avec un autre type
        self.assertRaises(TypeError, models.Cat.objects.get(id=1).fusionne, models.Banque.objects.get(id=1))
        # fusion entre deux cat de type different
        self.assertRaises(TypeError, models.Cat.objects.get(id=3).fusionne, models.Cat.objects.get(id=1))
        # fusion sur lui meme
        self.assertRaises(ValueError, models.Cat.objects.get(id=1).fusionne, models.Cat.objects.get(id=1))
        # fusion entre deux ib de type different
        self.assertRaises(TypeError, models.Ib.objects.get(id=3).fusionne, models.Ib.objects.get(id=1))
        # fusion avec un autre type
        self.assertRaises(TypeError, models.Ib.objects.get(id=1).fusionne, models.Banque.objects.get(id=1))
        # fusion sur lui meme
        self.assertRaises(ValueError, models.Ib.objects.get(id=1).fusionne, models.Ib.objects.get(id=1))
        # fusion avec un autre type
        self.assertRaises(TypeError, models.Exercice.objects.get(id=1).fusionne, models.Banque.objects.get(id=1))
        # fusion sur lui meme
        self.assertRaises(ValueError, models.Exercice.objects.get(id=1).fusionne, models.Exercice.objects.get(id=1))
        # fusion avec un autre type
        self.assertRaises(TypeError, models.Compte.objects.get(id=1).fusionne, models.Banque.objects.get(id=1))
        # fusion sur lui meme
        self.assertRaises(ValueError, models.Compte.objects.get(id=1).fusionne, models.Compte.objects.get(id=1))
        # fusion entre deux compte de type difference
        self.assertRaises(models.Gsb_exc, models.Compte.objects.get(id=1).fusionne, models.Compte.objects.get(id=2))
        # fusion avec un autre type
        self.assertRaises(TypeError, models.Compte.objects.get(id=4).fusionne, models.Banque.objects.get(id=1))
        # fusion sur lui meme
        self.assertRaises(ValueError, models.Compte.objects.get(id=4).fusionne, models.Compte.objects.get(id=4))
        # fusion avec un autre type
        self.assertRaises(TypeError, models.Moyen.objects.get(id=1).fusionne, models.Banque.objects.get(id=1))
        # fusion avec un autre type
        self.assertRaises(ValueError, models.Moyen.objects.get(id=1).fusionne, models.Moyen.objects.get(id=2))
        # probleme si fusion d'un moyen defini par defaut dans settings
        self.assertRaises(ValueError, models.Moyen.objects.get(id=1).fusionne, models.Moyen.objects.get(id=2))
        self.assertRaises(ValueError, models.Moyen.objects.get(id=4).fusionne, models.Moyen.objects.get(id=5))
        # fusion sur lui meme
        self.assertRaises(ValueError, models.Moyen.objects.get(id=4).fusionne, models.Moyen.objects.get(id=4))
        # fusion avec un autre type
        self.assertRaises(TypeError, models.Rapp.objects.get(id=1).fusionne, models.Banque.objects.get(id=1))
        # fusion avec lui meme
        self.assertRaises(ValueError, models.Rapp.objects.get(id=1).fusionne, models.Rapp.objects.get(id=1))

    def test_tiers_fusionne(self):
        """fusion entre 2 tiers"""
        models.Tiers.objects.get(nom="tiers1").fusionne(models.Tiers.objects.get(nom="tiers2"))
        # un tiers de moins
        self.assertQuerysetEqual(models.Tiers.objects.all().order_by('id'), [2, 3, 4, 5, 6, 7, 8, 256], attrgetter("id"))
        # verifie sur les dependance que c'est bien le nouveau tiers
        t = models.Tiers.objects.get(nom="tiers2")
        # id des operations
        self.assertQuerysetEqual(models.Ope.objects.filter(tiers=t).order_by('id'), [4, 5, 6, 7, 11, 12, 13], attrgetter("id"))
        # id des echeances
        self.assertQuerysetEqual(models.Echeance.objects.filter(tiers=t).order_by('id'), [1, 2, 3, 4, 5, 6, 7, 8], attrgetter("id"))

    def test_tiers_titre_save2(self):
        """on verifie que si on change le nom du titre, ca change le nom du tiers"""
        t = models.Titre.objects.get(nom='t1')
        t.nom = 'test'
        id_tiers = t.tiers.id
        t.save()
        self.assertEqual(models.Tiers.objects.get(id=id_tiers).nom, 'titre_ test')

    def test_titre_chgt_isin(self):
        """si on change isin , ca change chez le tiers"""
        t = models.Titre.objects.get(nom='t1')
        t.isin = "1234567"
        id_tiers = t.tiers.id
        t.save()
        self.assertEqual(models.Tiers.objects.get(id=id_tiers).notes, '1234567@ACT')

    def test_titre_last_cours1(self):
        """recupere le derniere cours d'un tiers 3 test:
        dernier cours
        dernier cours a une date et cours exist pas
        dernier cours a un dat et cours existe"""
        t = models.Titre.objects.get(nom="t2")
        self.assertEquals(t.last_cours(), 10)
        self.assertEquals(t.last_cours("2001-01-01"), 0)  # pas de cours possible
        self.assertEquals(t.last_cours("2011-11-01"), 5)

    def test_titre_last_date(self):
        """tests:
        date du dernier cours
        date du dernier cours rapprochee
        date du dernier cours rapp mais qui n'existe pas
        date du dernier cours alors que aucun n'est rapp"""
        t2 = models.Titre.objects.get(nom="t2")
        self.assertEqual(t2.last_cours_date(), datetime.date(2011, 11, 30))
        rep = t2.last_cours_date(rapp=True)
        self.assertEqual(rep, datetime.date(2011, 10, 29))
        t = models.Titre.objects.get(nom="t1")
        self.assertEqual(t.last_cours_date(rapp=True), None)
        self.assertEqual(t.last_cours_date(), datetime.date(2011, 12, 18))

    def test_titre_creation(self):
        """creation titre"""
        # on cree le titre
        t = models.Titre.objects.create(nom='ceci_est_un_titre', isin="123456789", type='ACT')
        # un titre de plus
        tiers = t.tiers
        self.assertEqual(models.Tiers.objects.count(), 10)
        self.assertEqual(tiers.nom, 'titre_ ceci_est_un_titre')
        self.assertEqual(tiers.notes, "123456789@ACT")
        self.assertEqual(tiers.is_titre, True)

    def test_titre_fusionne(self):
        """fusion de deux titres"""
        models.Titre.objects.get(nom="autre").fusionne(models.Titre.objects.get(nom="autre 2"))
        t = models.Titre.objects.get(nom="autre 2")
        # on regarde ce qui existe comme id de titre
        self.assertQuerysetEqual(models.Titre.objects.all().order_by('id'), [2, 3, 4, 5], attrgetter("id"))
        # verifie que la fusion des tiers sous jacent
        self.assertQuerysetEqual(models.Tiers.objects.all().order_by('id'), [1, 2, 4, 5, 6, 7, 8, 256], attrgetter("id"))
        # ce tiers n'existe plus
        self.assertRaises(models.Tiers.DoesNotExist, lambda: models.Tiers.objects.get(nom='Titre_ autre'))
        # ok pour les ope (et les tiers sous jacent)
        self.assertQuerysetEqual(models.Ope.objects.filter(tiers__nom='titre_ autre 2').order_by('id'), [10], attrgetter("id"))
        # ok pour les ope titre
        self.assertQuerysetEqual(models.Ope_titre.objects.filter(titre__nom='autre 2').order_by('id'), [4], attrgetter("id"))
        self.assertQuerysetEqual(t.ope_titre_set.all(), [4], attrgetter("id"))
        # verifier que les cours ont été fusionneés
        self.assertEquals(t.cours_set.count(), 2)

    def test_titre_fusionne_error(self):
        """fusionnne deux titre avec des cours differents"""
        models.Cours.objects.create(titre=models.Titre.objects.get(nom="autre"), valeur=20, date=utils.strpdate('2011-01-01'))
        models.Cours.objects.create(titre=models.Titre.objects.get(nom="autre 2"), valeur=40, date=utils.strpdate('2011-01-01'))
        self.assertRaises(models.Gsb_exc, models.Titre.objects.get(nom="autre").fusionne, models.Titre.objects.get(nom="autre 2"))

    def test_titre_investi(self):
        """test titre investi (version initial puis apres achat 20 t2 @ 20 """
        c1 = models.Compte.objects.get(id=4)
        c2 = models.Compte.objects.get(id=5)
        t = models.Titre.objects.get(nom="t2")
        self.assertEquals(t.investi(), 1600)
        self.assertEquals(t.investi(rapp=True), 100)
        self.assertEquals(t.investi(compte=c1), 0)
        self.assertEquals(t.investi(compte=c2), 1600)
        self.assertEquals(t.investi(compte=c2, rapp=True), 100)
        # on achete 20 t @ 1
        c1.achat(titre=t, nombre=20, date='2011-01-01')
        self.assertEquals(t.investi(), 1620)
        self.assertEquals(t.investi(c1), 20)
        self.assertEquals(t.investi(datel='2011-07-01'), 20)
        self.assertEquals(t.investi(compte=c1, datel='2010-12-31'), 0)
        self.assertEquals(t.investi(compte=c2, datel='2011-07-31'), 0)
        self.assertEquals(t.investi(compte=c2, exclude=models.Ope_titre.objects.get(id=3)), 1500)

    def test_titre_nb(self):
        """test nb titre"""
        c1 = models.Compte.objects.get(id=4)
        c2 = models.Compte.objects.get(id=5)
        t = models.Titre.objects.get(nom="t2")
        self.assertEquals(t.nb(), 170)
        self.assertEquals(t.nb(c1), 0)
        self.assertEquals(t.nb(datel='2011-07-01'), 0)
        self.assertEquals(t.nb(datel='2011-11-01'), 20)
        self.assertEquals(t.nb(compte=c2, datel='2011-07-01'), 0)
        self.assertEquals(t.nb(compte=c2), 170)
        self.assertEquals(t.nb(rapp=True), 20)
        self.assertEquals(t.nb(rapp=True, datel='2010-01-01'), 0)
        self.assertEquals(t.nb(rapp=True, datel='2011-11-01'), 20)
        self.assertEquals(t.nb(compte=c2, exclude_id=2), 20)
        self.assertEquals(t.nb(rapp=True, compte=c2), 20)

    @mock.patch('gsb.utils.today')
    def test_titre_encours(self, today_mock):
        """test titres encours"""
        today_mock.return_value = datetime.date(2011, 12, 31)
        c1 = models.Compte.objects.get(id=4)
        c2 = models.Compte.objects.get(id=5)
        t2 = models.Titre.objects.get(nom="t2")
        self.assertEquals(t2.encours(datel='1900-01-01'), 0)
        self.assertEquals(t2.encours(), 1700)
        self.assertEquals(t2.encours(rapp=True, compte=c2), 100)
        self.assertEquals(t2.encours(compte=c1), 0)
        self.assertEquals(t2.encours(compte=c2), 1700)
        c1.achat(titre=t2, nombre=20, date='2011-01-01', prix=20)
        self.assertEquals(t2.encours(rapp=True), 100)
        self.assertEquals(t2.encours(), 1900)
        self.assertEquals(t2.encours(c1), 200)
        self.assertEquals(t2.encours(datel='2011-05-01'), 400)
        self.assertEquals(t2.encours(compte=c1, datel='2010-07-01'), 0)
        self.assertEquals(t2.encours(compte=c2, datel='2011-11-01'), 100)
        self.assertEquals(t2.encours(rapp=True, datel='2011-01-01'), 0)

    # pas de test specifique pour cours

    def test_banque_fusionne(self):
        new_b = models.Banque.objects.get(cib="10001")
        models.Banque.objects.get(cib="99999").fusionne(new_b)
        self.assertQuerysetEqual(models.Banque.objects.all().order_by('id'), [1], attrgetter("id"))
        self.assertQuerysetEqual(models.Compte.objects.filter(banque__cib='10001').order_by('id'), [1, 2, 3, 4, 5, 6], attrgetter("id"))

    def test_cat_fusionne(self):
        models.Cat.objects.get(nom="cat2").fusionne(models.Cat.objects.get(nom="cat1"))
        # on verfie qu'elle est effface
        self.assertQuerysetEqual(models.Cat.objects.all().order_by('id'), [1, 3, 4, 54, 64, 65, 66, 67, 68, 69, 70, 71, 72], attrgetter("id"))
        self.assertQuerysetEqual(models.Ope.objects.filter(cat__nom="cat1").order_by('id'), [4, 5, 6, 7, 12, 13], attrgetter("id"))
        self.assertQuerysetEqual(models.Echeance.objects.filter(cat__nom="cat1").order_by('id'), [1, 2, 5, 6, 7], attrgetter("id"))

    def test_ib_fusionne(self):
        models.Ib.objects.get(nom="ib2").fusionne(models.Ib.objects.get(nom="ib1"))
        self.assertQuerysetEqual(models.Ib.objects.all().order_by('id'), [1, 3], attrgetter("id"))
        self.assertQuerysetEqual(models.Ope.objects.filter(ib__nom="ib1").order_by('id'), [6, 7], attrgetter("id"))
        self.assertQuerysetEqual(models.Echeance.objects.filter(ib__nom="ib1").order_by('id'), [1, 2], attrgetter("id"))

    def test_exo_fusionne(self):
        exo = models.Exercice.objects.get(id=1)
        models.Exercice.objects.get(id=2).fusionne(exo)
        self.assertQuerysetEqual(models.Exercice.objects.order_by('id'), [1], attrgetter("id"))
        # on verifie qu'il prend la totalite de la durée des 2 exo
        exo = models.Exercice.objects.get(id=1)
        self.assertEquals(exo.date_debut, utils.strpdate('2010-1-1'))
        self.assertEquals(exo.date_fin, utils.strpdate('2011-12-31'))
        # verification des liens
        self.assertQuerysetEqual(models.Ope.objects.filter(exercice__id=1).order_by('id'), [4, 5], attrgetter("id"))
        self.assertQuerysetEqual(models.Echeance.objects.filter(exercice__id=1).order_by('id'), [1, 2], attrgetter("id"))

    def test_compte_solde_normal(self):
        # version de base
        self.assertEqual(models.Compte.objects.get(id=1).solde(), -70)
        # si pas d'operation en stock dans le compte
        self.assertEqual(models.Compte.objects.get(id=2).ope_set.count(), 0)
        self.assertEqual(models.Compte.objects.get(id=2).solde(), 0)
        # seulement les operations rapproches
        self.assertEqual(models.Compte.objects.get(id=1).solde(rapp=True), -90)
        # a une date anterieur
        self.assertEqual(models.Compte.objects.get(id=1).solde(datel=utils.strpdate('2009-01-01')), 0)
        self.assertEqual(models.Compte.objects.get(id=1).solde(datel=utils.strpdate('2011-10-01')), -70)

    def test_compte_solde_rappro(self):
        c = models.Compte.objects.get(id=1)
        self.assertEqual(c.solde_rappro(), -90)
        self.assertEqual(c.date_rappro(), utils.strpdate('2011-08-12'))
        self.assertEqual(models.Compte.objects.get(id=3).date_rappro(), None)

    def test_compte_solde_pointe_rapp(self):
        self.assertEqual(models.Compte.objects.get(id=1).solde_pointe_rapp(), -80)
        o = models.Ope.objects.get(id=6)
        o.pointe = True
        o.save()
        self.assertEqual(models.Compte.objects.get(id=1).solde_pointe_rapp(), -70)
        self.assertEqual(models.Compte.objects.get(id=1).solde(pointe_rapp=True), -70)
        self.assertEqual(models.Compte.objects.get(id=2).solde_pointe_rapp(), 0)

    def test_compte_absolute_url(self):
        c = models.Compte.objects.get(id=1)
        absolute = c.get_absolute_url()
        self.assertEqual(absolute, '/compte/1/')

    def test_compte_fusion(self):
        n = models.Compte.objects.get(id=3)
        o = models.Compte.objects.get(id=2)
        # fusion avec un compte ferme dans un sens
        self.assertRaises(models.Gsb_exc, lambda: o.fusionne(models.Compte.objects.get(id=6)))
        # fusion ferme et dans l'autre
        self.assertRaises(models.Gsb_exc, lambda: models.Compte.objects.get(id=6).fusionne(o))
        # fusion effective
        n.fusionne(o)
        # les ope relatives
        self.assertEqual(models.Compte.objects.filter(id=3).exists(), False)
        self.assertQuerysetEqual(models.Ope.objects.filter(compte__id=2).order_by('id'), [9, ], attrgetter("id"))
        self.assertQuerysetEqual(models.Echeance.objects.filter(compte__id=2).order_by('id'), [2, 8], attrgetter("id"))
        self.assertQuerysetEqual(models.Echeance.objects.filter(compte_virement__id=2).order_by('id'), [1], attrgetter("id"))
        # fusion de compte titre
        models.Compte.objects.get(id=4).fusionne(models.Compte.objects.get(id=5))
        self.assertEquals(models.Ope.objects.get(id=1).compte_id, 5)
        self.assertEquals(models.Ope_titre.objects.get(id=1).compte_id, 5)

    def test_compte_achat_vente_error(self):
        c1 = models.Compte.objects.get(id=4)
        c2 = models.Compte.objects.get(id=5)
        # probleme si on utilise pas un titre dans le param titre
        self.assertRaises(TypeError, c1.achat, c2, 20, '2011-01-01')
        self.assertRaises(TypeError, c1.vente, c2, 20, '2011-01-01')
        self.assertRaises(TypeError, c1.revenu, c2, 20, '2011-01-01')

    def test_solde_titre_nul(self):
        c = models.Compte.objects.get(id=4)
        self.assertEquals(c.solde_titre(), 6)
        self.assertEquals(c.solde_titre(datel='2001-01-01'), 0)
        self.assertEquals(c.solde_titre(datel=datetime.date(2001, 1, 1)), 0)

    def test_compte_solde(self):
        c = models.Compte.objects.get(id=4)
        c2 = models.Compte.objects.get(id=5)
        t = models.Titre.objects.get(nom="t1")
        self.assertEqual(c.solde(), 0)
        # variation des cours (et donc du solde)
        t.cours_set.create(date='2012-07-18', valeur=2)
        self.assertEqual(c.solde(), 1)
        # solde a une date anterieur
        teston = c.solde(datel=utils.strpdate('2010-01-01'))
        self.assertEqual(teston, 0)
        teston = c2.solde(rapp=True)
        self.assertEqual(teston, 0)
        self.assertEqual(c.solde_titre(rapp=True), 0)

    def test_compte_achat_return_ope_titre(self):
        c = models.Compte.objects.get(id=4)
        t = models.Titre.objects.get(nom="t1")
        o = c.achat(titre=t, nombre=20, date='2011-01-01')
        self.assertEqual(o.id, 5)

    def test_compte_achat_sans_virement(self):
        c = models.Compte.objects.get(id=4)
        t = models.Titre.objects.get(nom="t1")
        c.achat(titre=t, nombre=20, date='2011-01-01')
        self.assertEqual(t.investi(c), 21)
        tall = c.titre.all().distinct()
        self.assertEqual(tall.count(), 2)
        self.assertEqual(tall[0].last_cours(), 1)
        self.assertEqual(c.solde(), 0)
        c.achat(titre=t, nombre=20, prix=2, date='2011-01-01')
        self.assertEqual(c.solde(), -20)

    def test_compte_achat_avec_frais(self):
        c = models.Compte.objects.get(id=4)
        t = models.Titre.objects.get(nom="t1")
        # utilisation des cat et tiers par defaut
        self.assertEqual(c.solde(), 0)
        self.assertEqual(t.investi(c), 1)
        c.achat(titre=t, nombre=20, frais=20, date='2011-07-01')
        self.assertEqual(c.solde(), -20)
        self.assertEqual(t.investi(c), 41)
        o = models.Ope.objects.filter(compte=c, date='2011-07-01', notes__icontains='frais')[0]
        self.assertEqual(o.cat_id, 69)
        self.assertEqual(o.montant, -20)
        self.assertEquals(o.notes, u"Frais 20@1")
        self.assertEquals(o.moyen_id, 2)
        # utilisa des cat et tiers donnes
        c.achat(titre=t, nombre=20, frais=20,
                cat_frais=models.Cat.objects.get(id=3),
                tiers_frais=models.Tiers.objects.get(id=2),
                date='2011-07-02')
        self.assertEqual(c.solde(), -40)
        self.assertEqual(t.investi(c), 61)
        o = models.Ope.objects.filter(compte=c, date='2011-07-02', notes__icontains='frais')[0]
        self.assertEqual(o.tiers_id, 2)
        self.assertEqual(o.cat_id, 3)
        self.assertEqual(o.montant, -20)
        self.assertEquals(o.notes, u"Frais 20@1")
        self.assertEquals(o.moyen_id, 2)

    def test_compte_achat_avec_virement(self):
        c = models.Compte.objects.get(id=5)
        t = models.Titre.objects.get(nom="t1")
        c.achat(titre=t, nombre=20, date='2011-01-01', virement_de=models.Compte.objects.get(id=1))
        self.assertEqual(t.investi(c), 20)
        self.assertEqual(c.solde(), 120)
        self.assertEquals(models.Ope.objects.filter(compte__id=c.id).count(), 4)
        self.assertEqual(models.Compte.objects.get(id=1).solde(), -90)

    def test_operation_titre_avec_moyen_defaut(self):
        c = models.Compte.objects.create(nom="cpt6", type='t')
        t = models.Titre.objects.get(nom="t1")
        c.achat(titre=t, nombre=20, date='2011-01-01')
        self.assertEqual(t.investi(c), 20)
        self.assertEqual(c.solde(), 0)
        o = models.Ope.objects.filter(compte__id=c.id)[0]
        self.assertEqual(o.id, 14)
        self.assertEqual(o.moyen.nom, 'moyen_dep1')
        c.vente(titre=t, nombre=20, date='2011-01-02')
        self.assertEqual(t.investi(c), 0)
        self.assertEqual(c.solde(), 0)
        o = models.Ope.objects.filter(compte__id=c.id)[1]
        self.assertEqual(o.id, 15)
        self.assertEqual(o.moyen.nom, 'moyen_rec1')

    def test_compte_vente_simple(self):
        c = models.Compte.objects.get(id=4)
        self.assertEqual(c.nom, u'cpt_titre1')
        t = models.Titre.objects.get(nom='t1')
        self.assertEqual(t.investi(c), 1)
        self.assertRaises(models.Titre.DoesNotExist, lambda: c.vente(titre=t, nombre=20, date='2011-01-01'))  # trop tot
        self.assertRaises(models.Titre.DoesNotExist,
                          lambda: c.vente(titre=t, nombre=40, date='2011-11-02'))  # montant trop eleve car entre les deux operations
        self.assertRaises(models.Titre.DoesNotExist,
                          lambda: c.vente(titre=t, nombre=2000, date='2011-12-31'))  # montant trop eleve car entre les deux operations
        c.vente(titre=t, nombre=1, date='2011-12-25')
        a_test = t.investi(c)
        self.assertEqual(a_test, decimal.Decimal('0'))
        tall = c.liste_titre()
        self.assertEqual(len(tall), 2)
        self.assertRaises(models.Titre.DoesNotExist, lambda: c.vente(titre=t, nombre=20, date='2011-12-26'))  # a pu de titre
        self.assertEqual(c.solde(), 0)

    def test_compte_vente_avec_frais(self):
        """vente avec frais"""
        # on cree le compte
        c = models.Compte.objects.create(type="t", nom="c_test", moyen_credit_defaut=models.Moyen.objects.get(id=4),
                                  moyen_debit_defaut=models.Moyen.objects.get(id=2))
        # on cree le titre
        t = models.Titre.objects.create(nom="t3", isin="xxxxxxx")
        # utilisation des cat et tiers par defaut
        models.Ope_titre.objects.create(titre=t, compte=c, nombre=15, date=utils.strpdate('2011-01-01'), cours=10)
        c.vente(titre=t, nombre=5, frais=20, date='2011-11-01', prix=5)
        self.assertEqual(c.solde() - c.solde_titre(), -145)
        self.assertEqual(c.solde_titre(), 50)
        self.assertEqual(c.solde(), -95)
        self.assertEqual(t.investi(c), 120)  # attention, on prend le cmup avec les frais
        o = models.Ope.objects.filter(compte=c, date='2011-11-01', notes__icontains='frais')[0]
        self.assertEqual(o.cat_id, 69)
        self.assertEqual(o.montant, -20)
        self.assertEquals(o.notes, u"frais -5@5")
        self.assertEquals(o.moyen_id, 2)
        # "utilisa des cat et tiers donnes
        c.vente(titre=t, nombre=5, frais=20,
                cat_frais=models.Cat.objects.get(id=3),
                tiers_frais=models.Tiers.objects.get(id=2),
                date='2011-11-02', prix=10)
        self.assertEqual(c.solde(), -65)
        self.assertEqual(t.investi(c), 60)
        o = models.Ope.objects.filter(compte=c, date='2011-11-02', notes__icontains='frais')[0]
        self.assertEqual(o.tiers_id, 2)
        self.assertEqual(o.cat_id, 3)
        self.assertEqual(o.montant, -20)
        self.assertEquals(o.notes, u"frais -5@10")
        self.assertEquals(o.moyen_id, 2)

    def test_compte_vente_avec_virement(self):
    # on cree le compte
        c = models.Compte.objects.create(type="t", nom="c_test", moyen_credit_defaut=models.Moyen.objects.get(id=4),
                                  moyen_debit_defaut=models.Moyen.objects.get(id=2))
        # on cree le titre
        t = models.Titre.objects.create(nom="t_test", isin="xxxxxxx")
        c.achat(titre=t, prix=10, nombre=15, date='2011-11-01')
        c.vente(titre=t, prix=5, nombre=5, date='2011-11-02', virement_vers=models.Compte.objects.get(id=1))
        self.assertEqual(t.investi(c), decimal.Decimal('100'))
        self.assertEqual(t.nb(c), 10)
        self.assertEqual(c.solde(), -100)
        self.assertEquals(models.Ope.objects.filter(compte=c).count(), 4)
        self.assertEqual(models.Compte.objects.get(id=1).solde(), -70 + 25)  # montant de l'operation

    def test_compte_revenu_simple(self):
        c = models.Compte.objects.get(id=4)
        t = models.Titre.objects.get(nom="t1")
        self.assertRaises(models.Titre.DoesNotExist, lambda: c.revenu(titre=t, montant=20, date='2011-01-01'))  # trop tot
        c.revenu(titre=t, montant=20, date='2011-12-25')
        self.assertEqual(t.investi(c), -19)
        self.assertEqual(c.solde(), 20)
        c.vente(titre=t, nombre=1, date='2011-12-25')
        self.assertRaises(models.Titre.DoesNotExist, lambda: c.revenu(titre=t, montant=20, date='2012-01-01'))  # a pu

    def test_compte_revenu_frais(self):
        c = models.Compte.objects.get(id=4)
        t = models.Titre.objects.get(nom="t1")
        # on cree un revenu avec des frais
        c.revenu(titre=t, montant=20, date='2011-12-20', frais=10)
        self.assertEqual(t.investi(c), -9)
        self.assertEqual(c.solde(), 10)
        cat = models.Cat.objects.get(id=3)
        tiers = models.Tiers.objects.get(id=2)
        # second revenu avec des frais mais ratache a autre chose que le titre
        c.revenu(titre=t, montant=20, frais=20,
                 cat_frais=cat,
                 tiers_frais=tiers,
                 date='2011-12-21')
        self.assertEqual(t.investi(c), -29)
        self.assertEqual(c.solde(), 10)
        self.assertEquals(models.Ope.objects.filter(compte=c).count(), 6)

    def test_compte_revenu_virement(self):
        c = models.Compte.objects.get(id=4)
        t = models.Titre.objects.get(nom="t1")
        c.revenu(titre=t, montant=20, date='2011-12-25', virement_vers=models.Compte.objects.get(id=1))
        self.assertEqual(c.solde(), 0)
        self.assertEquals(models.Ope.objects.filter(compte=c).count(), 4)
        self.assertEqual(models.Compte.objects.get(id=1).solde(), -50)

    def test_compte_liste_titre(self):
        c = models.Compte.objects.get(id=4)
        self.assertQuerysetEqual(c.liste_titre(), [u'autre', u't1'], attrgetter("nom"))

    def test_compte_date_rappro(self):
        self.assertEqual(models.Compte.objects.get(id=5).date_rappro(), utils.strpdate('2011-10-30'))
        self.assertEqual(models.Compte.objects.get(id=4).date_rappro(), None)

    def test_compte_t_solde_rappro(self):
        c = models.Compte.objects.create(type="t", nom="c_test", moyen_credit_defaut=models.Moyen.objects.get(id=4),
                                  moyen_debit_defaut=models.Moyen.objects.get(id=2))
        self.assertEqual(c.solde_rappro(), 0)
        self.assertEqual(models.Compte.objects.get(id=4).solde_rappro(), 0)
        v = models.Virement.create(models.Compte.objects.get(id=1), models.Compte.objects.get(id=5), 20)
        v.dest.rapp = models.Rapp.objects.get(id=1)
        v.save()
        self.assertEqual(models.Compte.objects.get(id=5).solde_rappro(), 20)
    def test_compte_solde_espece(self):
        self.assertEqual(models.Compte.objects.get(id=1).solde_espece(), -70)
        self.assertEqual(models.Compte.objects.get(id=4).solde_espece(), -6)
    def test_compte_ajustement_normal(self):
        c=models.Compte.objects.get(id=1)
        c.ajustement(datel=datetime.date(2012, 11, 30),montant_vrai=0)
        self.assertEqual(models.Ope.objects.filter(compte_id=1).count(),9)
        self.assertEqual(models.Ope.objects.get(id=14).__unicode__(),u"(14) le 30/11/2012 : 70 EUR a ajustement cpt: cpte1")
        #on verifie que si on fait un ajustement et qu'il est deja fait, on fait rien
        c.ajustement(datel=datetime.date(2012, 12, 30),montant_vrai=0)
        self.assertEqual(models.Ope.objects.filter(compte_id=1).count(),9)


    def test_ope_titre_invest(self):
        """invest est le montant"""
        t = models.Titre.objects.create(nom="t3", isin="xxxxxxx")
        c = models.Compte.objects.create(type="t", nom="c_test", moyen_credit_defaut=models.Moyen.objects.get(id=4),
                                  moyen_debit_defaut=models.Moyen.objects.get(id=2))
        # creation d'une nouvelle operation
        o = models.Ope_titre.objects.create(titre=t, compte=c, nombre=15, date=utils.strpdate('2011-01-01'), cours=10)
        self.assertEqual(o.invest, 150)

    def test_ope_titre_save(self):
        """creation ope puis nouvel achat mais erreur1 et erreur2"""
        t = models.Titre.objects.create(nom="t3", isin="xxxxxxx")
        c = models.Compte.objects.create(type="t", nom="c_test", moyen_credit_defaut=models.Moyen.objects.get(id=4),
                                  moyen_debit_defaut=models.Moyen.objects.get(id=2))
        # creation d'une nouvelle operation
        models.Ope_titre.objects.create(titre=t, compte=c, nombre=15, date=utils.strpdate('2011-01-01'), cours=10)
        models.Ope_titre.objects.create(titre=t, compte=c, nombre=5, date=utils.strpdate('2011-01-02'), cours=20)
        o = models.Ope_titre.objects.get(id=5)
        o2 = models.Ope_titre.objects.get(id=6)
        self.assertEqual(o.ope_ost.montant, -150)
        self.assertEqual(o2.ope_ost.montant, -100)  # juste verification
        self.assertEqual(t.nb(c), 20)
        self.assertEqual(t.investi(c), 250)
        self.assertEqual(t.encours(c), 20 * 20)
        # en fait on s'est trompé, c'est une vente
        o2.nombre = -5
        o2.save()
        o2 = models.Ope_titre.objects.get(id=6)
        self.assertEqual(o2.ope_ost.id, 15)
        self.assertEqual(o2.ope_pmv.id, 16)
        self.assertEqual(t.nb(c), 10)
        self.assertEqual(t.investi(c), 100)
        self.assertEqual(t.encours(c), 10 * 20)
        o2 = models.Ope_titre.objects.get(id=6)
        o2.nombre = -10
        o2.save()
        self.assertEqual(o2.ope_ost.id, 15)
        self.assertEqual(o2.ope_pmv.id, 16)
        self.assertEqual(t.nb(c), 5)
        self.assertEqual(t.investi(c), 50)
        self.assertEqual(t.encours(c), 5 * 20)

        # finalement c'etait vraiment ca
        o2 = models.Ope_titre.objects.get(id=6)
        o2.nombre = 10
        o2.save()
        self.assertEqual(t.nb(c), 25)
        self.assertEqual(t.investi(c), 350)
        self.assertEqual(t.encours(c), 25 * 20)

    def test_ope_titre_moins_value(self):
        t = models.Titre.objects.create(nom="t3", isin="xxxxxxx")
        c = models.Compte.objects.create(type="t", nom="c_test", moyen_credit_defaut=models.Moyen.objects.get(id=4),
                                  moyen_debit_defaut=models.Moyen.objects.get(id=2))
        models.Ope_titre.objects.create(titre=t, compte=c, nombre=15, date=utils.strpdate('2011-01-01'), cours=10)
        models.Ope_titre.objects.create(titre=t, compte=c, nombre=-5, date='2011-01-02', cours=5)
        o = models.Ope.objects.filter(compte=c).filter(date='2011-01-02')[0]
        self.assertEqual(o.id, 15)
        self.assertEqual(o.montant, 50)  # desinvestissement
        o = models.Ope.objects.filter(compte=c).filter(date='2011-01-02')[1]
        self.assertEqual(o.id, 16)
        self.assertEqual(o.montant, -25)  # desinvest

    def test_ope_titre_save2(self):
        """ nouvelle ope, puis vente partielle, puis vente totale"""
        t = models.Titre.objects.create(nom="t3", isin="xxxxxxx")
        c = models.Compte.objects.create(type="t", nom="c_test", moyen_credit_defaut=models.Moyen.objects.get(id=4),
                                  moyen_debit_defaut=models.Moyen.objects.get(id=2))
        # creation d'une nouvelle operation
        o = models.Ope_titre.objects.create(titre=t, compte=c, nombre=15, date=utils.strpdate('2011-01-01'), cours=10)
        self.assertEqual(o.ope_ost.id, 14)
        self.assertEqual(o.ope_ost.montant, -150)
        self.assertEqual(o.ope_ost.moyen_id, 2)
        self.assertEqual(t.investi(c), 150)
        self.assertEqual(o.ope_ost.notes, "15@10")
        # on verifie qu'il creer bien un cours a la date
        self.assertEqual(models.Cours.objects.get(date=utils.strpdate('2011-01-01'), titre=t).valeur, 10)
        # on vend
        o = models.Ope_titre.objects.create(titre=t, compte=c, nombre=-10, date='2011-01-02', cours=15)
        self.assertEqual(o.ope_ost.id, 15)
        self.assertEqual(o.ope_ost.montant, 100)
        self.assertEqual(o.ope_ost.moyen_id, 4)
        self.assertEqual(o.ope_pmv.id, 16)
        self.assertEqual(o.ope_pmv.montant, 50)
        self.assertEqual(o.ope_pmv.moyen_id, 4)
        self.assertEqual(o.ope_pmv.cat.nom, 'Revenus de placement:Plus-values')
        self.assertEqual(o.ope_ost.notes, "-10@15")
        self.assertEqual(t.investi(c), 50)
        self.assertEqual(t.encours(c), 5 * 15)
        # on vend ce qui reste
        o = models.Ope_titre.objects.create(titre=t, compte=c, nombre=-5, date='2011-01-03', cours=20)
        self.assertEqual(t.investi(c), 0)
        self.assertEqual(o.ope_ost.montant, 50)
        self.assertEqual(o.ope_pmv.montant, 50)
        self.assertEqual(t.encours(c), 0)

    def test_ope_titre_delete(self):
        """creation puis effacement d'une operation_titre"""
        t = models.Titre.objects.create(nom="t3", isin="xxxxxxx")
        c = models.Compte.objects.create(type="t", nom="c_test", moyen_credit_defaut=models.Moyen.objects.get(id=4),
                                  moyen_debit_defaut=models.Moyen.objects.get(id=2))
        # on cree l'ope
        o = models.Ope_titre.objects.create(titre=t, compte=c, nombre=15, date=utils.strpdate('2011-01-01'), cours=10)
        o_id = o.id
        # on l'efface

        o.delete()
        #on verifie que l'ope titre a bien ete efface
        self.assertFalse(models.Ope_titre.objects.filter(id=o_id).exists())
        #on verifie que l'ope sous jacente a bien ete efface
        self.assertEqual(models.Ope.objects.count(),13)

    def test_ope_titre_delete2(self):
        """verification des test d'integrite, test ope si achat"""
        t = models.Titre.objects.create(nom="t3", isin="xxxxxxx")
        c = models.Compte.objects.create(type="t", nom="c_test", moyen_credit_defaut=models.Moyen.objects.get(id=4),
                                  moyen_debit_defaut=models.Moyen.objects.get(id=2))
        o = models.Ope_titre.objects.create(titre=t, compte=c, nombre=15, date=utils.strpdate('2011-01-01'), cours=10)
        o_id = o.id
        # on rapproche son ope
        o.ope_ost.rapp_id = 1
        o.ope_ost.save()
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                models.Ope_titre.objects.filter(id=o_id).delete()

    def test_ope_titre_delete3(self):
        """verification des test d'integrite, test ope si vente"""
        t = models.Titre.objects.create(nom="t3", isin="xxxxxxx")
        c = models.Compte.objects.create(type="t", nom="c_test", moyen_credit_defaut=models.Moyen.objects.get(id=4),
                                  moyen_debit_defaut=models.Moyen.objects.get(id=2))
        #comme on teste une vente, il faut d'abord acheter
        models.Ope_titre.objects.create(titre=t, compte=c, nombre=15, date=utils.strpdate('2011-01-01'), cours=10)
        # avec une vente comme ca il y a des plus values
        o = models.Ope_titre.objects.create(titre=t, compte=c, nombre=-5, date=utils.strpdate('2011-01-01'), cours=10)
        o_id = o.id
        # on rapproche son ope pmv
        o.ope_pmv.rapp = models.Rapp.objects.get(id=1)
        o.ope_pmv.save()
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                models.Ope_titre.objects.filter(id=o_id).delete()

    def test_ope_titre_get_absolute_url(self):
        self.assertEqual(models.Ope_titre.objects.get(id=1).get_absolute_url(), '/ope_titre/1/')

    def test_ope_titre_rapp(self):
        """verifie les deux cas ou une ope peut etre rapp"""
        t = models.Titre.objects.create(nom="t3", isin="xxxxxxx")
        c = models.Compte.objects.create(type="t", nom="c_test", moyen_credit_defaut=models.Moyen.objects.get(id=4),
                                  moyen_debit_defaut=models.Moyen.objects.get(id=2))
        o = models.Ope_titre.objects.create(titre=t, compte=c, nombre=15, date=utils.strpdate('2011-01-01'), cours=10)
        o_id = o.id
        # on rapproche son ope
        o.ope_ost.rapp_id = 1
        o.ope_ost.save()
        self.assertEqual(models.Ope_titre.objects.get(id=o_id).rapp, True)
        o.ope_ost.rapp = None
        o.ope_ost.save()
        self.assertEqual(models.Ope_titre.objects.get(id=o_id).rapp, False)
        o = models.Ope_titre.objects.create(titre=t, compte=c, nombre=-5, date=utils.strpdate('2011-01-01'), cours=100)
        o_id = o.id
        o.ope_pmv.rapp_id = 1
        o.ope_pmv.save()
        self.assertEqual(models.Ope_titre.objects.get(id=o_id).rapp, True)

    def test_moyen_fusionne(self):
        models.Moyen.objects.get(id=3).fusionne(models.Moyen.objects.get(id=2))
        self.assertQuerysetEqual(models.Moyen.objects.order_by('id'), [1, 2, 4, 5, 6, 7], attrgetter("id"))
        self.assertQuerysetEqual(models.Compte.objects.filter(moyen_credit_defaut__id=2).order_by('id'), [], attrgetter("id"))
        self.assertQuerysetEqual(models.Compte.objects.filter(moyen_debit_defaut__id=2).order_by('id'), [4, 5], attrgetter("id"))
        self.assertQuerysetEqual(models.Echeance.objects.filter(moyen__id=2).order_by('id'), [3, 4, 8], attrgetter("id"))
        self.assertQuerysetEqual(models.Echeance.objects.filter(moyen_virement__id=2).order_by('id'), [1, ], attrgetter("id"))
        self.assertQuerysetEqual(models.Ope.objects.filter(moyen__id=2).order_by('id'), [1, 2, 3, 10], attrgetter("id"))

    def test_moyen_defaut(self):
        m = models.Moyen.objects.get(id=1)
        self.assertRaises(IntegrityError, m.delete)

    def test_moyen_defaut2(self):
        m = models.Moyen.objects.get(id=4)
        self.assertRaises(IntegrityError, m.delete)

    def test_rapp_compte(self):
        self.assertEquals(models.Rapp.objects.get(id=1).compte, 1)
        self.assertEquals(models.Rapp.objects.get(id=3).compte, None)

    def test_rapp_solde(self):
        self.assertEquals(models.Rapp.objects.get(id=1).solde, -90)
        self.assertEquals(models.Rapp.objects.get(id=3).solde, 0)

    def test_rapp_fusionne(self):
        models.Rapp.objects.get(id=1).fusionne(models.Rapp.objects.get(id=3))
        self.assertQuerysetEqual(models.Ope.objects.filter(rapp__id=3).order_by('id'), [4, 5], attrgetter("id"))

    def test_echeance_save(self):
        """on ne peut sauver une echeance avec un virement sur un meme compte"""
        self.assertRaises(ValidationError, lambda: models.Echeance.objects.create(date=utils.strpdate('2011-01-01'),
                                                                           compte=models.Compte.objects.get(id=1),
                                                                           montant=2,
                                                                           tiers=models.Tiers.objects.get(id=2),
                                                                           compte_virement=models.Compte.objects.get(id=1)))

    def test_echeance_calcul_next(self):
        self.assertEquals(models.Echeance.objects.get(id=1).calcul_next(), None)
        self.assertEquals(models.Echeance.objects.get(id=2).calcul_next(), utils.strpdate('2011-12-02'))
        self.assertEquals(models.Echeance.objects.get(id=3).calcul_next(), utils.strpdate('2011-11-01'))
        self.assertEquals(models.Echeance.objects.get(id=4).calcul_next(), utils.strpdate('2011-11-13'))
        self.assertEquals(models.Echeance.objects.get(id=5).calcul_next(), utils.strpdate('2011-12-30'))
        self.assertEquals(models.Echeance.objects.get(id=6).calcul_next(), utils.strpdate('2013-10-30'))
        self.assertEquals(models.Echeance.objects.get(id=7).calcul_next(), None)

    def test_echeance_check1(self):
        """enregistre toutes les echaances jusqu'au 31/12/2011"""
        request = self.request_get('/options/check')
        models.Echeance.check(to=utils.strpdate('2011-12-31'), request=request)
        self.assertcountmessage(request, 57)
        self.assertEqual(models.Ope.objects.count(), 71)

    def test_echeance_check2(self):
        """enregistre les echeance du compte 2 jusqu'au 09/12/2011"""
        request = self.request_get('/options/check')
        models.Echeance.check(queryset=models.Echeance.objects.filter(id=2), to=utils.strpdate('2011-12-09'), request=request)
        self.assertEqual(models.Ope.objects.count(), 18)

    @mock.patch('gsb.utils.today')
    def test_echeance_check3(self, today_mock):
        """enregistre les operation jusqu'a aujourdhui 'en fait le 31/12/2011'"""
        today_mock.return_value = datetime.date(2011, 12, 31)
        request = self.request_get('/options/check')
        models.Echeance.check(request=request)
        self.assertcountmessage(request, 57)
        self.assertEqual(models.Ope.objects.count(), 71)

    def test_ope_absolute_url(self):
        self.assertEqual(models.Ope.objects.get(id=1).get_absolute_url(), '/ope/1/')

    def test_ope_non_mere(self):
        self.assertQuerysetEqual(models.Ope.non_meres().order_by('id'), [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 13], attrgetter("id"))

    def test_ope_is_mere(self):
        self.assertEqual(models.Ope.objects.get(id=11).is_mere, True)

    def test_ope_is_fille(self):
        self.assertEqual(models.Ope.objects.get(id=12).is_fille, True)

    def test_ope_pr(self):
        c = models.Compte.objects.get(id=1)
        t = models.Tiers.objects.get(id=1)
        # test pas defaut
        o = models.Ope.objects.create(compte=c, date='2010-01-01', montant=20, tiers=t)
        ide = o.id
        self.assertEquals(o.pr, False)
        o.pointe = True
        o.save()
        self.assertEquals(models.Ope.objects.get(id=ide).pr, True)
        o = models.Ope.objects.get(id=ide)
        o.rapp_id = 1
        o.pointe = False
        o.save()
        self.assertEquals(models.Ope.objects.get(id=ide).pr, True)

    def test_ope_save(self):
        c = models.Compte.objects.get(id=1)
        t = models.Tiers.objects.get(id=1)
        # test avecmoyen par defaut credit
        o = models.Ope.objects.create(compte=c, date='2010-01-01', montant=20, tiers=t)
        self.assertEquals(o.moyen_id, 4)
        # test avecmoyen par defaut debit
        o = models.Ope.objects.create(compte=c, date='2010-01-01', montant=-20, tiers=t)
        self.assertEquals(o.moyen_id, 1)
        # test avec moyen defini
        o = models.Ope.objects.create(compte=c, date='2010-01-01', montant=-20, tiers=t, moyen=models.Moyen.objects.get(id=2))
        self.assertEquals(o.moyen_id, 2)
        # test avec les moyens par defaut
        c.moyen_credit_defaut = None
        o = models.Ope.objects.create(compte=c, date='2010-01-01', montant=20, tiers=t)
        self.assertEquals(o.moyen_id, 4)
        c.moyen_debit_defaut = None
        o = models.Ope.objects.create(compte=c, date='2010-01-01', montant=-20, tiers=t)
        self.assertEquals(o.moyen_id, 1)

    def test_uuid_ope(self):
        """on verifie que l'uuid ne change pas si on sauve"""
        o = models.Ope.objects.get(pk=4)
        o.montant = 245
        uuid = o.uuid
        o.save()
        o = models.Ope.objects.get(pk=4)
        self.assertEqual(o.uuid, uuid)

    def test_uuid_cree(self):
        """on verifie que c'est un uuid qui est bien renseigne et qu'il ne change pas si il est sauve"""
        o = models.Ope.objects.create(tiers_id=1, compte_id=1, cat_id=1, moyen_id=1, date=utils.now())
        uuid = o.uuid
        o.save()
        o = models.Ope.objects.get(pk=o.id)
        self.assertEqual(o.uuid, uuid)

    def test_last_modif(self):
        o = models.Ope.objects.get(pk=4)
        lup = o.lastupdate
        o.save()
        o = models.Ope.objects.get(pk=4)
        self.assertLess(lup, o.lastupdate)

    def test_last_modif2(self):
        """on verifie que last update est toujours modifie"""
        o = models.Tiers.objects.create(nom="Test")
        lup = o.lastupdate
        pk = o.id
        time.sleep(10)
        o.nom = "Test2"
        o.save()
        o = models.Tiers.objects.get(pk=pk)
        self.assertLess(lup, o.lastupdate)

    def test_ope_clean(self):
        o = models.Ope.objects.get(pk=4)
        t = models.Tiers.objects.get(id=1)
        c = models.Cat.objects.get(id=1)
        m = models.Moyen.objects.get(id=1)
        cpt = models.Compte.objects.get(id=1)
        r = models.Rapp.objects.get(id=1)
        ensemble_a_tester = (
        ({'tiers': t.id, 'compte': cpt.id, 'cat': c.id, 'montant': 120, 'moyen': m.id, 'date': utils.now()}, {}, o), # normal
        ({'tiers': t.id, 'compte': cpt.id, 'cat': c.id, 'montant': 120, 'moyen': m.id, 'pointe': True, 'rapp': r.id, 'date': utils.now()},
         {'__all__': [u"cette opération ne peut pas etre à la fois pointée et rapprochée", ]},
         o),
        ({'tiers': t.id, 'compte': cpt.id, 'cat': c.id, 'montant': 120, 'moyen': m.id, 'date': utils.now()}, {}, models.Ope.objects.get(pk=11)))
        for ens in ensemble_a_tester:
            form = forms.OperationForm(ens[0], instance=ens[2])
            form.is_valid()
            self.assertEqual(form.errors, ens[1], "probleme avec le form: data %s, resultat attendu %s" % (ens[0], ens[1]))

    def test_ope_clean_pointee(self):
        """une fille pointee a le montant de la mere changee"""
        t = models.Tiers.objects.get(id=1)
        c = models.Cat.objects.get(id=1)
        m = models.Moyen.objects.get(id=1)
        cpt = models.Compte.objects.get(id=1)
        o = models.Ope.objects.get(pk=12)
        o.pointe = True
        o.save()
        data = {'tiers': t.id, 'compte': cpt.id, 'cat': c.id, 'montant': 120, 'moyen': m.id, 'date': utils.now()}
        form = forms.OperationForm(data, instance=models.Ope.objects.get(pk=11))
        form.is_valid()
        self.assertEqual(form.errors, {'__all__': [u"impossible de modifier l'opération car au moins une partie est pointée", ]})

    def test_ope_clean_pointee2(self):
        """une fille pointee a le montant d'une autre fille changee"""
        t = models.Tiers.objects.get(id=1)
        c = models.Cat.objects.get(id=1)
        m = models.Moyen.objects.get(id=1)
        cpt = models.Compte.objects.get(id=1)
        o = models.Ope.objects.get(pk=12)
        o.pointe = True
        o.save()
        data = {'tiers': t.id, 'compte': cpt.id, 'cat': c.id, 'montant': 120, 'moyen': m.id, 'date': utils.now()}
        form = forms.OperationForm(data, instance=models.Ope.objects.get(pk=13))
        form.is_valid()
        self.assertEqual(form.errors, {'__all__': [u"impossible de modifier l'opération car au moins une partie est pointée", ]})

    def test_ope_clean_pointee3(self):
        """une mere pointee a le montant d'une fille changee"""
        t = models.Tiers.objects.get(id=1)
        c = models.Cat.objects.get(id=1)
        m = models.Moyen.objects.get(id=1)
        cpt = models.Compte.objects.get(id=1)
        o = models.Ope.objects.get(pk=11)
        o.pointe = True
        o.save()
        data = {'tiers': t.id, 'compte': cpt.id, 'cat': c.id, 'montant': 120, 'moyen': m.id, 'date': utils.now()}
        form = forms.OperationForm(data, instance=models.Ope.objects.get(pk=13))
        form.is_valid()
        self.assertEqual(form.errors, {'__all__': [u"impossible de modifier l'opération car au moins une partie est pointée", ]})

    def test_ope_clean_pointee4(self):
        """une mere pointee a son montant  changee"""
        t = models.Tiers.objects.get(id=1)
        c = models.Cat.objects.get(id=1)
        m = models.Moyen.objects.get(id=1)
        cpt = models.Compte.objects.get(id=1)
        o = models.Ope.objects.get(pk=11)
        o.pointe = True
        o.save()
        data = {'tiers': t.id, 'compte': cpt.id, 'cat': c.id, 'montant': 120, 'moyen': m.id, 'date': utils.now(), 'pointe': True}
        form = forms.OperationForm(data, instance=models.Ope.objects.get(pk=11))
        form.is_valid()
        self.assertEqual(form.errors, {'__all__': [u"impossible de modifier l'opération car au moins une partie est pointée", ]})

    def test_ope_clean_pointee5(self):
        """une fille pointee a son montant  changee"""
        t = models.Tiers.objects.get(id=1)
        c = models.Cat.objects.get(id=1)
        m = models.Moyen.objects.get(id=1)
        cpt = models.Compte.objects.get(id=1)
        o = models.Ope.objects.get(pk=13)
        o.pointe = True
        o.save()
        data = {'tiers': t.id, 'compte': cpt.id, 'cat': c.id, 'montant': 120, 'moyen': m.id, 'date': utils.now(), 'pointe': True}
        form = forms.OperationForm(data, instance=models.Ope.objects.get(pk=13))
        form.is_valid()
        self.assertEqual(form.errors, {'__all__': [u"impossible de modifier l'opération car au moins une partie est pointée", ]})

    def test_ope_cleanrapp(self):
        """une fille rapp, mere changee"""
        t = models.Tiers.objects.get(id=1)
        c = models.Cat.objects.get(id=1)
        m = models.Moyen.objects.get(id=1)
        cpt = models.Compte.objects.get(id=1)
        r = models.Rapp.objects.get(id=1)
        o = models.Ope.objects.get(pk=12)
        o.rapp = r
        o.save()
        data = {'tiers': t.id, 'compte': cpt.id, 'cat': c.id, 'montant': 120, 'moyen': m.id, 'date': utils.now()}
        form = forms.OperationForm(data, instance=models.Ope.objects.get(pk=11))
        form.is_valid()
        self.assertEqual(form.errors, {'__all__': [u"impossible de modifier l'opération car au moins une partie est rapprochée", ]})

    def test_ope_cleanrapp2(self):
        """une fille rapp, une autre fille changee"""
        t = models.Tiers.objects.get(id=1)
        c = models.Cat.objects.get(id=1)
        m = models.Moyen.objects.get(id=1)
        cpt = models.Compte.objects.get(id=1)
        r = models.Rapp.objects.get(id=1)
        o = models.Ope.objects.get(pk=12)
        o.rapp = r
        o.save()
        data = {'tiers': t.id, 'compte': cpt.id, 'cat': c.id, 'montant': 120, 'moyen': m.id, 'date': utils.now()}
        form = forms.OperationForm(data, instance=models.Ope.objects.get(pk=13))
        form.is_valid()
        self.assertEqual(form.errors, {'__all__': [u"impossible de modifier l'opération car au moins une partie est rapprochée", ]})

    def test_ope_clean_rapp3(self):
        """une mere rapp a le montant d'une fille changee"""
        t = models.Tiers.objects.get(id=1)
        c = models.Cat.objects.get(id=1)
        m = models.Moyen.objects.get(id=1)
        cpt = models.Compte.objects.get(id=1)
        o = models.Ope.objects.get(pk=11)
        r = models.Rapp.objects.get(id=1)
        o.rapp = r
        o.save()
        data = {'tiers': t.id, 'compte': cpt.id, 'cat': c.id, 'montant': 120, 'moyen': m.id, 'date': utils.now()}
        form = forms.OperationForm(data, instance=models.Ope.objects.get(pk=13))
        form.is_valid()
        self.assertEqual(form.errors, {'__all__': [u"impossible de modifier l'opération car au moins une partie est rapprochée", ]})

    def test_ope_clean_rapp4(self):
        """une mere rapp a son montant  changee"""
        t = models.Tiers.objects.get(id=1)
        c = models.Cat.objects.get(id=1)
        m = models.Moyen.objects.get(id=1)
        cpt = models.Compte.objects.get(id=1)
        o = models.Ope.objects.get(pk=11)
        r = models.Rapp.objects.get(id=1)
        o.rapp = r
        o.save()
        data = {'tiers': t.id, 'compte': cpt.id, 'cat': c.id, 'montant': 120, 'moyen': m.id, 'date': utils.now(), 'rapp': r.id}
        form = forms.OperationForm(data, instance=models.Ope.objects.get(pk=11))
        form.is_valid()
        self.assertEqual(form.errors, {'__all__': [u"impossible de modifier l'opération car au moins une partie est rapprochée", ]})

    def test_ope_clean_rapp5(self):
        """une mere pointee a son montant  changee"""
        t = models.Tiers.objects.get(id=1)
        c = models.Cat.objects.get(id=1)
        m = models.Moyen.objects.get(id=1)
        cpt = models.Compte.objects.get(id=1)
        o = models.Ope.objects.get(pk=13)
        r = models.Rapp.objects.get(id=1)
        o.rapp = r
        o.save()
        data = {'tiers': t.id, 'compte': cpt.id, 'cat': c.id, 'montant': 120, 'moyen': m.id, 'date': utils.now(), 'rapp': r.id}
        form = forms.OperationForm(data, instance=models.Ope.objects.get(pk=13))
        form.is_valid()
        self.assertEqual(form.errors, {'__all__': [u"impossible de modifier l'opération car au moins une partie est rapprochée", ]})

    def test_tot_fille(self):
        o = models.Ope.objects.get(pk=11)
        self.assertEqual(o.tot_fille, 100)

    def test_save_moyen_positif(self):
        o = models.Ope.objects.get(pk=1)
        m = models.Moyen.objects.get(id=1)
        o.moyen = m
        o.montant = 100
        o.save()
        self.assertEqual(models.Ope.objects.get(pk=1).montant, -100)

    def test_ope_clean_mere1(self):
        """pas de probleme (pas de pointe ni de rapp) change fille"""
        t = models.Tiers.objects.get(id=1)
        c = models.Cat.objects.get(id=1)
        m = models.Moyen.objects.get(id=1)
        cpt = models.Compte.objects.get(id=1)
        data = {'tiers': t.id, 'compte': cpt.id, 'cat': c.id, 'montant': 250, 'moyen': m.id, 'date': utils.now()}
        form = forms.OperationForm(data, instance=models.Ope.objects.get(pk=13))
        if form.is_valid():
            form.save()
        else:
            self.assertEqual(form.errors, "")
        self.assertTrue(models.Ope.objects.get(pk=13).is_fille)
        self.assertTrue(models.Ope.objects.get(pk=11).is_mere)
        self.assertEqual(models.Ope.objects.get(pk=13).montant, -250)
        self.assertEqual(models.Ope.objects.get(pk=11).montant, -151)

    def test_ope_clean_mere2(self):
        """pas de probleme (pas de pointe ni de rapp) change mere"""
        t = models.Tiers.objects.get(id=1)
        c = models.Cat.objects.get(id=1)
        m = models.Moyen.objects.get(id=4)
        cpt = models.Compte.objects.get(id=1)
        data = {'tiers': t.id, 'compte': cpt.id, 'cat': c.id, 'montant': 250, 'moyen': m.id, 'date': utils.now()}
        form = forms.OperationForm(data, instance=models.Ope.objects.get(pk=11))
        if form.is_valid():
            form.save()
        else:
            self.assertEqual(form.errors, "")
        self.assertTrue(models.Ope.objects.get(pk=11).is_mere)
        self.assertEqual(models.Ope.objects.get(pk=11).montant, 100)
        self.assertEqual(models.Ope.objects.get(pk=11).cat.nom, u"Opération Ventilée")

    def test_ope_moyen_def_recette1(self):
        t = models.Tiers.objects.get(id=1)
        c = models.Cat.objects.get(id=1)
        cpt = models.Compte.objects.get(id=1)
        data = {'tiers': t, 'compte': cpt, 'cat': c, 'montant': 120, 'moyen': None, 'date': utils.now()}
        models.Ope.objects.create(**data)
        o = models.Ope.objects.get(pk=14)
        self.assertEqual(o.moyen_id, 4)

    def test_ope_moyen_def_recette2(self):
        t = models.Tiers.objects.get(id=1)
        c = models.Cat.objects.get(id=1)
        cpt = models.Compte.objects.get(id=1)
        data = {'tiers': t, 'compte': cpt, 'cat': c, 'montant': -120, 'moyen': None, 'date': utils.now()}
        models.Ope.objects.create(**data)
        o = models.Ope.objects.get(pk=14)
        self.assertEqual(o.moyen_id, 1)

    def test_ope_moyen_def_recette3(self):
        t = models.Tiers.objects.get(id=1)
        c = models.Cat.objects.get(id=1)
        cpt = models.Compte.objects.get(id=5)
        data = {'tiers': t, 'compte': cpt, 'cat': c, 'montant': -120, 'moyen': None, 'date': utils.now()}
        models.Ope.objects.create(**data)
        o = models.Ope.objects.get(pk=14)
        self.assertEqual(o.moyen_id, 3)

    def test_ope_ferme(self):
        o = models.Ope.objects.get(pk=12)
        o.compte_id = 6
        self.assertRaises(IntegrityError, o.save)

    def test_ope_solde_set_nul(self):
        self.assertEqual(models.Ope.solde_set(models.Ope.objects.none()), 0)
        self.assertEqual(models.Ope.solde_set(models.Ope.objects.all()), -1476)

    def test_ope_iseditable(self):
        self.assertEqual(models.Ope.objects.get(pk=4).is_editable(), False)  # ope rapp
        self.assertEqual(models.Ope.objects.get(pk=12).is_editable(), True)  # ope normale
        self.assertEqual(models.Ope.objects.get(pk=11).is_editable(), False)  # ope mere

        # rajout d'une operation dans un compte ferme
        c = models.Compte.objects.get(id=6)
        t = models.Tiers.objects.get(id=1)
        c.ouvert = True
        c.save()
        o = models.Ope.objects.create(compte=c, date='2010-01-01', montant=-20, tiers=t, moyen=models.Moyen.objects.get(id=2))
        c.ouvert = False
        c.save()
        self.assertEqual(o.is_editable(), False)
        c.ouvert = False

        # ajout d'un virement rapproche
        o = models.Ope.objects.get(pk=9)
        o.rapp = models.Rapp.objects.get(id=1)
        o.save()
        o = models.Ope.objects.get(pk=8)
        self.assertEqual(o.is_editable(), False)

    def test_ope_rapp_pre_delete(self):
        # ope rapp
        self.assertRaises(IntegrityError, models.Ope.objects.get(id=3).delete)

    def test_ope_ope_titre(self):
        """verfication qu'un ope a bien une ope titre"""
        self.assertEqual(models.Ope.objects.get(pk=10).opetitre.id, 4)
        self.assertEqual(models.Ope.objects.get(pk=11).opetitre, None)

    def test_ope_ope_titre2(self):
        """test si vente"""
        t = models.Titre.objects.get(id=1)
        c = models.Compte.objects.get(id=4)
        c.vente(t, 2)
        o = models.Ope.objects.get(pk=15)
        self.assertEqual(o.opetitre.id, 5)

    def test_ope_titre_3(self):
        """test titres encours"""
        t = models.Titre.objects.get(id=1)
        c = models.Compte.objects.get(id=4)
        models.Cours.objects.get(id=1).delete()
        o=models.Ope_titre.objects.get(id=1)
        o.cours=5
        o.save()


    def test_pre_delete_ope_titre_rapp_ope_ost(self):
        #on rapproche l'ope ost
        o = models.Ope_titre.objects.get(id=4)
        o.ope_ost.rapp_id = 1
        o.save()
        self.assertRaises(IntegrityError, models.Ope_titre.objects.get(id=4).delete)
    def test_pre_delete_ope_titre_rapp_ope_pmv(self):
        t = models.Titre.objects.get(id=1)
        c = models.Compte.objects.get(id=4)
        c.vente(t, 2)
        #on rapproche l'ope ost
        o = models.Ope_titre.objects.get(id=5)
        o.ope_pmv.rapp_id = 1
        o.save()
        self.assertRaises(IntegrityError, models.Ope_titre.objects.get(id=5).delete)


    def test_pre_delete_ope_mere(self):
        o = models.Ope.objects.get(id=8)
        # on transforme l'ope 1 en ope mere
        o.mere_id = 4
        o.save()
        # on ne peut effacer un mere qui a encore des filles
        self.assertRaises(IntegrityError, models.Ope.objects.get(id=4).delete)

    def test_pre_delete_ope_rapp_mere(self):
        o = models.Ope.objects.get(id=8)
        o.rapp_id = None
        o.save()
        # on transforme l'ope 3 en ope mere
        o.mere_id = 3
        o.save()
        o = models.Ope.objects.get(id=3)
        o.rapp_id = 1
        o.save()
        # on ne peut effacer fille qui a une mere rapp
        o = models.Ope.objects.get(id=8)
        self.assertRaises(IntegrityError, o.delete)

    def test_pre_delete_ope_rapp_jumelle(self):
        o = models.Ope.objects.get(id=9)
        o.rapp_id = 1
        o.save()
        self.assertRaises(IntegrityError, models.Ope.objects.get(id=8).delete)

    def test_pre_delete_ope_titre_rapp(self):
        models.Compte.objects.get(id=5).achat(titre=models.Titre.objects.get(id=1), nombre=20, date='2011-01-01')
        o = models.Ope.objects.filter(compte=models.Compte.objects.get(id=5), date='2011-01-01')[0]
        o.rapp = models.Rapp.objects.get(id=1)
        o.save()
        self.assertRaises(IntegrityError, models.Ope_titre.objects.get(id=o.ope_titre_ost.id).delete)

    def test_pre_save_ope_mere(self):
        o = models.Ope.objects.get(id=11)
        o.cat = models.Cat.objects.get(id=1)
        o.save()
        o = models.Ope.objects.get(id=11)
        self.assertEquals(o.cat.nom, u"Opération Ventilée")
        o.montant = 154563
        o.save()
        o = models.Ope.objects.get(id=11)
        self.assertEquals(o.montant, 100)

    def test_virement_error(self):
        # _non_ope
        self.assertRaises(TypeError, lambda: models.Virement('35'))
        # creation avec autre que ope
        c = models.Compte.objects.get(id=1)
        nc = "ceci est un compte en fait mais non"
        v = models.Virement()
        self.assertRaises(TypeError, lambda: v.create(compte_origine=nc, compte_dest=c, montant=2))
        self.assertRaises(TypeError, lambda: v.create(compte_origine=c, compte_dest=nc, montant=2))
        # save non init
        self.assertRaises(models.Gsb_exc, lambda: models.Virement().save())
        # form unbound
        self.assertRaises(models.Gsb_exc, lambda: models.Virement().init_form())

    def test_virement_verif_property(self):
        v = models.Virement(models.Ope.objects.get(id=8))
        self.assertEquals(v.origine.id, 8)
        self.assertEquals(v.dest.id, 9)
        self.assertEquals(v.origine.compte, models.Compte.objects.get(nom='cpte1'))
        self.assertEquals(v.dest.compte, models.Compte.objects.get(nom='cptb3'))
        self.assertEquals(v.date, utils.strpdate('2011-10-30'))
        self.assertEquals(v.montant, v.origine.montant * -1)
        self.assertEquals(v.montant, v.dest.montant)
        self.assertEquals(v.montant, 100)
        self.assertEquals(v.__unicode__(), u"cpte1 => cptb3")
        self.assertEquals(v.auto, False)
        self.assertEquals(v.exercice, None)
        v.date_val = '2011-02-01'
        v.pointe = True
        v.save()
        self.assertEquals(models.Virement(models.Ope.objects.get(id=8)).date_val, utils.strpdate('2011-02-01'))
        self.assertEquals(models.Virement(models.Ope.objects.get(id=8)).pointe, True)

    def test_virement_inverse(self):
        v = models.Virement(models.Ope.objects.get(id=9))
        self.assertEquals(v.origine.id, 8)
        self.assertEquals(v.dest.id, 9)
        self.assertEquals(v.origine.compte, models.Compte.objects.get(nom='cpte1'))
        self.assertEquals(v.dest.compte, models.Compte.objects.get(nom='cptb3'))
        self.assertEquals(v.date, utils.strpdate('2011-10-30'))
        self.assertEquals(v.montant, v.origine.montant * -1)
        self.assertEquals(v.montant, v.dest.montant)
        self.assertEquals(v.montant, 100)
        self.assertEquals(v.__unicode__(), u"cpte1 => cptb3")
        self.assertEquals(v.auto, False)
        self.assertEquals(v.exercice, None)
        v.date_val = '2011-02-01'
        v.pointe = True
        v.save()
        self.assertEquals(models.Virement(models.Ope.objects.get(id=8)).date_val, utils.strpdate('2011-02-01'))
        self.assertEquals(models.Virement(models.Ope.objects.get(id=8)).pointe, True)

    def test_virement_edit(self):
        v = models.Virement(models.Ope.objects.get(id=8))
        v.date = '2011-02-01'
        v.save()

    @mock.patch('gsb.utils.today')
    def test_virement_create(self, today_mock):
        today_mock.return_value = datetime.date(2012, 10, 14)
        v = models.Virement.create(models.Compte.objects.get(id=1), models.Compte.objects.get(id=2), 20)
        self.assertEqual(models.Compte.objects.get(id=1).solde(), -90)
        self.assertEquals(v.origine.compte, models.Compte.objects.get(nom='cpte1'))
        self.assertEquals(v.dest.compte, models.Compte.objects.get(nom='cptb2'))
        self.assertEquals(v.origine.id, 14)
        self.assertEquals(v.date, datetime.date(2012, 10, 14))
        self.assertEquals(v.montant, v.origine.montant * -1)
        self.assertEquals(v.montant, v.dest.montant)
        self.assertEquals(v.montant, 20)
        v = models.Virement.create(models.Compte.objects.get(id=1), models.Compte.objects.get(id=2), 20, '2010-01-01', 'test_notes')
        self.assertEqual(models.Compte.objects.get(id=1).solde(), -110)
        self.assertEqual(models.Compte.objects.get(id=2).solde(), 40)
        self.assertEqual(v.date, '2010-01-01')
        self.assertEqual(v.notes, 'test_notes')
    @mock.patch('gsb.utils.today')
    def test_virement_create_avec_probleme(self, today_mock):
        today_mock.return_value = datetime.date(2012, 10, 14)
        self.assertRaises(TypeError, models.Virement.create,models.Compte.objects.get(id=2), models.Compte.objects.get(id=2), 20)


    def test_virement_delete(self):
        v = models.Virement.create(models.Compte.objects.get(id=1), models.Compte.objects.get(id=2), 20)
        v.delete()
        self.assertEquals(models.Compte.objects.get(nom='cpte1').solde(), -70)
        self.assertEquals(models.Compte.objects.get(nom='cptb2').solde(), 0)

    def test_virement_init_form(self):
        v = models.Virement.create(models.Compte.objects.get(id=1), models.Compte.objects.get(id=2), 20, '2010-01-01', 'test_notes')
        tab = {'compte_origine': 1,
               'compte_destination': 2,
               'montant': 20,
               'date': "2010-01-01",
               'notes': 'test_notes',
               'pointe': False,
               'moyen_origine': 6,
               'moyen_destination': 6
        }
        self.assertEquals(tab, v.init_form())

class Test_models2(TestCase):
    def setUp(self):
        super(Test_models2, self).setUp()
        # on cree les elements indispensables
        import_base.Cat_cache(self.request_get('toto'))
        import_base.Moyen_cache(self.request_get('toto'))
        import_base.Tiers_cache(self.request_get('toto'))
        self.c = models.Compte.objects.create(nom="cpt_titre1")
        self.t = models.Titre.objects.create(isin="0000", nom="titre1")
        self.r = models.Rapp.objects.create(nom="rapp1", date=utils.strpdate('2012-01-20'))

    # sans fixtures

    def test_last_cours_date_special(self):
        """last cours avec ope cree, modifie puis effacee"""
        c = self.c
        t = self.t
        r = self.r
        c.achat(t, 10, date=utils.strpdate('2012-01-01'))
        o = models.Ope.objects.get(id=1)
        o.rapp = r
        o.save()
        cours = t.last_cours_date(rapp=True)
        self.assertEquals(cours, utils.strpdate('2012-01-01'))
        models.Cours.objects.get(id=1).delete()
        cours = t.last_cours_date(rapp=True)
        self.assertEquals(cours, None)

    def test_ope_titre_special3(self):
        """encours simple mais le cours a change entre temps"""
        c = self.c
        t = self.t
        o = models.Ope_titre.objects.create(titre=t, compte=c, date=utils.strpdate('2011-01-01'), nombre=10)
        o.cours = 3
        o.save()
        self.assertEqual(t.encours(), 30)

    def test_compte_solde_avec_solde_init(self):
        c = models.Compte.objects.create(nom="bhh", solde_init=5)
        t = models.Tiers.objects.create(nom='teet')
        self.assertEqual(c.solde(), 5)
        models.Ope.objects.create(date=utils.strpdate("2011-01-01"), montant=12, compte=c, tiers=t)
        self.assertEqual(c.solde(), 17)

    @mock.patch('gsb.utils.today')
    def test_revenu_today(self, today_mock):
        today_mock.return_value = datetime.date(2012, 10, 14)
        c = self.c
        t = self.t
        c.achat(titre=t, nombre=1, prix=1)
        c.revenu(titre=t, montant=20)
        self.assertEqual(t.investi(c), -19)
        self.assertEqual(c.solde(), 19)

    def test_compte_moyen_credit_et_debit(self):
        c1 = models.Compte.objects.create(nom="les2",
                                   moyen_credit_defaut=models.Moyen.objects.create(nom="uniquement_credit", type='c'),
                                   moyen_debit_defaut=models.Moyen.objects.create(nom="uniquement_debit", type='d')
        )
        c2 = models.Compte.objects.create(nom="aucun")
        self.assertEqual(c1.moyen_credit().nom, "uniquement_credit")
        self.assertEqual(c1.moyen_debit().nom, "uniquement_debit")
        self.assertEqual(c2.moyen_credit().id, settings.MD_CREDIT)
        self.assertEqual(c2.moyen_debit().id, settings.MD_DEBIT)

    def test_has_changed(self):
        t = models.Tiers.objects.create(nom='teet')
        t.nom = "toto"
        self.assertEqual(models.has_changed(t, ('nom', 'notes')), True)
        self.assertEqual(models.has_changed(t, ('nom',)), True)
        self.assertEqual(models.has_changed(t, 'nom'), True)
        t.notes = "notes"
        self.assertEqual(models.has_changed(t, ('nom', 'notes')), True)

    def test_has_changed2(self):
        """verifie si on a rien change par defaut"""
        t = models.Tiers.objects.create(nom='teet')
        self.assertEqual(models.has_changed(t, ('nom', 'notes')), False)

    def test_has_changed3(self):
        """verifie si qd on envoit une string et non un objet ds haschanged"""
        self.assertEqual(models.has_changed('toto', ('nom', 'notes')), False)
