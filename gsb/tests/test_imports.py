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
# import gsb.utils as utils
# import mock
# import datetime
from .. import models
from django.contrib.auth.models import User
from ..io import import_base
import glob
import os
__all__ = ['Test_import', ]


class Test_import(TestCase):

    def setUp(self):
        super(Test_import, self).setUp()
        self.user = User.objects.create_user(username='admin', password='mdp', email="toto@toto.com")
        self.client.login(username='admin', password='mdp')

    def test_import_csv_ok(self):
        with open(os.path.join(settings.PROJECT_PATH, "gsb", "test_files", "import_simple.csv"))  as file_test:
            r = self.client.post(reverse('import_csv_ope_all'), {'nom_du_fichier': file_test})
            self.assertEqual(r.status_code, 302)
            self.assertEqual(models.Tiers.objects.count(), 3)
            self.assertEqual(models.Ope.objects.count(), 4)
            self.assertEqual(models.Cat.objects.count(), 8)
            self.assertEqual(models.Compte.objects.get(nom="cpte1").solde(), -4)
            self.assertEqual(models.Compte.objects.get(nom="cptb2").solde(), -54)
        for name in glob.glob(os.path.join(settings.PROJECT_PATH, 'upload', 'import_simple*')):
                os.remove(name)

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
        self.assertEqual(prop.num_cheque, None)
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
        cats = import_base.Cat_cache(self.request_get("/outils"))
        self.assertEqual(models.Cat.objects.filter(nom=u"Opération sur titre").count(), 1)
        self.assertEqual(models.Cat.objects.filter(nom="Revenus de placements:Plus-values").count(), 1)
        self.assertEqual(models.Cat.objects.filter(nom=settings.REV_PLAC).count(), 1)
        self.assertEqual(models.Cat.objects.filter(nom=u'Impôts:Cotisations sociales').count(), 1)
        self.assertEqual(cats.goc('Opération sur titre'), settings.ID_CAT_OST)

    def test_cat_cache2(self):
        # test avec definition de l'ensemble
        cats = import_base.Cat_cache(self.request_get("/outils"))
        self.assertEqual(cats.goc('test', {'nom': 'test', 'id': 1215, 'type': 'd'}), 1215)

    def test_cat_cache3(self):
        # test normal
        cats = import_base.Cat_cache(self.request_get("/outils"))
        self.assertEqual(cats.goc("cat1"), 69)
        self.assertEqual(models.Cat.objects.filter(nom=u"cat1").count(), 1)

    def test_cat_cache4(self):
        # test integrity error
        cats = import_base.Cat_cache(self.request_get("/outils"))
        with self.assertRaises(import_base.ImportException):
            self.assertEqual(cats.goc('test', {'nom': 'test', 'id': 1215, 'type': 'd'}), 1215)
            self.assertEqual(cats.goc('test2', {'nom': 'test2', 'id': 1215, 'type': 'd'}), 1215)

    def test_cat_cache5(self):
        # test creation et readonly
        cats = import_base.Cat_cache(self.request_get("/outils"))
        cats.readonly = True
        with self.assertRaises(import_base.ImportException) as exc:
            self.assertEqual(cats.goc("cat1"), 69)
        self.assertEqual(exc.exception.msg, u"Cat 'cat1' non créée alors que c'est read only")

    def test_cat_cache6(self):
        # on teste si on peut bien recuperer une cat deja existante
        cats = import_base.Cat_cache(self.request_get("/outils"))
        models.Cat.objects.create(nom='test')
        self.assertEqual(cats.goc("test"), 69)

    def test_cat_cache7(self):
        # on teste si on peut bien recuperer une cat de virement deja existante
        models.Cat.objects.create(nom='test', type='v', pk=30)
        cats = import_base.Cat_cache(self.request_get("/outils"))
        self.assertEqual(cats.goc("Virement"), 30)

    def test_moyen_cache1(self):
        moyens = import_base.Moyen_cache(self.request_get("/outils"))
        self.assertEqual(models.Moyen.objects.filter(id=settings.MD_CREDIT).count(), 1)
        self.assertEqual(models.Moyen.objects.filter(id=settings.MD_DEBIT).count(), 1)
        self.assertEqual(moyens.goc("moyen1"), 5)
        models.Moyen.objects.create(nom='test', type='d', id=30)
        self.assertEqual(moyens.goc("test"), 30)
        self.assertEqual(moyens.goc("test2", {"nom": 'test2', 'type': 'r', 'id': 31}), 31)
        m = models.Moyen.objects.get(id=31)
        self.assertEqual(m.id, 31)
        self.assertEqual(m.nom, 'test2')
        self.assertEqual(m.type, 'r')

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
        self.assertEqual(m.id, 1)
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
        self.assertEqual(m.id, 1)
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
