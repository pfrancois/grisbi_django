# -*- coding: utf-8 -*
"""
test import
"""
from __future__ import absolute_import

# from gsb import forms as gsb_forms
from django.core.urlresolvers import reverse

from django.test.utils import override_settings
from django.conf import settings
from django.contrib.auth.models import User

import os.path
import datetime
import glob
from decimal import Decimal

from .test_base import TestCase
import gsb.utils as utils
from gsb import models
from gsb.io import import_base
from  gsb.io import import_csv
#import shutil
__all__ = ['Test_import_csv1', 'Test_import_base','Test_import_csv2']


class Test_import_abstract(TestCase):
    def setUp(self):
        super(Test_import_abstract, self).setUp()
        self.user = User.objects.create_user(username='admin', password='mdp', email="toto@toto.com")
        self.client.login(username='admin', password='mdp')


@override_settings(CONVERSION_CPT_TITRE=True)
class Test_import_csv1(Test_import_abstract):
    """test import csv version sans jumelle ni ope mere bref en ne gerant pas les id mais gere les virement et les ope titre"""
    def setUp(self):
        super(Test_import_csv1, self).setUp()
        self.cl=import_csv.Import_csv_ope_sans_jumelle_et_ope_mere()
        self.cl.request = self.request_get('outils')
        self.maxDiff=None

    def test_import_isin_defaut(self):
        self.assertEqual(import_base.isin_default(),"ZZ_1")

    def test_import_erreur_tableau(self):
        self.cl.init_cache()
        self.cl.erreur = list()
        self.moyen_virement = self.cl.moyens.goc('', {'nom': "Virement", 'type': 'v'})
        self.maxDiff=None
        cl=self.cl
        with open(os.path.join(settings.PROJECT_PATH, "gsb", "test_files", "test_import_export_erreur_de_date.csv")) as file_test:
            fich = cl.reader(file_test, encoding=cl.encoding)
            cl.tableau(fich,self.moyen_virement)
        self.assertEqual([u"erreur de date '2013/18/12' à la ligne 1",
                                    u"erreur de date '' à la ligne 3",
                                    u"attention il faut deux bouts à un virement ligne 4",
                                    u'attention, virement impossible entre le même compte à la ligne 5',
                                    u"le compte designé doit être un des deux comptes 'tiers' ligne 6",
                                    u"Ce tiers 't1' ne peut être un titre à la ligne 8"],cl.erreur)
        self.assertEqual(models.Compte.objects.get(nom='cpt_titre1').type,'t')
    def test_import_erreur_champ_incomplet(self):
        self.cl.init_cache()
        self.cl.erreur = list()
        self.moyen_virement = self.cl.moyens.goc('', {'nom': "Virement", 'type': 'v'})
        self.maxDiff=None
        cl=self.cl
        with open(os.path.join(settings.PROJECT_PATH, "gsb", "test_files", "test_import_export_erreur.csv")) as file_test:
            fich = cl.reader(file_test, encoding=cl.encoding)
            cl.tableau(fich,self.moyen_virement)
        self.assertEqual(cl.erreur,[u"il manque la/les colonne(s) 'date'"])
    def test_import_moyen_par_defaut(self):
        self.cl.init_cache()
        self.cl.erreur = list()
        self.moyen_virement = self.cl.moyens.goc('', {'nom': "Virement", 'type': 'v'})
        self.maxDiff=None
        cl=self.cl
        with open(os.path.join(settings.PROJECT_PATH, "gsb", "test_files", "test_import_export_2_moyens.csv")) as file_test:
            fich = cl.reader(file_test, encoding=cl.encoding)
            cl.tableau(fich,self.moyen_virement)
        attendu=[
            #depense de 100E non p , rapproche, sans notes
            {'ope_titre': False, 'pointe': False, 'montant': Decimal('-100'), 'date_val': None, 'tiers_id': 257, 'ligne': 1, 'rapp_id': 1, 'automatique': False, 'virement': False, 'num_cheque': u'12345678', 'moyen_id': 7, 'compte_id': 1, 'date': datetime.date(2011, 8, 11), 'notes': '', 'cat_id': 74, 'ib_id': None},
            #recette de 10E rapproche
            {'ope_titre': False, 'pointe': False, 'montant': Decimal('10'), 'date_val': None, 'tiers_id': 257, 'ligne': 2, 'rapp_id': 1, 'automatique': False, 'virement': False, 'num_cheque': '', 'moyen_id': 4, 'compte_id': 1, 'date': datetime.date(2011, 8, 11), 'notes': '', 'cat_id': 75, 'ib_id': None},
            ]
        self.assertEqual(attendu,cl.opes.created_items)
    def test_erreur_import_file(self):
        cl=self.cl
        nomfich=os.path.join(settings.PROJECT_PATH, "gsb", "test_files", "test_import_export_erreur_de_date.csv")
        retour=cl.import_file(nomfich)
        self.assertEqual(retour,False)
        self.assertEqual([u"erreur de date '2013/18/12' à la ligne 1",
                                    u"erreur de date '' à la ligne 3",
                                    u"attention il faut deux bouts à un virement ligne 4",
                                    u'attention, virement impossible entre le même compte à la ligne 5',
                                    u"le compte designé doit être un des deux comptes 'tiers' ligne 6",
                                    u"Ce tiers 't1' ne peut être un titre à la ligne 8"],cl.erreur)
        self.assertEqual(models.Compte.objects.get(nom='cpt_titre1').type,'t')
    def test_import_file_vir(self):
        cl=self.cl
        nomfich=os.path.join(settings.PROJECT_PATH, "gsb", "test_files", "test_import_export_3.csv")
        retour=cl.import_file(nomfich)
        self.assertEqual(retour,True)
        self.assertEqual(models.Ope.objects.count(),18)
        #rine/rien
        self.assertEqual(models.Ope.objects.get(pk=1).pointe,False)
        self.assertEqual(models.Ope.objects.get(pk=1).rapp_id,None)
        self.assertEqual(models.Ope.objects.get(pk=2).pointe,False)
        self.assertEqual(models.Ope.objects.get(pk=2).rapp_id,None)
        #rien/rapp
        self.assertEqual(models.Ope.objects.get(pk=3).pointe,False)
        self.assertEqual(models.Ope.objects.get(pk=3).rapp_id,None)
        self.assertEqual(models.Ope.objects.get(pk=4).pointe,False)
        self.assertEqual(models.Ope.objects.get(pk=4).rapp.nom,"cpte1201101")
        #rien/pointee
        self.assertEqual(models.Ope.objects.get(pk=5).pointe,False)
        self.assertEqual(models.Ope.objects.get(pk=5).rapp_id,None)
        self.assertEqual(models.Ope.objects.get(pk=6).pointe,True)
        self.assertEqual(models.Ope.objects.get(pk=6).rapp_id,None)
        #rapp/rien
        self.assertEqual(models.Ope.objects.get(pk=7).pointe,False)
        self.assertEqual(models.Ope.objects.get(pk=7).rapp.nom,"Rapp")
        self.assertEqual(models.Ope.objects.get(pk=8).pointe,False)
        self.assertEqual(models.Ope.objects.get(pk=8).rapp_id,None)
        #rapp/rapp
        self.assertEqual(models.Ope.objects.get(pk=9).pointe,False)
        self.assertEqual(models.Ope.objects.get(pk=9).rapp.nom,"Rapp")
        self.assertEqual(models.Ope.objects.get(pk=10).pointe,False)
        self.assertEqual(models.Ope.objects.get(pk=10).rapp.nom,"cpte1201101")
        #rapp/pointee
        self.assertEqual(models.Ope.objects.get(pk=11).pointe,False)
        self.assertEqual(models.Ope.objects.get(pk=11).rapp.nom,"Rapp")
        self.assertEqual(models.Ope.objects.get(pk=12).pointe,True)
        self.assertEqual(models.Ope.objects.get(pk=12).rapp_id,None)
        #pointee/rien
        self.assertEqual(models.Ope.objects.get(pk=13).pointe,True)
        self.assertEqual(models.Ope.objects.get(pk=13).rapp_id,None)
        self.assertEqual(models.Ope.objects.get(pk=14).pointe,False)
        self.assertEqual(models.Ope.objects.get(pk=14).rapp_id,None)
        #pointee/rapp
        self.assertEqual(models.Ope.objects.get(pk=15).pointe,True)
        self.assertEqual(models.Ope.objects.get(pk=15).rapp_id,None)
        self.assertEqual(models.Ope.objects.get(pk=16).pointe,False)
        self.assertEqual(models.Ope.objects.get(pk=16).rapp.nom,"cpte1201101")
        #pointee/pointee
        self.assertEqual(models.Ope.objects.get(pk=17).pointe,True)
        self.assertEqual(models.Ope.objects.get(pk=17).rapp_id,None)
        self.assertEqual(models.Ope.objects.get(pk=18).pointe,True)
        self.assertEqual(models.Ope.objects.get(pk=18).rapp_id,None)
        self.assertEqual(models.Rapp.objects.count(),2)
        self.assertmessagecontains(self.cl.request,"virement ope: (17) le 09/12/2013 : -100.00 EUR a cpte1 => cptb3 cpt: cpte1 ligne 9")
        self.assertmessagecontains(self.cl.request,"virement ope: (18) le 09/12/2013 : 100.00 EUR a cpte1 => cptb3 cpt: cptb3 ligne 9")

    def test_import_file_ope_titre(self):
        cl=self.cl
        nomfich=os.path.join(settings.PROJECT_PATH, "gsb", "test_files", "test_import_export_4.csv")
        retour=cl.import_file(nomfich)
        self.assertEqual(retour,True)
        self.assertEqual(models.Ope.objects.count(),4)
        self.assertmessagecontains(self.cl.request,"ope_titre: (1) le 18/12/2011 : -1 EUR a titre_ t1 cpt: cpt_titre1 ligne 1")
        self.assertmessagecontains(self.cl.request,"ope_titre: (2) le 24/09/2012 : -5 EUR a titre_ autre cpt: cpt_titre1 ligne 2")
        self.assertmessagecontains(self.cl.request,"ope_titre: (3) le 25/09/2012 : 5.00 EUR a titre_ autre cpt: cpt_titre1 ligne 3")
        self.assertmessagecontains(self.cl.request,"ope_titre(pmv): (4) le 25/09/2012 : 0.00 EUR a titre_ autre cpt: cpt_titre1 ligne 3")
        self.assertmessagecontains(self.cl.request,u"attention, fausse opération sur titre ligne 4")
        self.assertmessagecontains(self.cl.request,"impossible de vendre car pas de titre en portefeuille ligne 5")

    def test_import_tableau(self):
        self.cl.init_cache()
        self.cl.erreur = list()
        self.moyen_virement = self.cl.moyens.goc('', {'nom': "Virement", 'type': 'v'})
        self.maxDiff=None
        cl=self.cl
        with open(os.path.join(settings.PROJECT_PATH, "gsb", "test_files", "test_import_export_1.csv")) as file_test:
            fich = cl.reader(file_test, encoding=cl.encoding)
            cl.tableau(fich,self.moyen_virement)
        attendu=[
            #depense de 100E non p , rapproche, sans notes
            {'ope_titre': False, 'pointe': False, 'montant': Decimal('-100.00'), 'date_val': None, 'tiers_id': 257, 'ligne': 1, 'rapp_id': 1, 'automatique': False,  'virement': False, 'num_cheque': u'12345678', 'moyen_id': 7, 'compte_id': 1, 'date': datetime.date(2011, 8, 11), 'notes': '', 'cat_id': 74, 'ib_id': None},
            #recette de 10E rapproche
            {'ope_titre': False, 'pointe': False, 'montant': Decimal('10.00'), 'date_val': None, 'tiers_id': 257, 'ligne': 2, 'rapp_id': 1, 'automatique': False,  'virement': False, 'num_cheque': '', 'moyen_id': 8, 'compte_id': 1, 'date': datetime.date(2011, 8, 11), 'notes': '', 'cat_id': 75, 'ib_id': None},
            ##recette poitee de 10E
            {'ope_titre': False, 'pointe': True, 'montant': Decimal('10.00'), 'date_val': None, 'tiers_id': 257, 'ligne': 3, 'rapp_id': None, 'automatique': False,  'virement': False, 'num_cheque': '', 'moyen_id': 8, 'compte_id': 1, 'date': datetime.date(2011, 8, 11), 'notes': '', 'cat_id': 74, 'ib_id': 1},
            {'ope_titre': False, 'pointe': False, 'montant': Decimal('10.00'), 'date_val': None, 'tiers_id': 258, 'ligne': 4, 'rapp_id': None, 'automatique': False,  'virement': False, 'num_cheque': '', 'moyen_id': 8, 'compte_id': 1, 'date': datetime.date(2011, 8, 21), 'notes': u'fusion avec ope1', 'cat_id': 75, 'ib_id': 2},
            {'ope_titre': True, 'pointe': False, 'montant': Decimal('-100.00'), 'date_val': None, 'tiers_id': 259, 'ligne': 5, 'rapp_id': 2, 'automatique': False,  'virement': False, 'num_cheque': '', 'moyen_id': 9, 'compte_id': 2, 'date': datetime.date(2011, 10, 29), 'titre_id': 1, 'notes': u'20@5', 'cat_id': 64, 'ib_id': None},
            {'ope_titre': False, 'pointe': False, 'montant': Decimal('-100.00'), 'date_val': None, 'tiers_id': 260, 'ligne': 6, 'dest_id': 3, 'rapp_id': None, 'automatique': False,  'virement': True, 'num_cheque': '', 'moyen_id': 5, 'compte_id': 1, 'date': datetime.date(2011, 10, 30), 'notes': '', 'cat_id': 65, 'ib_id': None},
            {'ope_titre': True, 'pointe': False, 'montant': Decimal('-1500.00'), 'date_val': None, 'tiers_id': 259, 'ligne': 7, 'rapp_id': None, 'automatique': False,  'virement': False, 'num_cheque': '', 'moyen_id': 9, 'compte_id': 2, 'date': datetime.date(2011, 11, 30), 'titre_id': 1, 'notes': u'150@10', 'cat_id': 64, 'ib_id': None},
            {'ope_titre': True, 'pointe': False, 'montant': Decimal('-1.00'), 'date_val': None, 'tiers_id': 261, 'ligne': 8, 'rapp_id': None, 'automatique': False,  'virement': False, 'num_cheque': '', 'moyen_id': 10, 'compte_id': 4, 'date': datetime.date(2011, 12, 18), 'titre_id': 2, 'notes': u'1@1', 'cat_id': 64, 'ib_id': None},
            {'ope_titre': True, 'pointe': False, 'montant': Decimal('-5.00'), 'date_val': None, 'tiers_id': 262, 'ligne': 9, 'rapp_id': None, 'automatique': False,  'virement': False, 'num_cheque': '', 'moyen_id': 10, 'compte_id': 4, 'date': datetime.date(2012, 9, 24), 'titre_id': 3, 'notes': u'5@1', 'cat_id':64, 'ib_id': None},
            {'ope_titre': False, 'pointe': False, 'montant': Decimal('99.00'), 'date_val': None, 'tiers_id': 258, 'ligne': 10, 'rapp_id': None, 'automatique': False,  'virement': False, 'num_cheque': '', 'moyen_id': 8, 'compte_id': 1, 'date': datetime.date(2012, 9, 24), 'notes': '', 'cat_id': 74, 'ib_id': None},
            {'ope_titre': False, 'pointe': False, 'montant': Decimal('1.00'), 'date_val': None, 'tiers_id': 258, 'ligne': 11, 'rapp_id': None, 'automatique': False,  'virement': False, 'num_cheque': '', 'moyen_id': 8, 'compte_id': 1, 'date': datetime.date(2012, 9, 24), 'notes': '', 'cat_id': 75, 'ib_id': None},
            {'ope_titre': False, 'pointe': False, 'montant': Decimal('-100.00'), 'date_val': None, 'tiers_id': 260, 'ligne': 12, 'dest_id': 3, 'rapp_id': None, 'automatique': False,  'virement': True, 'num_cheque': '', 'moyen_id': 5, 'compte_id': 1, 'date': datetime.date(2012, 12, 18), 'notes': u'>Rcpte1201101', 'cat_id': 65, 'ib_id': None},
            {'ope_titre': False, 'pointe': False, 'montant': Decimal('-100.00'), 'date_val': None, 'tiers_id': 260, 'ligne': 13, 'dest_id': 3, 'rapp_id': None, 'automatique': False,  'virement': True, 'num_cheque': '', 'moyen_id': 5, 'compte_id': 1, 'date': datetime.date(2013, 12, 18), 'notes': u'>P', 'cat_id': 65, 'ib_id': None}
        ]
        self.assertEqual(attendu,cl.opes.created_items)

@override_settings(CONVERSION_CPT_TITRE=True)
class Test_import_csv2(Test_import_abstract):

    def test_import_csv_simple_ok_global(self):
        """test d'integration"""
        with open(os.path.join(settings.PROJECT_PATH, "gsb", "test_files", "test_import_export.csv")) as file_test:
            r = self.client.post(reverse('import_csv_ope_simple'), {'nom_du_fichier': file_test})
            # on efface les fichier crée par le test
            for name in glob.glob(os.path.join(settings.PROJECT_PATH, 'upload', 'import_simple*')): 
                os.remove(name)
        self.assertEqual(r.status_code, 302)
        self.assertQueryset_list(models.Tiers.objects.all(),
                                 [u'tiers1', u'tiers2', u'cpte1 => cptb3', u'titre_ autre', u'secu', u'titre_ t1', u'titre_ t2'],
                                 'nom')  # ne pas oublier le tiers cree automatiquement
        self.assertEquals(models.Ope.objects.all().count(), 16)
        self.assertQueryset_list(models.Cat.objects.all(),
                                 [u'cat1', u'cat2',
                                  u'Frais bancaires', u"Opération Ventilée", u"Opération sur titre",
                                  u"Revenus de placements:Plus-values", u'Impôts',
                                  u'Revenus de placements:interets', u'Virement', u"Non affecté", u"Avance", u"Remboursement"],
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
        """verification des property"""
        prop = import_base.Property_ope_base()
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
        """test de l'exception sans rien de special"""
        with self.assertRaises(import_base.ImportException) as exc:
            raise import_base.ImportException('test')
        self.assertEqual(exc.exception.msg, 'test')
        self.assertEqual("%s" % exc.exception, 'test')

    def test_cat_cache(self):
        """on teste si les categories par defaut sont bien crees"""
        import_base.Cat_cache(self.request_get("/outils"))
        self.assertEqual(models.Cat.objects.get(nom=u"Opération sur titre").id, 64)
        self.assertEqual(models.Cat.objects.get(nom="Revenus de placements:Plus-values").id, 67)
        self.assertEqual(models.Cat.objects.get(nom="Revenus de placements:interets").id, 68)
        self.assertEqual(models.Cat.objects.get(nom=u'Impôts').id, 54)
        self.assertEqual(models.Cat.objects.get(nom=u'Virement').id, 65)
        self.assertEqual(models.Cat.objects.get(nom=u"Opération Ventilée").id, 69)
        self.assertEqual(models.Cat.objects.get(nom=u"Frais bancaires").id, 70)
        self.assertEqual(models.Cat.objects.get(nom=u"Non affecté").id, 71)

    def test_cat_cache2(self):
        """test avec definition de l'ensemble avec nom defini"""
        cats = import_base.Cat_cache(self.request_get("/outils"))
        self.assertEqual(cats.goc('test', {'nom': 'test', 'id': 1215, 'type': 'd'}), 1215)

    def test_cat_cache2bis(self):
        """# test avec definition de l'ensemble sans nom defini"""
        cats = import_base.Cat_cache(self.request_get("/outils"))
        self.assertEqual(cats.goc('', {'nom': 'test', 'id': 1215, 'type': 'd'}), 1215)

    def test_cat_cache3(self):
        """test normal"""
        cats = import_base.Cat_cache(self.request_get("/outils"))
        cats.goc("cat1")  # on cree
        self.assertEqual(cats.goc("cat1"), models.Cat.objects.get(nom=u"cat1").id)  # on demande

    def test_cat_cache4(self):
        """test integrity error"""
        cats = import_base.Cat_cache(self.request_get("/outils"))
        cats.goc('test', {'nom': 'test', 'id': 1215, 'type': 'd'})
        with self.assertRaises(import_base.ImportException):
            cats.goc('test2', {'nom': 'test2', 'id': 1215, 'type': 'd'})
        del cats.id['test']
        with self.assertRaises(import_base.ImportException):
            cats.goc('test', {'nom': 'test', 'id': 1215, 'type': 'c'})
        with self.assertRaises(KeyError):
            _=cats.id['test']
        with self.assertRaises(import_base.ImportException):
            cats.goc('test', {'nom': 'test', 'id': 1216, 'type': 'c'})

    def test_cat_cache5(self):
        """test creation et readonly"""
        cats = import_base.Cat_cache(self.request_get("/outils"))
        cats.readonly = True
        with self.assertRaises(import_base.ImportException) as exc:
            cats.goc("cat1")
        self.assertEqual(exc.exception.msg, u"Cat 'cat1' non créée parce que c'est read only")

    def test_cat_cache6(self):
        """on teste si on peut bien recuperer une cat deja existante"""
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
        self.assertEqual(moyens.goc("moyen1", montant=10), 7)

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
        self.assertEqual(moyens.goc("test", montant=-10), 7)
        m = models.Moyen.objects.get(id=7)
        self.assertEqual(m.nom, 'test')
        self.assertEqual(m.type, 'd')

    def test_moyen_cache5(self):
        """test d'un nouveau moyen avec un montant >0"""
        moyens = import_base.Moyen_cache(self.request_get("/outils"))
        self.assertEqual(moyens.goc("test", montant=10), 7)
        m = models.Moyen.objects.get(id=7)
        self.assertEqual(m.nom, 'test')
        self.assertEqual(m.type, 'r')

    def test_moyen_cache5bis(self):
        """test d'un nouveau moyen avec un montant par defaut"""
        moyens = import_base.Moyen_cache(self.request_get("/outils"))
        self.assertEqual(moyens.goc("test"), 7)
        m = models.Moyen.objects.get(id=7)
        self.assertEqual(m.nom, 'test')
        self.assertEqual(m.type, 'd')

    def test_moyen_cache7(self):
        cache = import_base.Moyen_cache(self.request_get("/outils"))
        self.assertEqual(cache.goc(obj={'nom': 't', 'type':'d', 'id': 255}), 255)

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
        cache = import_base.Exercice_cache(self.request_get('url_exemple'))
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
        cache = import_base.Titre_cache(self.request_get('url_exemple'))
        self.assertEqual(cache.goc("titre1"), 1)
        # on regarde si il existe effectivement
        m = models.Titre.objects.get(id=1)
        self.assertEqual(m.nom, 'titre1')
        self.assertEqual(m.type, 'ZZZ')
        self.assertEqual(m.isin, "ZZ_1")
        # on essaye de le rappeller
        self.assertEqual(cache.goc("titre1"), 1)

    def test_titre_cache_obj(self):
        """on essaye avec les objects"""
        cache = import_base.Titre_cache(self.request_get('url_exemple'))
        self.assertEqual(cache.goc('titre3', obj={"nom": 'titre3', "isin": 'ceci est un isin', "type": "ZZZ", 'id': 23553}), 23553)
        m = models.Titre.objects.get(id=23553)
        self.assertEqual(m.nom, 'titre3')
        with self.assertRaises(import_base.ImportException):
            cache.goc("titre4", obj={"nom": 'titre4', "isin": 'ceci est un isin', "type": "ZZZ", 'id': 23553})

    def test_titre_cache2(self):
        """essai de creer un titre alors qu'on est en read only"""
        cache = import_base.Titre_cache(self.request_get('url_exemple'))
        cache.readonly = True
        with self.assertRaises(import_base.ImportException):
            cache.goc("titre1")

    def test_cours_cache(self):
        # version avec nom titre
        titres = import_base.Titre_cache(self.request_get('url_exemple'))
        cache = import_base.Cours_cache(self.request_get('url_exemple'), titres)
        self.assertEqual(cache.goc("titre1", utils.strpdate("2011-01-01"), 150), 1)
        self.assertEqual(titres.goc("titre1"), 1)
        m = models.Cours.objects.get(id=1)
        self.assertEqual(m.valeur, 150)
        self.assertEqual(m.titre.nom, "titre1")
        self.assertEqual(m.date, utils.strpdate("2011-01-01"))
        self.assertEqual(cache.goc("titre1", utils.strpdate("2011-01-01"), 150), 1)

    def test_cours_cache3(self):
        # meme date, cours different
        titres = import_base.Titre_cache(self.request_get('url_exemple'))
        cache = import_base.Cours_cache(self.request_get('url_exemple'), titres)
        cache.goc("titre1", utils.strpdate("2011-01-01"), 150)
        del cache.id[1]
        with self.assertRaises(import_base.ImportException):
            cache.goc("titre1", utils.strpdate("2011-01-01"), 200)

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
        models.Compte.objects.create(nom="sansrien_init")
        moyens = import_base.Moyen_cache(self.request_get("/outils"))
        # on cree les deux comptes utiles
        models.Compte.objects.create(nom="sansrien")
        models.Compte.objects.create(nom="les2", moyen_credit_defaut_id=moyens.goc("uniquement_credit", montant=10),
                                     moyen_debit_defaut_id=moyens.goc("uniquement_debit", montant=-10))
        cache = import_base.Moyen_defaut_cache()
        self.assertEqual(cache.goc("sansrien", 10), settings.MD_CREDIT)
        self.assertEqual(cache.goc("sansrien", -10), settings.MD_DEBIT)
        self.assertEqual(cache.goc("les2", 10), 7)
        self.assertEqual(cache.goc("les2", -10), 8)
        self.assertEqual(cache.goc("test", 10), settings.MD_CREDIT)
        self.assertEqual(cache.goc("test", -10), settings.MD_DEBIT)
    def test_ope_cache(self):
        opes = import_base.Ope_cache(self.request_get("/outils"))
        opes.create("opes")
        self.assertEqual(opes.created_items,["opes",])
        self.assertEqual(opes.nb_created,1)
