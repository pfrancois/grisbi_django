# -*- coding: utf-8 -*
"""
test import
"""

from django.test.utils import override_settings
from django.conf import settings

import os.path
import datetime
import django.utils.timezone as tz

from gsb.io import lecture_plist
from gsb import models

from .test_imports_csv import Test_import_abstract
from gsb.io.lecture_plist import Lecture_plist_exception
from gsb.io.ecriture_plist_money_journal import Export_icompta_plist
import mock
from testfixtures import compare
import collections


class Test_element(Test_import_abstract):

    def test_ope(self):
        fich = os.path.join(settings.PROJECT_PATH, "gsb", "test_files", "import_plist", 'Applications', 'Money Journal',
                            'log', "1402954705000.log")
        ele = lecture_plist.collection_datas_decodes(fich)
        self.compare(ele.datemaj, datetime.datetime(2014, 6, 16, 21, 38, 25, tzinfo=tz.utc))
        el = ele.list_el[0]
        self.compare(el.device, 'MyHpyVfqnK')
        self.compare(el.action, 'c')
        self.compare(el.sens_element, 'd')
        self.compare(el.is_ope, True)
        self.compare(el.is_cat, False)
        self.compare(el.is_compte, False)
        self.compare(el.is_budget, False)
        self.compare(el.lastup, datetime.datetime(2014, 6, 16, 21, 38, 25, tzinfo=tz.utc))
        self.compare(el.id, 66)
        self.compare(el.cat, 1)
        self.compare(el.automatique, False)
        self.compare(el.date, datetime.date(2014, 6, 16))
        self.compare(el.montant, -10.25)
        self.compare(el.tiers, 'Ope standart')
        self.compare(el.__str__(), "(66) le 16/06/2014 : -10.25 EUR tiers: Ope standart cpt: 1")
        ele = lecture_plist.collection_datas_decodes(
            os.path.join(settings.PROJECT_PATH, "gsb", "test_files", "import_plist", 'Applications', 'Money Journal',
                         'log', "1403036267000.log"))
        self.compare(ele.datemaj, datetime.datetime(2014, 6, 17, 20, 17, 47, tzinfo=tz.utc))
        el = ele.list_el[0]
        self.compare(el.device, 'MyHpyVfqnK')
        self.compare(el.action, 'm')
        self.compare(el.sens_element, 'd')
        self.compare(el.is_ope, True)
        self.compare(el.is_cat, False)
        self.compare(el.is_compte, False)
        self.compare(el.is_budget, False)
        self.compare(el.lastup, datetime.datetime(2014, 6, 17, 20, 17, 47, 95470, tzinfo=tz.utc))
        self.compare(el.id, 66)
        self.compare(el.cat, 1)
        self.compare(el.automatique, False)
        self.compare(el.date, datetime.date(2014, 6, 16))
        self.compare(el.montant, -55)
        self.compare(el.tiers, 'Ope standart')
        ele = lecture_plist.collection_datas_decodes(
            os.path.join(settings.PROJECT_PATH, "gsb", "test_files", "import_plist", 'Applications', 'Money Journal',
                         'log', "1403037219000.log"))
        self.compare(ele.datemaj, datetime.datetime(2014, 6, 17, 20, 33, 39, tzinfo=tz.utc))
        el = ele.list_el[0]
        self.compare(el.device, 'MyHpyVfqnK')
        self.compare(el.action, 'd')
        self.compare(el.sens_element, 'd')
        self.compare(el.is_ope, True)
        self.compare(el.is_cat, False)
        self.compare(el.is_compte, False)
        self.compare(el.is_budget, False)
        self.compare(el.lastup, datetime.datetime(2014, 6, 17, 20, 17, 47, 95470, tzinfo=tz.utc))
        self.compare(el.id, 66)
        self.compare(el.cat, 1)
        self.compare(el.automatique, False)
        self.compare(el.date, datetime.date(2014, 6, 16))
        self.compare(el.montant, -55)
        self.compare(el.tiers, 'Ope standart')

    def test_compte(self):
        el = lecture_plist.collection_datas_decodes(
            os.path.join(settings.PROJECT_PATH, "gsb", "test_files", "import_plist", 'Applications', 'Money Journal',
                         'log', "1403040634000.log")).list_el[0]
        self.compare(el.device, 'MyHpyVfqnK')
        self.compare(el.datemaj, datetime.datetime(2014, 6, 17, 21, 30, 34, tzinfo=tz.utc))
        self.compare(el.action, 'c')
        self.compare(el.is_ope, False)
        self.compare(el.is_cat, False)
        self.compare(el.is_compte, True)
        self.compare(el.is_budget, False)
        self.compare(el.lastup, datetime.datetime(2014, 6, 17, 21, 30, 34, tzinfo=tz.utc))
        self.compare(el.id, 7)
        self.compare(el.couleur, "#000000")
        self.compare(el.nom, " ")
        el = lecture_plist.collection_datas_decodes(
            os.path.join(settings.PROJECT_PATH, "gsb", "test_files", "import_plist", 'Applications', 'Money Journal',
                         'log', "1403040635000.log")).list_el[0]
        self.compare(el.device, 'MyHpyVfqnK')
        self.compare(el.datemaj, datetime.datetime(2014, 6, 17, 21, 30, 35, tzinfo=tz.utc))
        self.compare(el.action, 'm')
        self.compare(el.is_ope, False)
        self.compare(el.is_cat, False)
        self.compare(el.is_compte, True)
        self.compare(el.is_budget, False)
        self.compare(el.lastup, datetime.datetime(2014, 6, 17, 21, 30, 34, 88255, tzinfo=tz.utc))
        self.compare(el.id, 7)
        self.compare(el.couleur, '#000000')
        self.compare(el.nom, "Ghh")
        self.compare(el.__str__(), "(7) 'Ghh'")
        el = lecture_plist.collection_datas_decodes(
            os.path.join(settings.PROJECT_PATH, "gsb", "test_files", "import_plist", 'Applications', 'Money Journal',
                         'log', "1403045414000.log")).list_el[0]
        self.compare(el.device, 'MyHpyVfqnK')
        self.compare(el.datemaj, datetime.datetime(2014, 6, 17, 22, 50, 14, tzinfo=tz.utc))
        self.compare(el.action, 'd')
        self.compare(el.is_ope, False)
        self.compare(el.is_cat, False)
        self.compare(el.is_compte, True)
        self.compare(el.is_budget, False)
        self.compare(el.lastup, datetime.datetime(2014, 6, 17, 21, 30, 34, 88255, tzinfo=tz.utc))
        self.compare(el.id, 7)
        self.compare(el.couleur, "#000000")
        self.compare(el.nom, "Ghh")

    def test_element_cat(self):
        el = lecture_plist.collection_datas_decodes(
            os.path.join(settings.PROJECT_PATH, "gsb", "test_files", "import_plist", 'Applications', 'Money Journal',
                         'log', "1403049014000.log")).list_el[0]
        self.compare(el.device, 'MyHpyVfqnK')
        self.compare(el.datemaj, datetime.datetime(2014, 6, 17, 23, 50, 14, tzinfo=tz.utc))
        self.compare(el.action, 'c')
        self.compare(el.is_ope, False)
        self.compare(el.is_cat, True)
        self.compare(el.is_compte, False)
        self.compare(el.is_budget, False)
        self.compare(el.lastup, datetime.datetime(2014, 6, 17, 23, 50, 14, tzinfo=tz.utc))
        self.compare(el.id, 16)
        self.compare(el.couleur, '#000000')
        self.compare(el.nom, " ")
        self.compare(el.type_cat, "d")
        el = lecture_plist.collection_datas_decodes(
            os.path.join(settings.PROJECT_PATH, "gsb", "test_files", "import_plist", 'Applications', 'Money Journal',
                         'log', "1403049014010.log")).list_el[0]
        self.compare(el.device, 'MyHpyVfqnK')
        self.compare(el.datemaj, datetime.datetime(2014, 6, 17, 23, 50, 14, 10000, tzinfo=tz.utc))
        self.compare(el.action, 'm')
        self.compare(el.is_ope, False)
        self.compare(el.is_cat, True)
        self.compare(el.is_compte, False)
        self.compare(el.is_budget, False)
        self.compare(el.lastup, datetime.datetime(2014, 6, 17, 23, 50, 14, 10000, tzinfo=tz.utc))
        self.compare(el.id, 16)
        self.compare(el.couleur, '#000000')
        self.compare(el.nom, "Cat aded")
        self.compare(el.type_cat, "d")
        self.compare(el.__str__(), "(16) 'Cat aded' type:d")
        el = lecture_plist.collection_datas_decodes(
            os.path.join(settings.PROJECT_PATH, "gsb", "test_files", "import_plist", 'Applications', 'Money Journal',
                         'log', "1403049014020.log")).list_el[0]
        self.compare(el.device, 'MyHpyVfqnK')
        self.compare(el.datemaj,  datetime.datetime(2014, 6, 17, 23, 50, 14, 20000, tzinfo=tz.utc))
        self.compare(el.action, 'd')
        self.compare(el.is_ope, False)
        self.compare(el.is_cat, True)
        self.compare(el.is_compte, False)
        self.compare(el.is_budget, False)
        self.compare(el.lastup,  datetime.datetime(2014, 6, 17, 23, 50, 14, 10000, tzinfo=tz.utc))
        self.compare(el.id, 16)
        self.compare(el.couleur, '#000000')
        self.compare(el.nom, "Cat aded")
        self.compare(el.type_cat, "d")


class Test_check(Test_import_abstract):

    @override_settings(DIR_DROPBOX=os.path.join(settings.PROJECT_PATH, "gsb", "test_files", "import_plist"))
    def test_element_check(self):
        self.compare(lecture_plist.check(), True)  # TODO improve it


class Test_import_item_first_part(Test_import_abstract):

    def setUp(self):
        self.request = self.request_get('outils')
        self.lastmaj = datetime.datetime(2014, 6, 15, 00, 25, 14, tzinfo=tz.utc)

    @override_settings(DIR_DROPBOX=os.path.join(settings.PROJECT_PATH, "gsb", "test_files", "import_plist"))
    def test_element_import(self):
        """normalement il n'y a aucune operation"""
        self.lastmaj = datetime.datetime(2014, 6, 20, 00, 25, 14, tzinfo=tz.utc)
        self.compare(sorted(lecture_plist.import_items(lastmaj=self.lastmaj, request=self.request).most_common()), [('deja', 9)])

    @override_settings(DIR_DROPBOX=os.path.join(settings.PROJECT_PATH, "gsb", "test_files", "import_plist"))
    def test_element_import2(self):
        """avec crea, modif et del de chaque type"""
        self.compare(sorted(lecture_plist.import_items(lastmaj=self.lastmaj, request=self.request).most_common()),
                     [('categorie', 0), ('compte', 0), ('ope', 0)])

    @override_settings(DIR_DROPBOX=os.path.join(settings.PROJECT_PATH, "gsb", "test_files", "import_plist_2"))
    def test_element_import3(self):
        """avec crea, modif de cat et compte"""
        self.compare(sorted(lecture_plist.import_items(lastmaj=self.lastmaj, request=self.request).most_common()),
                     [('categorie', 1), ('compte', 1)])
        self.assertmessagecontains(self.request, "catégorie (16) 'Cat aded' type:d créée")
        self.assertmessagecontains(self.request, "compte (7) 'Ghh' créé")


class Test_item_modif_effectives_cote_cat(Test_import_abstract):

    def setUp(self):
        self.request = self.request_get('outils')
        self.lastmaj = datetime.datetime(2014, 6, 15, 00, 25, 14, tzinfo=tz.utc)
        self.cat = models.Cat.objects.create(pk=16, nom="Cat aded", type="d", couleur=0)

    @override_settings(DIR_DROPBOX=os.path.join(settings.PROJECT_PATH, "gsb", "test_files", "import_plist_3"))
    def test_element_import4(self):
        """teste modification standart"""
        self.cpt = models.Compte.objects.create(pk=7, nom='hjhjhkh', couleur='#FFFFFF')
        self.cat.nom = "Cat initial"
        self.cat.type = 'r'
        self.cat.couleur = '#FFFFFF'
        self.cat.save()
        self.compare(sorted(lecture_plist.import_items(lastmaj=self.lastmaj, request=self.request).most_common()),
                     [('categorie', 1), ('compte', 1)])
        self.assertmessagecontains(self.request,
                                   "catégorie (16) 'Cat aded' type:d modifiée comme ca: nom: Cat initial => Cat aded, couleur: #FFFFFF => #000000, type: r => d")
        self.assertmessagecontains(self.request,
                                   "compte (7) 'Ghh' modifié comme ca: nom: hjhjhkh => Ghh, couleur: #FFFFFF => #000000")
        cat = models.Cat.objects.get(pk=16)
        self.compare(cat.nom, 'Cat aded')
        self.compare(cat.couleur, '#000000')
        self.compare(cat.type, 'd')
        obj = models.Compte.objects.get(pk=7)
        self.compare(obj.nom, 'Ghh')

    @override_settings(DIR_DROPBOX=os.path.join(settings.PROJECT_PATH, "gsb", "test_files", "import_plist_5"))
    def test_element_import6(self):
        """ttest si cat deja cree"""
        with self.assertRaises(Lecture_plist_exception) as exception_context_manager:
            lecture_plist.import_items(lastmaj=self.lastmaj, request=self.request)
        self.compare(exception_context_manager.exception.args,
                     ("attention la catégorie (16) 'Cat aded' type:d existe déja alors qu'on demande de la créer", ))

    @override_settings(DIR_DROPBOX=os.path.join(settings.PROJECT_PATH, "gsb", "test_files", "import_plist_6"))
    def test_element_import7(self):
        """ttest si modif alors que cat pas cree"""
        with self.assertRaises(Lecture_plist_exception) as exception_context_manager:
            lecture_plist.import_items(lastmaj=self.lastmaj, request=self.request)
        self.compare(exception_context_manager.exception.args, (
            "attention la catégorie (1111) 'Cat aded' type:d n'existe pas alors qu'on demande de la modifier", ))

    @override_settings(DIR_DROPBOX=os.path.join(settings.PROJECT_PATH, "gsb", "test_files", "import_plist_8"))
    @override_settings(ID_CAT_OST=2)
    def test_element_import8(self):
        """ttest si modif alors que cat par defaut"""
        models.Cat.objects.create(pk=2, nom="Cat ost", type="r", couleur='#FFFFFF')
        lecture_plist.import_items(lastmaj=self.lastmaj, request=self.request)
        self.assertmessagecontains(self.request, "impossible de modifier la cat (2) 'Cat aded' type:d")

    @override_settings(DIR_DROPBOX=os.path.join(settings.PROJECT_PATH, "gsb", "test_files", "import_plist_9"))
    def test_element_import9(self):
        """ttest si modif cat avec le nom deja cree"""
        self.cat.type = 'r'
        self.cat.couleur = '#FFFFFF'
        self.cat.save()
        lecture_plist.import_items(lastmaj=self.lastmaj, request=self.request)
        self.assertmessagecontains(self.request,
                                   "catégorie (16) 'Cat aded' type:d modifiée comme ca: couleur: #FFFFFF => #000000, type: r => d")

    @override_settings(DIR_DROPBOX=os.path.join(settings.PROJECT_PATH, "gsb", "test_files", "import_plist_10"))
    def test_element_import10(self):
        """ttest si suppr alors que cat pas cree"""
        self.cat.delete()
        with self.assertRaises(Lecture_plist_exception) as exception_context_manager:
            lecture_plist.import_items(lastmaj=self.lastmaj, request=self.request)
        self.compare(exception_context_manager.exception.args, (
            "attention la catégorie (16) 'Cat aded' type:d n'existe pas alors qu'on demande de la supprimer", ))

    @override_settings(DIR_DROPBOX=os.path.join(settings.PROJECT_PATH, "gsb", "test_files", "import_plist_11"))
    def test_element_import11(self):
        """ttest si suppr alors que cat deja utilise ds ope"""
        self.cpt = models.Compte.objects.create(pk=7, nom='Ghh', couleur=0)
        self.moyen = models.Moyen.objects.create(id=settings.MD_CREDIT, nom="dd", type="r")
        self.ope = models.Ope.objects.create(compte=self.cpt, date=datetime.date(2014, 6, 15), montant=250, tiers=models.Tiers.objects.get_or_create(nom="tiers", defaults={'nom': "tiers"})[0], cat=self.cat, moyen=self.moyen)
        with self.assertRaises(Lecture_plist_exception) as exception_context_manager:
            lecture_plist.import_items(lastmaj=self.lastmaj, request=self.request)
        self.compare(("catégorie non supprimable (16) 'Cat aded' type:d car elle a des opérations rattachées", ),
                     exception_context_manager.exception.args)

    @override_settings(DIR_DROPBOX=os.path.join(settings.PROJECT_PATH, "gsb", "test_files", "import_plist_12"))
    @override_settings(ID_CAT_OST=2)
    def test_element_import12(self):
        """tente de supprimer une categorie par defaut"""
        models.Cat.objects.create(pk=2, nom="Cat ost", type="r", couleur='#FFFFFF')
        with self.assertRaises(Lecture_plist_exception) as exception_context_manager:
            lecture_plist.import_items(lastmaj=self.lastmaj, request=self.request)
        self.compare(("impossible de supprimer la catégorie (2)", ), exception_context_manager.exception.args)

    @override_settings(DIR_DROPBOX=os.path.join(settings.PROJECT_PATH, "gsb", "test_files", "import_plist_12_1"))
    def test_element_import12_1(self):
        """ttest suprr d'une cat"""
        lecture_plist.import_items(lastmaj=self.lastmaj, request=self.request)
        self.assertmessagecontains(self.request, "catégorie (Cat aded) #16 supprimée")


class Test_import_item_modif_effectives_cote_compte(Test_import_abstract):

    def setUp(self):
        self.request = self.request_get('outils')
        self.lastmaj = datetime.datetime(2014, 6, 15, 00, 25, 14, tzinfo=tz.utc)
        self.cpt = models.Compte.objects.create(pk=7, nom='hjhjhkh', couleur=0)

    @override_settings(DIR_DROPBOX=os.path.join(settings.PROJECT_PATH, "gsb", "test_files", "import_plist_4"))
    def test_element_import5(self):
        """exception si compte deja cree"""
        with self.assertRaises(Lecture_plist_exception) as exception_context_manager:
            lecture_plist.import_items(lastmaj=self.lastmaj, request=self.request)
        self.compare(exception_context_manager.exception.args,
                     ("attention le compte (7) 'Ghh' existe déja alors qu'on demande de le créer", ))

    @override_settings(DIR_DROPBOX=os.path.join(settings.PROJECT_PATH, "gsb", "test_files", "import_plist_13"))
    def test_element_import13(self):
        """ttest si modif compte avec le nom deja cree"""
        self.cpt.couleur = "#FFFFFF"
        self.cpt.save()
        lecture_plist.import_items(lastmaj=self.lastmaj, request=self.request)
        self.assertmessagecontains(self.request, "compte (7) 'hjhjhkh' modifié comme ca: couleur: #FFFFFF => #000000")

    @override_settings(DIR_DROPBOX=os.path.join(settings.PROJECT_PATH, "gsb", "test_files", "import_plist_14"))
    def test_element_import14(self):
        """ttest si suppr alors que compte pas cree"""
        self.cpt.delete()
        with self.assertRaises(Lecture_plist_exception) as exception_context_manager:
            lecture_plist.import_items(lastmaj=self.lastmaj, request=self.request)
        self.compare(exception_context_manager.exception.args, (
            "attention le compte 7 n'existe pas pour ce nom (hjhjhkh) alors qu'on demande de le supprimer", ))

    @override_settings(DIR_DROPBOX=os.path.join(settings.PROJECT_PATH, "gsb", "test_files", "import_plist_15"))
    def test_element_import15(self):
        """ttest si suppr alors que compte deja utilise ds ope"""
        cat = models.Cat.objects.create(pk=16, nom="Cat aded", type="r", couleur='#FFFFFF')
        moyen = models.Moyen.objects.create(id=settings.MD_CREDIT, nom="dd", type="r")
        models.Ope.objects.create(compte=self.cpt, date=datetime.date(2014, 6, 15), montant=250,
                                  tiers=models.Tiers.objects.get_or_create(nom="tiers", defaults={'nom': "tiers"})[0],
                                  cat=cat, moyen=moyen)
        with self.assertRaises(Lecture_plist_exception) as exception_context_manager:
            lecture_plist.import_items(lastmaj=self.lastmaj, request=self.request)
        self.compare(exception_context_manager.exception.args,
                     ("compte non supprimable (7) 'hjhjhkh' car il a des opérations ou des écheances rattachées", ))

    @override_settings(DIR_DROPBOX=os.path.join(settings.PROJECT_PATH, "gsb", "test_files", "import_plist_16"))
    def test_element_import16(self):
        """ttest suppr d'un compte"""
        lecture_plist.import_items(lastmaj=self.lastmaj, request=self.request)
        self.assertmessagecontains(self.request, "compte (7) 'hjhjhkh' supprimé")


class Test_import_item_modif_effectives_cote_ope(Test_import_abstract):

    def setUp(self):
        self.request = self.request_get('outils')
        self.lastmaj = datetime.datetime(2014, 6, 15, 00, 25, 14, tzinfo=tz.utc)
        self.cat = models.Cat.objects.create(pk=1, nom="Cat aded", type="d", couleur=0)
        self.cat2 = models.Cat.objects.create(pk=2, nom="Cat aded2", type="d", couleur=0)
        self.cpt = models.Compte.objects.create(pk=1, nom='Ghh', couleur=0)
        self.cpt2 = models.Compte.objects.create(pk=2, nom='Ghh2', couleur=0)
        self.moyen_credit = models.Moyen.objects.create(id=settings.MD_CREDIT, nom="rr", type="r")
        self.moyen_debit = models.Moyen.objects.create(id=settings.MD_DEBIT, nom="dd", type="d")
        self.tiers = models.Tiers.objects.get_or_create(nom="Ope standart", defaults={'nom': "Ope standart"})[0]
        self.tiers2 = models.Tiers.objects.get_or_create(nom="tiers2", defaults={'nom': "tiers2"})[0]
        self.ope = models.Ope.objects.create(pk=66, compte=self.cpt2, date=datetime.date(2013, 6, 15), montant=25, tiers=self.tiers2,
                                             cat=self.cat2, moyen=self.moyen_credit)

    @override_settings(DIR_DROPBOX=os.path.join(settings.PROJECT_PATH, "gsb", "test_files", "import_plist_17"))
    def test_element_import17(self):
        """si un compte pour une ope n'existe pas"""
        self.ope.delete()
        self.cpt.delete()
        with self.assertRaises(Lecture_plist_exception) as exception_context_manager:
            lecture_plist.import_items(lastmaj=self.lastmaj, request=self.request)
        self.compare(exception_context_manager.exception.args, (
            "attention le compte (1) n'existe pas alors qu'on le demande pour l'opération (66) le 16/06/2014 : -10.25 EUR tiers: Ope standart cpt: 1", ))

    @override_settings(DIR_DROPBOX=os.path.join(settings.PROJECT_PATH, "gsb", "test_files", "import_plist_18"))
    def test_element_import18(self):
        """si une categorie pour une ope n'existe pas"""
        self.ope.delete()
        self.cat.delete()
        with self.assertRaises(Lecture_plist_exception) as exception_context_manager:
            lecture_plist.import_items(lastmaj=self.lastmaj, request=self.request)
        self.compare(exception_context_manager.exception.args, (
            "attention la catégorie (1) n'existe pas alors qu'on le demande pour l'opération (66) le 16/06/2014 : -10.25 EUR tiers: Ope standart cpt: 1", ))

    @override_settings(DIR_DROPBOX=os.path.join(settings.PROJECT_PATH, "gsb", "test_files", "import_plist_19"))
    def test_element_import19(self):
        """si une ope existe deja"""
        with self.assertRaises(Lecture_plist_exception) as exception_context_manager:
            lecture_plist.import_items(lastmaj=self.lastmaj, request=self.request)
        self.compare(exception_context_manager.exception.args, (
            "attention l'opération (66) le 16/06/2014 : -10.25 EUR tiers: Ope standart cpt: 1 existe déja alors qu'on demande de la créer", ))

    @override_settings(DIR_DROPBOX=os.path.join(settings.PROJECT_PATH, "gsb", "test_files", "import_plist_20"))
    def test_element_import20(self):
        """test ope cree sans probleme"""
        self.ope.delete()
        self.tiers.delete()
        lecture_plist.import_items(lastmaj=self.lastmaj, request=self.request)
        self.assertmessagecontains(self.request, "tiers 'Ope standart' créé")
        self.assertEqual(str(models.Ope.objects.get(id=66)),
                         "(66) le 16/06/2014 : -10.25 EUR tiers: Ope standart cpt: Ghh")

    @override_settings(DIR_DROPBOX=os.path.join(settings.PROJECT_PATH, "gsb", "test_files", "import_plist_21"))
    def test_element_import21(self):
        """test ope cree sans probleme"""
        self.ope.delete()
        self.cat.delete()
        self.cpt.delete()
        lecture_plist.import_items(lastmaj=self.lastmaj, request=self.request)
        self.assertEqual(str(models.Ope.objects.get(id=66)),
                         "(66) le 16/06/2014 : -10.25 EUR tiers: Ope standart cpt: hjhjhkh")

    @override_settings(DIR_DROPBOX=os.path.join(settings.PROJECT_PATH, "gsb", "test_files", "import_plist_22"))
    def test_element_import22(self):
        """test si ope a mofifier n'existe pas"""
        self.ope.delete()
        with self.assertRaises(Lecture_plist_exception) as exception_context_manager:
            lecture_plist.import_items(lastmaj=self.lastmaj, request=self.request)
        self.compare(exception_context_manager.exception.args, (
            "attention cette opération (66) le 16/06/2014 : -10.25 EUR tiers: Ope standart cpt: 1 n'existe pas alors qu'on demande de la modifier", ))

    @override_settings(DIR_DROPBOX=os.path.join(settings.PROJECT_PATH, "gsb", "test_files", "import_plist_23"))
    def test_element_import23(self):
        """test si ope mere"""
        fille = models.Ope.objects.create(pk=67, compte=self.cpt, date=datetime.date(2014, 6, 15), montant=-10.25, tiers=self.tiers,
                                          cat=self.cat, moyen=self.moyen_debit)
        fille.mere = self.ope
        fille.save()
        lecture_plist.import_items(lastmaj=self.lastmaj, request=self.request)
        self.assertmessagecontains(self.request,
                                   "impossible de modifier cette opération (66) le 16/06/2014 : -10.25 EUR tiers: Ope standart cpt: 1 car elle est mère")

    @override_settings(DIR_DROPBOX=os.path.join(settings.PROJECT_PATH, "gsb", "test_files", "import_plist_23"))
    def test_element_import24(self):
        """test si ope fille"""
        mere = models.Ope.objects.create(pk=67, compte=self.cpt, date=datetime.date(2014, 6, 15), montant=-10.25, tiers=self.tiers,
                                         cat=self.cat, moyen=self.moyen_debit)
        self.ope.mere = mere
        self.ope.save()
        lecture_plist.import_items(lastmaj=self.lastmaj, request=self.request)
        self.assertmessagecontains(self.request,
                                   "impossible de modifier cette opération (66) le 16/06/2014 : -10.25 EUR tiers: Ope standart cpt: 1 car elle est fille", )

    @override_settings(DIR_DROPBOX=os.path.join(settings.PROJECT_PATH, "gsb", "test_files", "import_plist_23"))
    def test_element_import25(self):
        """test si ope rapprochee"""
        rapp = models.Rapp.objects.create(nom="test_rapp")
        self.ope.rapp = rapp
        self.ope.save()
        lecture_plist.import_items(lastmaj=self.lastmaj, request=self.request)
        self.assertmessagecontains(self.request,
                                   "impossible de modifier cette opération (66) le 16/06/2014 : -10.25 EUR tiers: Ope standart cpt: 1 car elle est rapprochée", )

    @override_settings(DIR_DROPBOX=os.path.join(settings.PROJECT_PATH, "gsb", "test_files", "import_plist_23"))
    def test_element_import26(self):
        """test si ope avec compte ferme"""
        self.cpt2.ouvert = False
        self.cpt2.save()
        lecture_plist.import_items(lastmaj=self.lastmaj, request=self.request)
        self.assertmessagecontains(self.request,
                                   "impossible de modifier cette opération (66) le 16/06/2014 : -10.25 EUR tiers: Ope standart cpt: 1 car son compte est fermé", )

    @override_settings(DIR_DROPBOX=os.path.join(settings.PROJECT_PATH, "gsb", "test_files", "import_plist_23"))
    def testelement_import27(self):
        """test si ope jumelle"""
        jumelle = models.Ope.objects.create(pk=67, compte=self.cpt, date=datetime.date(2014, 6, 15), montant=10.25,
                                            tiers=self.tiers, cat=self.cat, moyen=self.moyen_credit)
        self.ope.jumelle = jumelle
        self.ope.save()
        lecture_plist.import_items(lastmaj=self.lastmaj, request=self.request)
        self.assertmessagecontains(self.request,
                                   "impossible de modifier cette opération (66) le 16/06/2014 : -10.25 EUR tiers: Ope standart cpt: 1 car elle est jumellée", )

    @override_settings(DIR_DROPBOX=os.path.join(settings.PROJECT_PATH, "gsb", "test_files", "import_plist_23"))
    def test_element_import28(self):
        """test si modif d'ope pointee"""
        self.ope.pointe = True
        self.ope.save()
        lecture_plist.import_items(lastmaj=self.lastmaj, request=self.request)
        self.assertmessagecontains(self.request,
                                   "impossible de modifier cette opération (66) le 16/06/2014 : -10.25 EUR tiers: Ope standart cpt: 1 car elle est pointée", )

    @override_settings(DIR_DROPBOX=os.path.join(settings.PROJECT_PATH, "gsb", "test_files", "import_plist_31"))
    def test_element_import31(self):
        """test si ope n'existe pas alors qu'elle va etre supprimer"""
        self.ope.delete()
        with self.assertRaises(Lecture_plist_exception) as exception_context_manager:
            lecture_plist.import_items(lastmaj=self.lastmaj, request=self.request)
        self.compare(exception_context_manager.exception.args,
                     ("attention cette opération 66 n'existe pas alors qu'on demande de la supprimer", ))

    @override_settings(DIR_DROPBOX=os.path.join(settings.PROJECT_PATH, "gsb", "test_files", "import_plist_31"))
    def test_element_import32(self):
        """test supprimeer une mere"""
        fille = models.Ope.objects.create(pk=67, compte=self.cpt, date=datetime.date(2014, 6, 15), montant=-10.25, tiers=self.tiers,
                                          cat=self.cat, moyen=self.moyen_debit)
        fille.mere = self.ope
        fille.save()
        with self.assertRaises(Lecture_plist_exception) as exception_context_manager:
            lecture_plist.import_items(lastmaj=self.lastmaj, request=self.request)
        self.compare(exception_context_manager.exception.args, (
            "impossible de supprimer cette opération (66) le 16/06/2014 : -10.25 EUR tiers: Ope standart cpt: 1 car elle est mère", ))

    @override_settings(DIR_DROPBOX=os.path.join(settings.PROJECT_PATH, "gsb", "test_files", "import_plist_31"))
    def test_element_import33(self):
        """test si ope fille"""
        mere = models.Ope.objects.create(pk=67, compte=self.cpt, date=datetime.date(2014, 6, 15), montant=-10.25, tiers=self.tiers,
                                         cat=self.cat, moyen=self.moyen_debit)
        self.ope.mere = mere
        self.ope.save()
        with self.assertRaises(Lecture_plist_exception) as exception_context_manager:
            lecture_plist.import_items(lastmaj=self.lastmaj, request=self.request)
        self.compare(exception_context_manager.exception.args, (
            "impossible de supprimer cette opération (66) le 16/06/2014 : -10.25 EUR tiers: Ope standart cpt: 1 car elle est fille", ))

    @override_settings(DIR_DROPBOX=os.path.join(settings.PROJECT_PATH, "gsb", "test_files", "import_plist_31"))
    def test_element_import34(self):
        """test si ope rapprochee"""
        rapp = models.Rapp.objects.create(nom="test_rapp")
        self.ope.rapp = rapp
        self.ope.save()
        with self.assertRaises(Lecture_plist_exception) as exception_context_manager:
            lecture_plist.import_items(lastmaj=self.lastmaj, request=self.request)
        self.compare(exception_context_manager.exception.args, (
            "impossible de supprimer cette opération (66) le 16/06/2014 : -10.25 EUR tiers: Ope standart cpt: 1 car elle est rapprochée", ))

    @override_settings(DIR_DROPBOX=os.path.join(settings.PROJECT_PATH, "gsb", "test_files", "import_plist_31"))
    def test_element_import35(self):
        """test si ope avec compte ferme"""
        self.cpt2.ouvert = False
        self.cpt2.save()
        with self.assertRaises(Lecture_plist_exception) as exception_context_manager:
            lecture_plist.import_items(lastmaj=self.lastmaj, request=self.request)
        self.compare(exception_context_manager.exception.args, (
            "impossible de supprimer cette opération (66) le 16/06/2014 : -10.25 EUR tiers: Ope standart cpt: 1 car son compte est fermé", ))

    @override_settings(DIR_DROPBOX=os.path.join(settings.PROJECT_PATH, "gsb", "test_files", "import_plist_31"))
    def test_element_import36(self):
        """test si ope jumelle"""
        jumelle = models.Ope.objects.create(pk=67, compte=self.cpt, date=datetime.date(2014, 6, 15), montant=10.25,
                                            tiers=self.tiers, cat=self.cat, moyen=self.moyen_credit)
        self.ope.jumelle = jumelle
        self.ope.save()
        with self.assertRaises(Lecture_plist_exception) as exception_context_manager:
            lecture_plist.import_items(lastmaj=self.lastmaj, request=self.request)
        self.compare(exception_context_manager.exception.args, (
            "impossible de supprimer cette opération (66) le 16/06/2014 : -10.25 EUR tiers: Ope standart cpt: 1 car elle est jumellée", ))

    @override_settings(DIR_DROPBOX=os.path.join(settings.PROJECT_PATH, "gsb", "test_files", "import_plist_31"))
    def test_element_import37(self):
        """test si modif d'ope pointee"""
        self.ope.pointe = True
        self.ope.save()
        with self.assertRaises(Lecture_plist_exception) as exception_context_manager:
            lecture_plist.import_items(lastmaj=self.lastmaj, request=self.request)
        self.compare(exception_context_manager.exception.args, (
            "impossible de supprimer cette opération (66) le 16/06/2014 : -10.25 EUR tiers: Ope standart cpt: 1 car elle est pointée", ))

    @override_settings(DIR_DROPBOX=os.path.join(settings.PROJECT_PATH, "gsb", "test_files", "import_plist_31"))
    def test_element_import38(self):
        """test si ope modifie sans probleme"""
        self.ope.delete()
        self.ope = models.Ope.objects.create(pk=66, compte=self.cpt, date=datetime.date(2014, 6, 16), montant=-10.25,
                                             tiers=self.tiers, cat=self.cat, moyen=self.moyen_debit)
        lecture_plist.import_items(lastmaj=self.lastmaj, request=self.request)
        self.assertmessagecontains(self.request,
                                   "opération (66) le 16/06/2014 : -10.25 EUR tiers: Ope standart cpt: 1 supprimée")

    @override_settings(DIR_DROPBOX=os.path.join(settings.PROJECT_PATH, "gsb", "test_files", "import_plist_31"))
    def test_element_import39(self):
        """test si ope modifie"""
        self.ope.delete()
        self.ope = models.Ope.objects.create(pk=66, compte=self.cpt, date=datetime.date(2014, 6, 15), montant=-10.25,
                                             tiers=self.tiers, cat=self.cat, moyen=self.moyen_debit)
        with self.assertRaises(Lecture_plist_exception) as exception_context_manager:
            lecture_plist.import_items(lastmaj=self.lastmaj, request=self.request)
        self.compare(exception_context_manager.exception.args, (
            "attention cette opération 66 existe alors qu'on demande de la supprimer mais elle est différente :\nDATE:\t2014-06-15!= 2014-06-16",))


@override_settings(CODE_DEVICE_POCKET_MONEY='totototo')
@override_settings(DIR_DROPBOX=os.path.join(settings.PROJECT_PATH, "gsb", "test_files", "export_plist"))
class Test_import_money_journal_export(Test_import_abstract):
    fixtures = ['test_money_journal.yaml', ]

    def setUp(self):
        self.request = self.request_get('outils')
        self.exp = Export_icompta_plist(request=self.request)
        directory = os.path.join(settings.PROJECT_PATH, "gsb", "test_files", "export_plist", 'Applications',
                                 'Money Journal', 'log')
        efface = list()
        for root, dirs, files in os.walk(directory, topdown=False):
            for name in files:
                efface.append(os.path.join(root, name))
                os.remove(os.path.join(root, name))
        for root, dirs, files in os.walk(directory, topdown=False):
            for name in dirs:
                efface.append(os.path.join(root, name))
                os.rmdir(os.path.join(root, name))

    def comp_file(self, filename, nom):

        attendu = os.path.join("export_plist_attendu", 'Applications', 'Money Journal', 'log', '140', '3', '4', filename)
        recu = os.path.join("export_plist", 'Applications', 'Money Journal', 'log', '140', '3', '4', filename)
        self.assert2filesequal(recu, attendu, nom=nom)

    def test_global(self):
            # on efface la table db_log
            models.Db_log.objects.all().delete()
            #cat modifie
            models.Db_log.objects.create(datamodel="cat", id_model=1, type_action="U", uuid="51a6674d-7f28-427b-8cf7-25ad2ac07901")
            #cat cree
            models.Db_log.objects.create(datamodel="cat", id_model=2, type_action="I", uuid="51a6674d-7f28-427b-8cf7-25ad2ac07902")
            models.Db_log.objects.create(datamodel="cat", id_model=72, type_action="I", uuid="51a0004d-7f28-427b-8cf7-44ad2ac07972")
            # c'est une modification d'une operation qui a ete efface (donc qui ne vas pas etre maj)
            models.Db_log.objects.create(datamodel="cat", id_model=35, type_action="I", uuid="51a0004d-7f28-427b-8cf7-44ad2ac07972")
            models.Cat.objects.filter(id=4).delete()  # la cat 4 a ete efface
            models.Db_log.objects.create(datamodel="cat", id_model=4, type_action="D", uuid="51a6674d-7f28-427b-8cf7-25ad2ac07a01")
            models.Compte.objects.filter(id=1).update(nom="compte_modifie")
            models.Compte.objects.create(id=3, nom="Compte nouveau")
            models.Db_log.objects.create(datamodel="compte", id_model=1, type_action="U", uuid="51a6674d-7f28-427b-8cf7-25ad2ac07a01")
            models.Db_log.objects.create(datamodel="compte", id_model=3, type_action="I", uuid="51a6674d-7f28-427b-8cf7-25ad2ac07a01")
            #on mock les opes
            models.Db_log.objects.create(datamodel="ope", id_model=1, type_action="U", uuid="51a6674d-7f28-427b-8cf7-25ad2ac07a01")
            models.Db_log.objects.create(datamodel="ope", id_model=2, type_action="U", uuid="51a6674d-7f28-427b-8cf7-25ad2ac07a02")
            models.Db_log.objects.create(datamodel="ope", id_model=3, type_action="U", uuid="51a6674d-7f28-427b-8cf7-25ad2ac07a03")
            models.Db_log.objects.create(datamodel="ope", id_model=8, type_action="U", uuid="51a6674d-7f28-427b-8cf7-25ad2ac07a08")
            models.Db_log.objects.create(datamodel="ope", id_model=9, type_action="U", uuid="51a6674d-7f28-427b-8cf7-25ad2ac07a09")
            models.Db_log.objects.create(datamodel="ope", id_model=11, type_action="U", uuid="51a6674d-7f28-427b-8cf7-25ad2ac07a10")
            models.Db_log.objects.create(datamodel="ope", id_model=12, type_action="U", uuid="51a6674d-7f28-427b-8cf7-25ad2ac07a11")
            models.Db_log.objects.create(datamodel="ope", id_model=13, type_action="U", uuid="51a6674d-7f28-427b-8cf7-25ad2ac07a12")
            models.Db_log.objects.create(datamodel="ope", id_model=14, type_action="I", uuid="51a6674d-7f28-427b-8cf7-25ad2ac07a13")
            models.Db_log.objects.create(datamodel="ope", id_model=15, type_action="I", uuid="51a6674d-7f28-427b-8cf7-25ad2ac07a14")
            models.Db_log.objects.create(datamodel="ope", id_model=16, type_action="I", uuid="51a6674d-7f28-427b-8cf7-25ad2ac07a15")
            models.Db_log.objects.create(datamodel="ope", id_model=17, type_action="I", uuid="51a6674d-7f28-427b-8cf7-25ad2ac07a16")
            models.Db_log.objects.create(datamodel="ope", id_model=18, type_action="I", uuid="51a6674d-7f28-427b-8cf7-25ad2ac07a17")
            models.Db_log.objects.create(datamodel="ope", id_model=19, type_action="D", uuid="51a6674d-7f28-427b-8cf7-25ad2ac07a18")
            date_time_action = datetime.datetime(2014, 6, 23, 18, 51, 40, tzinfo=tz.utc)
            models.Db_log.objects.all().update(date_time_action=date_time_action)
            mock_date = self.add_minutes(tz.make_aware(datetime.datetime(2014, 6, 23, 0, 0, 0), timezone=tz.utc))
            #test effectif
            with mock.patch('gsb.utils.timezone.now', mock_date.now):
                nb = self.exp.all_since_date(datetime.datetime(2014, 1, 21, 19, 27, 14, tzinfo=tz.utc))
            # compare nb
            compare(nb, collections.Counter({'global': 20, 'ope': 14, 'cat': 4, 'compte': 2}))
            #compare la liste des fichier
            attendu = os.path.join(settings.PROJECT_PATH, "gsb", "test_files", "export_plist_attendu", 'Applications',
                                   'Money Journal')
            recu = os.path.join(settings.PROJECT_PATH, "gsb", "test_files", "export_plist", 'Applications',
                                'Money Journal')
            list_fic_recu = list()
            list_fic_attendu = list()
            for root, dirs, files in os.walk(recu, topdown=False):
                for name in files:
                    list_fic_recu.append(os.path.basename(os.path.join(root, name)))
            for root, dirs, files in os.walk(attendu, topdown=False):
                for name in files:
                    list_fic_attendu.append(os.path.basename(os.path.join(root, name)))
            compare(list_fic_recu, list_fic_attendu)
            #compare chaque fichier
            self.comp_file('1403481660000.log', "export_plist_cat_modif")
            self.comp_file('1403481720000.log', "export_plist_cat_crea")
            self.comp_file('1403481780000.log', "export_plist_cat_vir_eff")
            self.comp_file('1403481840000.log', "export_plist_cat_vir")
            self.comp_file('1403481900000.log', "export_plist_compte_update")
            self.comp_file('1403481960000.log', "export_plist_compte_insert")
            self.comp_file('1403482020000.log', "export_plist_ope1_modifie_negatif")
            self.comp_file('1403482080000.log', "export_plist_ope2_modifie_positif")
            self.comp_file('1403482140000.log', "export_plist_ope3_ost")
            self.comp_file('1403482200000.log', "export_plist_ope8_virement_sortie")
            self.comp_file('1403482260000.log', "export_plist_ope9_virement_entree")
            self.comp_file('1403482320000.log', "export_plist_ope11_ope_ventile_mere")
            self.comp_file('1403482380000.log', "export_plist_ope12_ope_fille_1")
            self.comp_file('1403482440000.log', "export_plist_ope13_ope_fille_2")
            self.comp_file('1403482500000.log', "export_plist_ope14_vir_cree_sortie")
            self.comp_file('1403482560000.log', "export_plist_ope15_vir_cree_entree")
            self.comp_file('1403482620000.log', "export_plist_ope16_ope_mere_cree")
            self.comp_file('1403482680000.log', "export_plist_ope17_ope_fille_cree_1")
            self.comp_file('1403482740000.log', "export_plist_ope18_ope_fille_cree_2")
            self.comp_file('1403482800000.log', "export_plist_ope19_efface")
