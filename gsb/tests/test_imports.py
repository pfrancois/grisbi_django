# -*- coding: utf-8 -*
"""
test import
"""
from __future__ import absolute_import
from .test_base import TestCase
# import decimal
# from gsb import forms as gsb_forms
from django.core.urlresolvers import reverse
import os.path
from django.conf import settings
import gsb.utils as utils
# import mock
# import datetime
from .. import models
from django.contrib.auth.models import User
from ..io import import_base
import glob

__all__ = ['Test_import_csv', 'Test_import_base']


class Test_import_abstract(TestCase):

    def setUp(self):
        super(Test_import_abstract, self).setUp()
        self.user = User.objects.create_user(username='admin', password='mdp', email="toto@toto.com")
        self.client.login(username='admin', password='mdp')

    def tearDwon(self):
        nomfich = os.path.join(settings.PROJECT_PATH, 'upload', "test_*")
        os.remove(nomfich)


class Test_import_csv(Test_import_abstract):

    def test_import_csv_simple_ok(self):
        """test import csv version sans jumelle ni ope mere bref en ne gerant pas les id mais gere les virement et les ope titre"""
        with open(os.path.join(settings.PROJECT_PATH, "gsb", "test_files", "test_import_export.csv")) as file_test:
            r = self.client.post(reverse('import_csv_ope_simple'), {'nom_du_fichier': file_test})
            for name in glob.glob(os.path.join(settings.PROJECT_PATH, 'upload', 'import_simple*')):  # on efface les fichier crée par le test
                os.remove(name)
        # self.assertcountmessage(self.client.request(),36)
        self.assertEqual(r.status_code, 302)
        self.assertQueryset_list(models.Tiers.objects.all(), [u'tiers1', u'tiers2', u'cpte1 => cptb3', u'titre_ autre', u'secu', u'titre_ t1', u'titre_ t2'], 'nom')  # ne pas oublier le tiers cree automatiquement
        self.assertEquals(models.Ope.objects.all().count(), 16)
        self.assertQueryset_list(models.Cat.objects.all(),
                                 [u'cat1', u'cat2',
                                  u'Frais bancaires', u"Opération Ventilée", u"Opération sur titre",
                                  u"Revenus de placements:Plus-values", u'Impôts:Cotisations sociales',
                                  u'Revenus de placements:interets', u'Virement', u"Non affecté"],
                                'nom')  # ne pas oublier les cat cree automatiquement
        self.assertQueryset_list(models.Rapp.objects.all(), ["cpt_titre2201101", "cpte1201101"], "nom")
        self.assertEqual(models.Rapp.objects.get(nom="cpte1201101").solde, 10)
        self.assertEqual(models.Compte.objects.get(nom="cpte1").solde(), -270)
        self.assertEqual(models.Compte.objects.get(nom="cpt_titre2").solde(), 100)
        self.assertQueryset_list(models.Ib.objects.all(), ['ib1', 'ib2'], "nom")
        self.assertEqual(models.Ope.objects.get(id=14).notes, '')
        self.assertEqual(models.Ope.objects.get(id=1).rapp.id, 1)
        self.assertEqual(models.Ope.objects.get(id=3).ib.nom, 'ib1')
        self.assertEqual(models.Ope.objects.get(id=1).num_cheque, '12345678')


class Test_import_base(Test_import_abstract):

    def test_import_base(self):
        prop = import_base.property_ope_base()
        self.assertEqual(prop.id, None)
        self.assertEqual(prop.cat, None)
        self.assertEqual(prop.automatique, False)
        self.assertEqual(prop.cpt, None)
        self.assertEqual(prop.date, None)
        self.assertEqual(prop.date_val, None)
        self.assertEqual(prop.exercice, None)
        self.assertEqual(prop.ib, None)
        self.assertEqual(prop.jumelle, None)
        self.assertEqual(prop.mere, None)
        self.assertEqual(prop.montant, 0)
        self.assertEqual(prop.moyen, None)
        self.assertEqual(prop.rapp, None)
        self.assertEqual(prop.notes, "")
        self.assertEqual(prop.num_cheque, "")
        self.assertEqual(prop.piece_comptable, "")
        self.assertEqual(prop.pointe, False)
        self.assertEqual(prop.tiers, None)
        self.assertEqual(prop.monnaie, None)
        self.assertEqual(prop.ope_titre, False)
        self.assertEqual(prop.ope_pmv, False)
        self.assertEqual(prop.ligne, 0)
        self.assertEqual(prop.has_fille, False)

    def test_import_exception(self):
        with self.assertRaises(import_base.ImportException) as exc:
            raise import_base.ImportException('test')
        self.assertEqual(exc.exception.msg, 'test')
        self.assertEqual("%s" % exc.exception, 'test')

    def test_cat_cache(self):
        # on teste si les categories par defaut sont bien crees
        import_base.Cat_cache(self.request_get("/outils"))
        self.assertEqual(models.Cat.objects.get(nom=u"Opération sur titre").id, 64)
        self.assertEqual(models.Cat.objects.get(nom="Revenus de placements:Plus-values").id, 67)
        self.assertEqual(models.Cat.objects.get(nom="Revenus de placements:interets").id, 68)
        self.assertEqual(models.Cat.objects.get(nom=u'Impôts:Cotisations sociales').id, 54)
        self.assertEqual(models.Cat.objects.get(nom=u'Virement').id, 65)
        self.assertEqual(models.Cat.objects.get(nom=u"Opération Ventilée").id, 66)
        self.assertEqual(models.Cat.objects.get(nom=u"Frais bancaires").id, 69)
        self.assertEqual(models.Cat.objects.get(nom=u"Non affecté").id, 70)

    def test_cat_cache2(self):
        # test avec definition de l'ensemble
        cats = import_base.Cat_cache(self.request_get("/outils"))
        self.assertEqual(cats.goc('test', {'nom': 'test', 'id': 1215, 'type': 'd'}), 1215)

    def test_cat_cache2bis(self):
        # test avec definition de l'ensemble
        cats = import_base.Cat_cache(self.request_get("/outils"))
        self.assertEqual(cats.goc('', {'nom': 'test', 'id': 1215, 'type': 'd'}), 1215)

    def test_cat_cache3(self):
        # test normal
        cats = import_base.Cat_cache(self.request_get("/outils"))
        cats.goc("cat1")  # on cree
        self.assertEqual(cats.goc("cat1"), models.Cat.objects.get(nom=u"cat1").id)  # on demande

    def test_cat_cache4(self):
        # test integrity error
        cats = import_base.Cat_cache(self.request_get("/outils"))
        cats.goc('test', {'nom': 'test', 'id': 1215, 'type': 'd'})
        with self.assertRaises(import_base.ImportException):
            cats.goc('test2', {'nom': 'test2', 'id': 1215, 'type': 'd'})
        del cats.id['test']
        with self.assertRaises(import_base.ImportException):
            cats.goc('test', {'nom': 'test', 'id': 1215, 'type': 'c'})
        with self.assertRaises(KeyError):
            cats.id['test']
        with self.assertRaises(import_base.ImportException):
            cats.goc('test', {'nom': 'test', 'id': 1216, 'type': 'c'})

    def test_cat_cache5(self):
        # test creation et readonly
        cats = import_base.Cat_cache(self.request_get("/outils"))
        cats.readonly = True
        with self.assertRaises(import_base.ImportException) as exc:
            cats.goc("cat1")
        self.assertEqual(exc.exception.msg, u"Cat 'cat1' non créée alors que c'est read only")

    def test_cat_cache6(self):
        # on teste si on peut bien recuperer une cat deja existante
        cats = import_base.Cat_cache(self.request_get("/outils"))
        cat_id = models.Cat.objects.create(nom='test').id
        self.assertEqual(cats.goc("test"), cat_id)

    def test_moyen_cache1(self):
        """test des moyens cree automatiquement"""
        import_base.Moyen_cache(self.request_get("/outils"))
        self.assertEqual(models.Moyen.objects.filter(id=settings.MD_CREDIT).count(), 1)
        self.assertEqual(models.Moyen.objects.filter(id=settings.MD_DEBIT).count(), 1)

    def test_moyen_cache2(self):
        """test d'un nouveau moyen"""
        moyens = import_base.Moyen_cache(self.request_get("/outils"))
        self.assertEqual(moyens.goc("moyen1", montant=10), 6)

    def test_moyen_cache3(self):
        """test de nouveau moyen avec obj et sans obj"""
        moyens = import_base.Moyen_cache(self.request_get("/outils"))
        models.Moyen.objects.create(nom='test', type='d', id=30)
        self.assertEqual(moyens.goc("test", montant=-10), 30)
        self.assertEqual(moyens.goc("test2", obj={"nom": 'test2', 'type': 'r', 'id': 31}), 31)
        m = models.Moyen.objects.get(id=31)
        self.assertEqual(m.nom, 'test2')
        self.assertEqual(m.type, 'r')

    def test_moyen_cache4(self):
        """test d'un nouveau moyen avec un montant <0"""
        moyens = import_base.Moyen_cache(self.request_get("/outils"))
        self.assertEqual(moyens.goc("test", montant=-10), 6)
        m = models.Moyen.objects.get(id=6)
        self.assertEqual(m.nom, 'test')
        self.assertEqual(m.type, 'd')

    def test_moyen_cache5(self):
        """test d'un nouveau moyen avec un montant >0"""
        moyens = import_base.Moyen_cache(self.request_get("/outils"))
        self.assertEqual(moyens.goc("test", montant=10), 6)
        m = models.Moyen.objects.get(id=6)
        self.assertEqual(m.nom, 'test')
        self.assertEqual(m.type, 'r')

    def test_moyen_cache6(self):
        """test avec des erreurs"""
        moyens = import_base.Moyen_cache(self.request_get("/outils"))
        with self.assertRaises(ValueError):
            moyens.goc("test", montant=None, obj=None)

    def test_ib_cache(self):
        ibs = import_base.IB_cache(self.request_get("/outils"))
        self.assertEqual(ibs.goc("moyen1"), 1)
        models.Ib.objects.create(nom='test', type='d', id=30)
        self.assertEqual(ibs.goc("test"), 30)
        self.assertEqual(ibs.goc("test2", {"nom": 'test2', 'type': 'r', 'id': 31}), 31)
        m = models.Ib.objects.get(id=31)
        self.assertEqual(m.id, 31)
        self.assertEqual(m.nom, 'test2')
        self.assertEqual(m.type, 'r')

    def test_compte_cache(self):
        cpts = import_base.Compte_cache(self.request_get("/outils"))
        self.assertEqual(cpts.goc("moyen1"), 1)
        m = models.Compte.objects.get(id=1)
        self.assertEqual(m.nom, 'moyen1')
        self.assertEqual(m.type, 'b')
        self.assertEqual(m.moyen_credit_defaut_id, settings.MD_CREDIT)
        models.Compte.objects.create(nom='test', type='b', id=30)
        self.assertEqual(cpts.goc("test"), 30)
        m = models.Compte.objects.get(id=30)
        self.assertEqual(m.id, 30)
        self.assertEqual(m.nom, 'test')
        self.assertEqual(m.type, 'b')
        self.assertEqual(cpts.goc("test2", {"nom": 'test2', 'type': 'e', 'id': 31}), 31)
        m = models.Compte.objects.get(id=31)
        self.assertEqual(m.id, 31)
        self.assertEqual(m.nom, 'test2')
        self.assertEqual(m.type, 'e')
        self.assertEqual(m.moyen_credit_defaut_id, None)

    def test_banque_cache(self):
        cache = import_base.Banque_cache(self.request_get("/outils"))
        self.assertEqual(cache.goc("bq1"), 1)
        m = models.Banque.objects.get(id=1)
        self.assertEqual(m.nom, 'bq1')
        models.Banque.objects.create(nom='test', id=30)
        self.assertEqual(cache.goc("test"), 30)
        m = models.Banque.objects.get(id=30)
        self.assertEqual(m.id, 30)
        self.assertEqual(m.nom, 'test')
        self.assertEqual(cache.goc("test2", {"nom": 'test2', 'id': 31}), 31)
        m = models.Banque.objects.get(id=31)
        self.assertEqual(m.id, 31)
        self.assertEqual(m.nom, 'test2')

    def test_tiers_cache(self):
        cache = import_base.Tiers_cache(self.request_get("/outils"))
        self.assertEqual(cache.goc("t1"), 257)
        m = models.Tiers.objects.get(id=257)
        self.assertEqual(m.nom, 't1')
        models.Tiers.objects.create(nom='test', id=30)
        self.assertEqual(cache.goc("test"), 30)
        m = models.Tiers.objects.get(id=30)
        self.assertEqual(m.id, 30)
        self.assertEqual(m.nom, 'test')
        self.assertEqual(cache.goc("test2", {"nom": 'test2', 'id': 31}), 31)
        m = models.Tiers.objects.get(id=31)
        self.assertEqual(m.id, 31)
        self.assertEqual(m.nom, 'test2')

    def test_exercice_cache(self):
        cache = import_base.Exercice_cache(self.request_get('toto'))
        self.assertEqual(cache.goc("exo1"), 1)
        m = models.Exercice.objects.get(id=1)
        self.assertEqual(m.nom, 'exo1')
        self.assertEqual(m.date_debut, utils.today())
        self.assertEqual(m.date_fin, utils.today())
        models.Exercice.objects.create(nom='test', id=30, date_debut=utils.today(), date_fin=utils.today())
        self.assertEqual(cache.goc("test"), 30)
        m = models.Exercice.objects.get(id=30)
        self.assertEqual(m.id, 30)
        self.assertEqual(m.nom, 'test')
        self.assertEqual(cache.goc("test2", {"nom": 'test2', 'id': 31, 'date_debut': utils.today(), 'date_fin': utils.today()}), 31)
        m = models.Exercice.objects.get(id=31)
        self.assertEqual(m.id, 31)
        self.assertEqual(m.date_debut, utils.today())
        self.assertEqual(m.date_fin, utils.today())
        self.assertEqual(m.nom, 'test2')

    def test_titre_cache(self):
        cache = import_base.Titre_cache(self.request_get('toto'))
        tata = cache.goc("titre1")
        self.assertEqual(tata, 1)
        self.assertEqual(cache.goc(isin="%s%s" % (1, utils.today())), 1)
        m = models.Titre.objects.get(id=1)
        self.assertEqual(m.nom, 'titre1')
        self.assertEqual(m.type, 'ZZZ')
        self.assertEqual(m.isin, "%s%s" % (1, utils.today()))
        self.assertEqual(cache.goc(isin="isin1"), 2)
        self.assertEqual(cache.goc("inconnu%s%s" % (2, utils.today())), 2)
        m = models.Titre.objects.get(id=2)
        self.assertEqual(m.nom, "inconnu%s%s" % (2, utils.today()))
        self.assertEqual(m.type, 'ZZZ')
        self.assertEqual(m.isin, 'isin1')
        self.assertEqual(cache.goc("titre_ titre1"), 1)
        self.assertEqual(cache.goc('titre3', obj={"nom": 'titre3', "isin": 'ceci est un isin', "type": "ZZZ", 'id': 23553}), 23553)
        m = models.Titre.objects.get(id=23553)
        self.assertEqual(m.nom, 'titre3')
        with self.assertRaises(import_base.ImportException):
            cache.goc("titre4", obj={"nom": 'titre4', "isin": 'ceci est un isin', "type": "ZZZ", 'id': 23553})

    def test_titre_cache2(self):
        """essai de creer un titre alors qu'on est en read only"""
        cache = import_base.Titre_cache(self.request_get('toto'))
        cache.readonly = True
        with self.assertRaises(import_base.ImportException):
            cache.goc("titre1")

    def test_titre_cache3(self):
        """interogation sans parametre"""
        cache = import_base.Titre_cache(self.request_get('toto'))
        self.assertEqual(cache.goc(), None)

    def test_cours_cache(self):
        # version avec nom titre
        titres = import_base.Titre_cache(self.request_get('toto'))
        cache = import_base.Cours_cache(self.request_get('toto'), titres)
        self.assertEqual(cache.goc("titre1", utils.strpdate("2011-01-01"), 150), 1)
        self.assertEqual(titres.goc("titre1"), 1)
        m = models.Cours.objects.get(id=1)
        self.assertEqual(m.valeur, 150)
        self.assertEqual(m.titre.nom, "titre1")
        self.assertEqual(m.date, utils.strpdate("2011-01-01"))
        self.assertEqual(cache.goc("titre1", utils.strpdate("2011-01-01"), 150), 1)

    def test_cours_cache2(self):
        # version avec isin
        titres = import_base.Titre_cache(self.request_get('toto'))
        cache = import_base.Cours_cache(self.request_get('toto'), titres)
        self.assertEqual(cache.goc("isin1", utils.strpdate("2011-01-01"), 150, methode='isin'), 1)
        self.assertEqual(titres.goc(isin="isin1"), 1)
        m = models.Cours.objects.get(id=1)
        self.assertEqual(m.valeur, 150)
        self.assertEqual(m.titre.isin, "isin1")
        self.assertEqual(m.date, utils.strpdate("2011-01-01"))

    def test_cours_cache3(self):
        # meme date, cours different
        titres = import_base.Titre_cache(self.request_get('toto'))
        cache = import_base.Cours_cache(self.request_get('toto'), titres)
        cache.goc("titre1", utils.strpdate("2011-01-01"), 150, methode='isin')
        del cache.id[1]
        with self.assertRaises(import_base.ImportException):
            cache.goc("titre1", utils.strpdate("2011-01-01"), 200, methode='isin')

    def test_rapp_cache(self):
        cache = import_base.Rapp_cache(self.request_get("/outils"))
        self.assertEqual(cache.goc("t1", utils.strpdate("2011-01-01")), 1)
        self.assertEqual(cache.goc("t1", utils.strpdate("2011-01-05")), 1)
        cache.sync_date()
        m = models.Rapp.objects.get(id=1)
        self.assertEqual(m.date, utils.strpdate("2011-01-05"))
        self.assertEqual(cache.goc(obj={'nom': 't', 'date': utils.strpdate("2011-01-05"), 'id': 255}), 255)

    def test_rapp_cache2(self):
        cache = import_base.Rapp_cache(self.request_get("/outils"))
        self.assertEqual(cache.goc(None, utils.strpdate("2011-01-05"), None), None)
        self.assertEqual(cache.goc("", utils.strpdate("2011-01-05"), None), None)

    def test_moyen_defaut(self):
        moyens = import_base.Moyen_cache(self.request_get("/outils"))
        # on cree les deux comptes utiles
        models.Compte.objects.create(nom="sansrien")
        models.Compte.objects.create(nom="les2", moyen_credit_defaut_id=moyens.goc("uniquement_credit", montant=10), moyen_debit_defaut_id=moyens.goc("uniquement_debit", montant=-10))
        cache = import_base.moyen_defaut_cache()
        self.assertEqual(cache.goc("sansrien", 10), settings.MD_CREDIT)
        self.assertEqual(cache.goc("sansrien", -10), settings.MD_DEBIT)
        self.assertEqual(cache.goc("les2", 10), 6)
        self.assertEqual(cache.goc("les2", -10), 7)
        self.assertEqual(cache.goc("test", 10), settings.MD_CREDIT)
        self.assertEqual(cache.goc("test", -10), settings.MD_DEBIT)
