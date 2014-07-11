# -*- coding: utf-8 -*
"""
test import
"""
from __future__ import absolute_import

from django.test.utils import override_settings
from django.conf import settings

import os.path
import datetime
import pytz

from gsb.io import lecture_plist

from gsb import models
from .test_imports_csv import Test_import_abstract
from gsb.io.lecture_plist import Lecture_plist_exception
from gsb.io.ecriture_plist_money_journal import export_icompta_plist
from testfixtures import Replacer,test_datetime,compare
from dateutil.parser import parse
from django.utils.encoding import force_unicode, smart_unicode
import warnings
warnings.filterwarnings("ignore", category=UnicodeWarning)
import collections

class Test_import_money_journal_element(Test_import_abstract):
    def test_money_journal_element_ope(self):
        fich=os.path.join(settings.PROJECT_PATH,"gsb","test_files","import_plist", 'Applications', 'Money Journal', 'log',"1402954705000.log")
        el=lecture_plist.Element(fich)
        self.assertEqual(el.device,'MyHpyVfqnK')
        self.assertEqual(el.datemaj, pytz.timezone(settings.TIME_ZONE).localize(datetime.datetime(2014, 6, 16, 23, 38, 25)))
        self.assertEqual(el.action, 'c')
        self.assertEqual(el.sens_element, 'd')
        self.assertEqual(el.is_ope, True)
        self.assertEqual(el.is_cat, False)
        self.assertEqual(el.is_compte, False)
        self.assertEqual(el.is_budget, False)
        self.assertEqual(el.lastup,  pytz.timezone(settings.TIME_ZONE).localize(datetime.datetime(2014, 6, 16, 23, 38, 25)))
        self.assertEqual(el.id, 66)
        self.assertEqual(el.cat, 1)
        self.assertEqual(el.automatique, False)
        self.assertEqual(el.date, datetime.date(2014, 6, 16))
        self.assertEqual(el.montant, -10.25)
        self.assertEqual(el.tiers, 'Ope standart')
        self.assertEqual(el.__unicode__(),u"OPE (66) le 16/06/2014 : -10.25 EUR a Ope standart cpt: 1")
        self.assertEqual(el.__str__(),u"OPE (66) le 16/06/2014 : -10.25 EUR a Ope standart cpt: 1")
        self.assertEqual(el.__repr__(),u"OPE (66) le 16/06/2014 : -10.25 EUR a Ope standart cpt: 1")
        el=lecture_plist.Element(os.path.join(settings.PROJECT_PATH,"gsb","test_files","import_plist", 'Applications', 'Money Journal', 'log',"1403036267000.log"))
        self.assertEqual(el.device,'MyHpyVfqnK')
        self.assertEqual(el.datemaj,  pytz.timezone(settings.TIME_ZONE).localize(datetime.datetime(2014, 6, 17, 22, 17, 47)))
        self.assertEqual(el.action, 'm')
        self.assertEqual(el.sens_element, 'd')
        self.assertEqual(el.is_ope, True)
        self.assertEqual(el.is_cat, False)
        self.assertEqual(el.is_compte, False)
        self.assertEqual(el.is_budget, False)
        self.assertEqual(el.lastup,  pytz.timezone(settings.TIME_ZONE).localize(datetime.datetime(2014, 6,  17, 22, 17, 47, 95470)))
        self.assertEqual(el.id, 66)
        self.assertEqual(el.cat, 1)
        self.assertEqual(el.automatique, False)
        self.assertEqual(el.date,  datetime.date(2014, 6, 16))
        self.assertEqual(el.montant, -55)
        self.assertEqual(el.tiers, 'Ope standart')
        el=lecture_plist.Element(os.path.join(settings.PROJECT_PATH,"gsb","test_files","import_plist", 'Applications', 'Money Journal', 'log',"1403037219000.log"))
        self.assertEqual(el.device,'MyHpyVfqnK')
        self.assertEqual(el.datemaj,  pytz.timezone(settings.TIME_ZONE).localize(datetime.datetime(2014, 6, 17, 22, 33, 39)))
        self.assertEqual(el.action, 'd')
        self.assertEqual(el.sens_element, 'd')
        self.assertEqual(el.is_ope, True)
        self.assertEqual(el.is_cat, False)
        self.assertEqual(el.is_compte, False)
        self.assertEqual(el.is_budget, False)
        self.assertEqual(el.lastup,  pytz.timezone(settings.TIME_ZONE).localize(datetime.datetime(2014, 6,  17, 22, 17, 47, 95470)))
        self.assertEqual(el.id, 66)
        self.assertEqual(el.cat, 1)
        self.assertEqual(el.automatique, False)
        self.assertEqual(el.date,  datetime.date(2014, 6, 16))
        self.assertEqual(el.montant, -55)
        self.assertEqual(el.tiers, 'Ope standart')
    def test_money_journal_element_compte(self):
        el=lecture_plist.Element(os.path.join(settings.PROJECT_PATH,"gsb","test_files","import_plist", 'Applications', 'Money Journal', 'log',"1403040634000.log"))
        self.assertEqual(el.device,'MyHpyVfqnK')
        self.assertEqual(el.datemaj,  pytz.timezone(settings.TIME_ZONE).localize(datetime.datetime(2014, 6, 17, 23, 30, 34)))
        self.assertEqual(el.action, 'c')
        self.assertEqual(el.is_ope, False)
        self.assertEqual(el.is_cat, False)
        self.assertEqual(el.is_compte, True)
        self.assertEqual(el.is_budget, False)
        self.assertEqual(el.lastup,  pytz.timezone(settings.TIME_ZONE).localize(datetime.datetime(2014, 6,  17, 23, 30, 34)))
        self.assertEqual(el.id, 7)
        self.assertEqual(el.couleur,0)
        self.assertEqual(el.nom, " ")
        el=lecture_plist.Element(os.path.join(settings.PROJECT_PATH,"gsb","test_files","import_plist", 'Applications', 'Money Journal', 'log',"1403040635000.log"))
        self.assertEqual(el.device,'MyHpyVfqnK')
        self.assertEqual(el.datemaj,  pytz.timezone(settings.TIME_ZONE).localize(datetime.datetime(2014, 6, 17, 23, 30, 35)))
        self.assertEqual(el.action, 'm')
        self.assertEqual(el.is_ope, False)
        self.assertEqual(el.is_cat, False)
        self.assertEqual(el.is_compte, True)
        self.assertEqual(el.is_budget, False)
        self.assertEqual(el.lastup,  pytz.timezone(settings.TIME_ZONE).localize(datetime.datetime(2014, 6,  17, 23, 30, 34,88255)))
        self.assertEqual(el.id, 7)
        self.assertEqual(el.couleur,0)
        self.assertEqual(el.nom, "Ghh")
        self.assertEqual(el.__unicode__(),u"COMPTE (7) 'Ghh'")
        self.assertEqual(el.__str__(),u"COMPTE (7) 'Ghh'")
        self.assertEqual(el.__repr__(),u"COMPTE (7) 'Ghh'")
        el=lecture_plist.Element(os.path.join(settings.PROJECT_PATH,"gsb","test_files","import_plist", 'Applications', 'Money Journal', 'log',"1403045414000.log"))
        self.assertEqual(el.device,'MyHpyVfqnK')
        self.assertEqual(el.datemaj,  pytz.timezone(settings.TIME_ZONE).localize(datetime.datetime(2014, 6, 18, 00, 50, 14)))
        self.assertEqual(el.action, 'd')
        self.assertEqual(el.is_ope, False)
        self.assertEqual(el.is_cat, False)
        self.assertEqual(el.is_compte, True)
        self.assertEqual(el.is_budget, False)
        self.assertEqual(el.lastup,  pytz.timezone(settings.TIME_ZONE).localize(datetime.datetime(2014, 6,  17, 23, 30, 34,88255)))
        self.assertEqual(el.id, 7)
        self.assertEqual(el.couleur,0)
        self.assertEqual(el.nom, "Ghh")
    def test_money_journal_element_cat(self):
        el=lecture_plist.Element(os.path.join(settings.PROJECT_PATH,"gsb","test_files","import_plist", 'Applications', 'Money Journal', 'log',"1403049014000.log"))
        self.assertEqual(el.device,'MyHpyVfqnK')
        self.assertEqual(el.datemaj,  pytz.timezone(settings.TIME_ZONE).localize(datetime.datetime(2014, 6, 18, 1, 50, 14)))
        self.assertEqual(el.action, 'c')
        self.assertEqual(el.is_ope, False)
        self.assertEqual(el.is_cat, True)
        self.assertEqual(el.is_compte, False)
        self.assertEqual(el.is_budget, False)
        self.assertEqual(el.lastup,  pytz.timezone(settings.TIME_ZONE).localize(datetime.datetime(2014, 6, 18, 1, 50, 14)))
        self.assertEqual(el.id, 16)
        self.assertEqual(el.couleur,0)
        self.assertEqual(el.nom, " ")
        self.assertEqual(el.type_cat,"d")
        el=lecture_plist.Element(os.path.join(settings.PROJECT_PATH,"gsb","test_files","import_plist", 'Applications', 'Money Journal', 'log',"1403049014010.log"))
        self.assertEqual(el.device,'MyHpyVfqnK')
        self.assertEqual(el.datemaj,  pytz.timezone(settings.TIME_ZONE).localize(datetime.datetime(2014, 6, 18, 1, 50, 14)))
        self.assertEqual(el.action, 'm')
        self.assertEqual(el.is_ope, False)
        self.assertEqual(el.is_cat, True)
        self.assertEqual(el.is_compte, False)
        self.assertEqual(el.is_budget, False)
        self.assertEqual(el.lastup,  pytz.timezone(settings.TIME_ZONE).localize(datetime.datetime(2014, 6, 18, 1, 50, 14,10000)))
        self.assertEqual(el.id, 16)
        self.assertEqual(el.couleur,0)
        self.assertEqual(el.nom, "Cat aded")
        self.assertEqual(el.type_cat,"d")
        self.assertEqual(el.__unicode__(),u"CAT (16) 'Cat aded' type:d")
        self.assertEqual(el.__str__(),u"CAT (16) 'Cat aded' type:d")
        self.assertEqual(el.__repr__(),u"CAT (16) 'Cat aded' type:d")
        el=lecture_plist.Element(os.path.join(settings.PROJECT_PATH,"gsb","test_files","import_plist", 'Applications', 'Money Journal', 'log',"1403049014020.log"))
        self.assertEqual(el.device,'MyHpyVfqnK')
        self.assertEqual(el.datemaj,  pytz.timezone(settings.TIME_ZONE).localize(datetime.datetime(2014, 6, 18, 1, 50, 14)))
        self.assertEqual(el.action, 'd')
        self.assertEqual(el.is_ope, False)
        self.assertEqual(el.is_cat, True)
        self.assertEqual(el.is_compte, False)
        self.assertEqual(el.is_budget, False)
        self.assertEqual(el.lastup,  pytz.timezone(settings.TIME_ZONE).localize(datetime.datetime(2014, 6, 18, 1, 50, 14,10000)))
        self.assertEqual(el.id, 16)
        self.assertEqual(el.couleur,0)
        self.assertEqual(el.nom, "Cat aded")
        self.assertEqual(el.type_cat,"d")

class Test_import_money_journal_check(Test_import_abstract):
    @override_settings(DIR_DROPBOX=os.path.join(settings.PROJECT_PATH,"gsb","test_files","import_plist"))
    def test_money_journal_element_check(self):
        self.assertEqual(lecture_plist.check(),True)#TODO improve it

class Test_import_money_journal_import_item_first_part(Test_import_abstract):
    def setUp(self):
        self.request = self.request_get('outils')
        self.lastmaj=pytz.timezone(settings.TIME_ZONE).localize(datetime.datetime(2014, 6, 15, 00, 25, 14))

    @override_settings(DIR_DROPBOX=os.path.join(settings.PROJECT_PATH,"gsb","test_files","import_plist"))
    def test_money_journal_element_import(self):
        """normalement il n'y a aucune operation"""
        self.lastmaj=pytz.timezone(settings.TIME_ZONE).localize(datetime.datetime(2014, 6, 20, 00, 25, 14))
        self.assertEqual(lecture_plist.import_items(lastmaj=self.lastmaj,request=self.request).most_common(),[('deja',9)])

    @override_settings(DIR_DROPBOX=os.path.join(settings.PROJECT_PATH,"gsb","test_files","import_plist"))
    def test_money_journal_element_import2(self):
        """avec crea, modif et del de chaque type"""
        self.assertEqual(lecture_plist.import_items(lastmaj=self.lastmaj, request=self.request).most_common(),
                        [('ope', 0), ('compte', 0), ('categorie', 0)])
    @override_settings(DIR_DROPBOX=os.path.join(settings.PROJECT_PATH,"gsb","test_files","import_plist_2"))
    def test_money_journal_element_import3(self):
        """avec crea, modif de cat et compte"""
        self.assertEqual(lecture_plist.import_items( lastmaj=self.lastmaj, request=self.request).most_common(),
                         [('compte', 1), ('categorie', 1)])
        self.assertmessagecontains(self.request,u"fichier: 1403040634000.log")
        self.assertmessagecontains(self.request,u"fichier: 1403040635000.log")
        self.assertmessagecontains(self.request,u"fichier: 1403049014000.log")
        self.assertmessagecontains(self.request,u"fichier: 1403049014010.log")
        self.assertmessagecontains(self.request,u"catégorie (16) 'Cat aded(d)' créée")
        self.assertmessagecontains(self.request,u"compte (7) 'Ghh' créé")
class Test_import_money_journal_import_item_modif_effectives_cote_cat(Test_import_abstract):
    def setUp(self):
        self.request = self.request_get('outils')
        self.lastmaj=pytz.timezone(settings.TIME_ZONE).localize(datetime.datetime(2014, 6, 15, 00, 25, 14))
        self.cat=models.Cat.objects.create(
                    pk=16,
                    nom=u"Cat aded",
                    type="d",
                    couleur=0)

    @override_settings(DIR_DROPBOX=os.path.join(settings.PROJECT_PATH,"gsb","test_files","import_plist_3"))
    def test_money_journal_element_import4(self):
        """teste modification standart"""
        self.cpt=models.Compte.objects.create(
                    pk=7,
                    nom='hjhjhkh',
                    couleur='#FFFFFF')
        self.cat.nom=u"Cat initial"
        self.cat.type='r'
        self.cat.couleur='#FFFFFF'
        self.cat.save()
        self.assertEqual(lecture_plist.import_items(lastmaj=self.lastmaj, request=self.request).most_common(),
                         [('compte', 1), ('categorie', 1)])
        self.assertmessagecontains(self.request,u"fichier: 1403040635000.log")
        self.assertmessagecontains(self.request,u"fichier: 1403049014010.log")
        self.assertmessagecontains(self.request,u"catégorie (16) modifiée comme ca: nom: Cat initial => Cat aded, couleur: #FFFFFF => 0, type: r => d")
        self.assertmessagecontains(self.request,u"compte (7) modifié comme ca: nom: hjhjhkh => Ghh, couleur: #FFFFFF => 0")
        cat=models.Cat.objects.get(pk=16)
        self.assertEqual(cat.nom,'Cat aded')
        self.assertEqual(cat.couleur,'0')
        self.assertEqual(cat.type,'d')
        obj=models.Compte.objects.get(pk=7)
        self.assertEqual(obj.nom,'Ghh')
    @override_settings(DIR_DROPBOX=os.path.join(settings.PROJECT_PATH,"gsb","test_files","import_plist_5"))
    def test_money_journal_element_import6(self):
        """ttest si cat deja cree"""
        with self.assertRaises(Lecture_plist_exception) as exception_context_manager:
            lecture_plist.import_items(lastmaj=self.lastmaj,request=self.request)
        self.assertEqual(exception_context_manager.exception.args, (u"attention la catégorie (16) existait déja alors qu'on demande de la créer", ))
    @override_settings(DIR_DROPBOX=os.path.join(settings.PROJECT_PATH,"gsb","test_files","import_plist_6"))
    def test_money_journal_element_import7(self):
        """ttest si modif alors que cat pas cree"""
        with self.assertRaises(Lecture_plist_exception) as exception_context_manager:
            lecture_plist.import_items(lastmaj=self.lastmaj,request=self.request)
        self.assertEqual(exception_context_manager.exception.args, (u"attention la catégorie (1111) n'existait pas alors qu'on demande de la modifier", ))
    @override_settings(DIR_DROPBOX=os.path.join(settings.PROJECT_PATH,"gsb","test_files","import_plist_8"))
    @override_settings(ID_CAT_OST=2)
    def test_money_journal_element_import8(self):
        """ttest si modif alors que cat par defaut"""
        models.Cat.objects.create(
                    pk=2,
                    nom=u"Cat ost",
                    type="r",
                    couleur='#FFFFFF')
        with self.assertRaises(Lecture_plist_exception) as exception_context_manager:
            lecture_plist.import_items(lastmaj=self.lastmaj,request=self.request)
        self.assertEqual(exception_context_manager.exception.args, (u"impossible de modifier la cat (2) car elle est par defaut", ))
    @override_settings(DIR_DROPBOX=os.path.join(settings.PROJECT_PATH,"gsb","test_files","import_plist_9"))
    def test_money_journal_element_import9(self):
        """ttest si modif cat avec le nom deja cree"""
        self.cat.type='r'
        self.cat.couleur='#FFFFFF'
        self.cat.save()
        lecture_plist.import_items(lastmaj=self.lastmaj,request=self.request)
        self.assertmessagecontains(self.request,u"catégorie (16) modifiée comme ca: couleur: #FFFFFF => 0, type: r => d")
    @override_settings(DIR_DROPBOX=os.path.join(settings.PROJECT_PATH,"gsb","test_files","import_plist_10"))
    def test_money_journal_element_import10(self):
        """ttest si suppr alors que cat pas cree"""
        self.cat.delete()
        with self.assertRaises(Lecture_plist_exception) as exception_context_manager:
            lecture_plist.import_items(lastmaj=self.lastmaj,request=self.request)
        self.assertEqual(exception_context_manager.exception.args, (u"attention la catégorie (16) n'existait pas alors qu'on demande de la supprimer", ))
    @override_settings(DIR_DROPBOX=os.path.join(settings.PROJECT_PATH,"gsb","test_files","import_plist_11"))
    def test_money_journal_element_import11(self):
        """ttest si suppr alors que cat deja utilise ds ope"""
        self.cpt=models.Compte.objects.create(
                    pk=7,
                    nom='Ghh',
                    couleur=0)
        self.moyen=models.Moyen.objects.create(
            id=settings.MD_CREDIT,
            nom=u"dd",
            type="r"
        )
        self.ope=models.Ope.objects.create(
                    compte=self.cpt,
                    date=datetime.date(2014, 6, 15),
                    montant = 250,
                    tiers=models.Tiers.objects.get_or_create(nom="tiers",defaults={'nom':"tiers"})[0],
                    cat=self.cat,
                    moyen=self.moyen
        )
        with self.assertRaises(Lecture_plist_exception) as exception_context_manager:
            lecture_plist.import_items(lastmaj=self.lastmaj,request=self.request)
        self.assertEqual(exception_context_manager.exception.args, (u"cat non supprimable 'CAT (16) 'Cat aded' type:d' car elle a des ope rattaches", ))
    @override_settings(DIR_DROPBOX=os.path.join(settings.PROJECT_PATH,"gsb","test_files","import_plist_12"))
    @override_settings(ID_CAT_OST=2)
    def test_money_journal_element_import12(self):
        """tente de supprimer une categorie par defaut"""
        models.Cat.objects.create(
                    pk=2,
                    nom=u"Cat ost",
                    type="r",
                    couleur='#FFFFFF')
        with self.assertRaises(Lecture_plist_exception) as exception_context_manager:
            lecture_plist.import_items(lastmaj=self.lastmaj,request=self.request)
        self.assertEqual(exception_context_manager.exception.args,(u"impossible de supprimer la catégorie (2) car elle est par défaut", ))
    @override_settings(DIR_DROPBOX=os.path.join(settings.PROJECT_PATH,"gsb","test_files","import_plist_12_1"))
    def test_money_journal_element_import12_1(self):
        """ttest suprr d'une cat"""
        lecture_plist.import_items(lastmaj=self.lastmaj,request=self.request)
        self.assertmessagecontains(self.request,u"catégorie (Cat aded) #16 supprimée")

class Test_import_money_journal_import_item_modif_effectives_cote_compte(Test_import_abstract):
    def setUp(self):
        self.request = self.request_get('outils')
        self.lastmaj=pytz.timezone(settings.TIME_ZONE).localize(datetime.datetime(2014, 6, 15, 00, 25, 14))
        self.cpt=models.Compte.objects.create(
                    pk=7,
                    nom='hjhjhkh',
                    couleur=0)
    @override_settings(DIR_DROPBOX=os.path.join(settings.PROJECT_PATH,"gsb","test_files","import_plist_4"))
    def test_money_journal_element_import5(self):
        """exception si compte deja cree"""
        with self.assertRaises(Lecture_plist_exception) as exception_context_manager:
            lecture_plist.import_items(lastmaj=self.lastmaj,request=self.request)
        self.assertEqual(exception_context_manager.exception.args, (u"attention le compte(7) existait déja alors qu'on demande de le créer", ))
    @override_settings(DIR_DROPBOX=os.path.join(settings.PROJECT_PATH,"gsb","test_files","import_plist_13"))
    def test_money_journal_element_import13(self):
        """ttest si modif compte avec le nom deja cree"""
        self.cpt.couleur="#FFFFFF"
        self.cpt.save()
        lecture_plist.import_items(lastmaj=self.lastmaj,request=self.request)
        self.assertmessagecontains(self.request,u"compte (7) modifié comme ca: couleur: #FFFFFF => 0")
    @override_settings(DIR_DROPBOX=os.path.join(settings.PROJECT_PATH,"gsb","test_files","import_plist_14"))
    def test_money_journal_element_import14(self):
        """ttest si suppr alors que compte pas cree"""
        self.cpt.delete()
        with self.assertRaises(Lecture_plist_exception) as exception_context_manager:
            lecture_plist.import_items(lastmaj=self.lastmaj,request=self.request)
        self.assertEqual(exception_context_manager.exception.args, (u"attention le compte '7' n'existe pas pour ce nom (hjhjhkh) alors qu'on demande de le supprimer", ))
    @override_settings(DIR_DROPBOX=os.path.join(settings.PROJECT_PATH,"gsb","test_files","import_plist_15"))
    def test_money_journal_element_import15(self):
        """ttest si suppr alors que compte deja utilise ds ope"""
        cat=models.Cat.objects.create(
                    pk=16,
                    nom=u"Cat aded",
                    type="r",
                    couleur='#FFFFFF')
        moyen=models.Moyen.objects.create(
            id=settings.MD_CREDIT,
            nom=u"dd",
            type="r"
        )
        models.Ope.objects.create(
                    compte=self.cpt,
                    date=datetime.date(2014, 6, 15),
                    montant = 250,
                    tiers=models.Tiers.objects.get_or_create(nom="tiers",defaults={'nom':"tiers"})[0],
                    cat=cat,
                    moyen=moyen
        )
        with self.assertRaises(Lecture_plist_exception) as exception_context_manager:
            lecture_plist.import_items(lastmaj=self.lastmaj,request=self.request)
        self.assertEqual(exception_context_manager.exception.args, (u"compte non supprimable 'hjhjhkh' # 7 car il a des opérations ou des écheances rattachées", ))
    @override_settings(DIR_DROPBOX=os.path.join(settings.PROJECT_PATH,"gsb","test_files","import_plist_16"))
    def test_money_journal_element_import16(self):
        """ttest suppr d'un compte"""
        lecture_plist.import_items(lastmaj=self.lastmaj,request=self.request)
        self.assertmessagecontains(self.request,u"compte 'hjhjhkh' #7 supprimé")

class Test_import_money_journal_import_item_modif_effectives_cote_ope(Test_import_abstract):
    def setUp(self):
        self.request = self.request_get('outils')
        self.lastmaj=pytz.timezone(settings.TIME_ZONE).localize(datetime.datetime(2014, 6, 15, 00, 25, 14))
        self.cat=models.Cat.objects.create(
                    pk=1,
                    nom=u"Cat aded",
                    type="d",
                    couleur=0)
        self.cat2=models.Cat.objects.create(
                    pk=2,
                    nom=u"Cat aded2",
                    type="d",
                    couleur=0)
        self.cpt=models.Compte.objects.create(
                    pk=1,
                    nom='Ghh',
                    couleur=0)
        self.cpt2=models.Compte.objects.create(
                    pk=2,
                    nom='Ghh2',
                    couleur=0)
        self.moyen_credit=models.Moyen.objects.create(
            id=settings.MD_CREDIT,
            nom=u"rr",
            type="r"
        )
        self.moyen_debit=models.Moyen.objects.create(
            id=settings.MD_DEBIT,
            nom=u"dd",
            type="d"
        )
        self.tiers=models.Tiers.objects.get_or_create(nom="Ope standart",defaults={'nom':"Ope standart"})[0]
        self.tiers2=models.Tiers.objects.get_or_create(nom="tiers2",defaults={'nom':"tiers2"})[0]
        self.ope=models.Ope.objects.create(
                    pk=66,
                    compte=self.cpt2,
                    date=datetime.date(2013, 6, 15),
                    montant = 25,
                    tiers=self.tiers2,
                    cat=self.cat2,
                    moyen=self.moyen_credit
        )
    @override_settings(DIR_DROPBOX=os.path.join(settings.PROJECT_PATH,"gsb","test_files","import_plist_17"))
    def test_money_journal_element_import17(self):
        """si un compte pour une ope n'existe pas"""
        self.ope.delete()
        self.cpt.delete()
        with self.assertRaises(Lecture_plist_exception) as exception_context_manager:
            lecture_plist.import_items(lastmaj=self.lastmaj,request=self.request)
        self.assertEqual(exception_context_manager.exception.args, (u"attention le compte (1) n'existait pas alors qu'on le demande pour l'ope #66", ))
    @override_settings(DIR_DROPBOX=os.path.join(settings.PROJECT_PATH,"gsb","test_files","import_plist_18"))
    def test_money_journal_element_import18(self):
        """si une categorie pour une ope n'existe pas"""
        self.ope.delete()
        self.cat.delete()
        with self.assertRaises(Lecture_plist_exception) as exception_context_manager:
            lecture_plist.import_items(lastmaj=self.lastmaj,request=self.request)
        self.assertEqual(exception_context_manager.exception.args, (u"attention la catégorie (1) n'existait pas alors qu'on le demande pour l'ope #66", ))

    @override_settings(DIR_DROPBOX=os.path.join(settings.PROJECT_PATH,"gsb","test_files","import_plist_19"))
    def test_money_journal_element_import19(self):
        """si une ope existe deja"""
        with self.assertRaises(Lecture_plist_exception) as exception_context_manager:
            lecture_plist.import_items(lastmaj=self.lastmaj,request=self.request)
        self.assertEqual(exception_context_manager.exception.args, (u"attention l'opération (66) existe déja alors qu'on demande de le créer", ))
    @override_settings(DIR_DROPBOX=os.path.join(settings.PROJECT_PATH,"gsb","test_files","import_plist_20"))
    def test_money_journal_element_import20(self):
        """test ope cree sans probleme"""
        self.ope.delete()
        self.tiers.delete()
        lecture_plist.import_items(lastmaj=self.lastmaj,request=self.request)
        self.assertmessagecontains(self.request,u"tiers 'Ope standart' crée")
        self.assertmessagecontains(self.request,u"opération '(66) le 16/06/2014 : -10.25 EUR a Ope standart cpt: Ghh' créée")
    @override_settings(DIR_DROPBOX=os.path.join(settings.PROJECT_PATH,"gsb","test_files","import_plist_21"))
    def test_money_journal_element_import21(self):
        """test ope cree sans probleme"""
        self.ope.delete()
        self.cat.delete()
        self.cpt.delete()
        lecture_plist.import_items(lastmaj=self.lastmaj,request=self.request)
        self.assertmessagecontains(self.request,u"opération '(66) le 16/06/2014 : -10.25 EUR a Ope standart cpt: hjhjhkh' créée")
    @override_settings(DIR_DROPBOX=os.path.join(settings.PROJECT_PATH,"gsb","test_files","import_plist_22"))
    def test_money_journal_element_import22(self):
        """test si ope a mofifier n'existe pas"""
        self.ope.delete()
        with self.assertRaises(Lecture_plist_exception) as exception_context_manager:
            lecture_plist.import_items(lastmaj=self.lastmaj,request=self.request)
        self.assertEqual(exception_context_manager.exception.args, (u"attention cette opé '66' n'existait pas alors qu'on demande de le modifier", ))
    @override_settings(DIR_DROPBOX=os.path.join(settings.PROJECT_PATH,"gsb","test_files","import_plist_23"))
    def test_money_journal_element_import23(self):
        """test si ope mere"""
        fille=models.Ope.objects.create(
                    pk=67,
                    compte=self.cpt,
                    date=datetime.date(2014, 6, 15),
                    montant = -10.25,
                    tiers=self.tiers,
                    cat=self.cat,
                    moyen=self.moyen_debit
        )
        fille.mere=self.ope
        fille.save()
        with self.assertRaises(Lecture_plist_exception) as exception_context_manager:
            lecture_plist.import_items(lastmaj=self.lastmaj,request=self.request)
        self.assertEqual(exception_context_manager.exception.args, (u"impossible de modifier cette opé '(66) le 15/06/2013 : -10.25 EUR a tiers2 cpt: Ghh2' car elle est mère", ))
    @override_settings(DIR_DROPBOX=os.path.join(settings.PROJECT_PATH,"gsb","test_files","import_plist_23"))
    def test_money_journal_element_import24(self):
        """test si ope fille"""
        mere=models.Ope.objects.create(
                    pk=67,
                    compte=self.cpt,
                    date=datetime.date(2014, 6, 15),
                    montant = -10.25,
                    tiers=self.tiers,
                    cat=self.cat,
                    moyen=self.moyen_debit
        )
        self.ope.mere=mere
        self.ope.save()
        with self.assertRaises(Lecture_plist_exception) as exception_context_manager:
            lecture_plist.import_items(lastmaj=self.lastmaj,request=self.request)
        self.assertEqual(exception_context_manager.exception.args, (u"impossible de modifier cette opé '(66) le 15/06/2013 : 25 EUR a tiers2 cpt: Ghh2' car elle est fille", ))
    @override_settings(DIR_DROPBOX=os.path.join(settings.PROJECT_PATH,"gsb","test_files","import_plist_23"))
    def test_money_journal_element_import25(self):
        """test si ope rapprochee"""
        rapp=models.Rapp.objects.create(
                    nom="test_rapp"
        )
        self.ope.rapp=rapp
        self.ope.save()
        with self.assertRaises(Lecture_plist_exception) as exception_context_manager:
            lecture_plist.import_items(lastmaj=self.lastmaj,request=self.request)
        self.assertEqual(exception_context_manager.exception.args, (u"impossible de modifier cette opé '(66) le 15/06/2013 : 25 EUR a tiers2 cpt: Ghh2' car elle est rapprochée", ))
    @override_settings(DIR_DROPBOX=os.path.join(settings.PROJECT_PATH,"gsb","test_files","import_plist_23"))
    def test_money_journal_element_import26(self):
        """test si ope avec compte ferme"""
        self.cpt2.ouvert=False
        self.cpt2.save()
        with self.assertRaises(Lecture_plist_exception) as exception_context_manager:
            lecture_plist.import_items(lastmaj=self.lastmaj,request=self.request)
        self.assertEqual(exception_context_manager.exception.args, (u"impossible de modifier cette opé '(66) le 15/06/2013 : 25 EUR a tiers2 cpt: Ghh2' car son compte est fermé", ))
    @override_settings(DIR_DROPBOX=os.path.join(settings.PROJECT_PATH,"gsb","test_files","import_plist_23"))
    def test_money_journal_element_import27(self):
        """test si ope jumelle"""
        jumelle=models.Ope.objects.create(
                    pk=67,
                    compte=self.cpt,
                    date=datetime.date(2014, 6, 15),
                    montant = 10.25,
                    tiers=self.tiers,
                    cat=self.cat,
                    moyen=self.moyen_credit
        )
        self.ope.jumelle=jumelle
        self.ope.save()
        with self.assertRaises(Lecture_plist_exception) as exception_context_manager:
            lecture_plist.import_items(lastmaj=self.lastmaj,request=self.request)
        self.assertEqual(exception_context_manager.exception.args, (u"impossible de modifier cette opé '(66) le 15/06/2013 : 25 EUR a tiers2 cpt: Ghh2' car elle est jumellée", ))
    @override_settings(DIR_DROPBOX=os.path.join(settings.PROJECT_PATH,"gsb","test_files","import_plist_23"))
    def test_money_journal_element_import28(self):
        """test si modif d'ope pointee"""
        self.ope.pointe=True
        self.ope.save()
        with self.assertRaises(Lecture_plist_exception) as exception_context_manager:
            lecture_plist.import_items(lastmaj=self.lastmaj,request=self.request)
        self.assertEqual(exception_context_manager.exception.args, (u"impossible de modifier cette opé '(66) le 15/06/2013 : 25 EUR a tiers2 cpt: Ghh2' car elle est pointée", ))
    @override_settings(DIR_DROPBOX=os.path.join(settings.PROJECT_PATH,"gsb","test_files","import_plist_23"))
    def test_money_journal_element_import29(self):
        """test si ope modifie sans probleme"""
        lecture_plist.import_items(lastmaj=self.lastmaj,request=self.request)
        self.assertmessagecontains(self.request,u"opération (66) modifiée comme ca: compte: 2 => 1\n, cat: 2 => 1\n, date: 2013-06-15 => 2014-06-16\n, montant: 25 => -10.25\n, tiers: tiers2 => Ope standart")
    @override_settings(DIR_DROPBOX=os.path.join(settings.PROJECT_PATH,"gsb","test_files","import_plist_23"))
    def test_money_journal_element_import30(self):
        """test si ope modifie sans probleme avec le compte deja modifie"""
        self.ope.compte=self.cpt
        self.ope.save()
        lecture_plist.import_items(lastmaj=self.lastmaj,request=self.request)
        self.assertmessagecontains(self.request,u"opération (66) modifiée comme ca: cat: 2 => 1\n, date: 2013-06-15 => 2014-06-16\n, montant: 25 => -10.25\n, tiers: tiers2 => Ope standart")
    @override_settings(DIR_DROPBOX=os.path.join(settings.PROJECT_PATH,"gsb","test_files","import_plist_31"))
    def test_money_journal_element_import31(self):
        """test si ope n'existe pas alors qu'elle va etre supprimer"""
        self.ope.delete()
        with self.assertRaises(Lecture_plist_exception) as exception_context_manager:
            lecture_plist.import_items(lastmaj=self.lastmaj,request=self.request)
        self.assertEqual(exception_context_manager.exception.args, (u"attention cette opé '66' n'existait pas alors qu'on demande de le supprimer", ))
    @override_settings(DIR_DROPBOX=os.path.join(settings.PROJECT_PATH,"gsb","test_files","import_plist_31"))
    def test_money_journal_element_import32(self):
        """test supprimeer une mere"""
        fille=models.Ope.objects.create(
                    pk=67,
                    compte=self.cpt,
                    date=datetime.date(2014, 6, 15),
                    montant = -10.25,
                    tiers=self.tiers,
                    cat=self.cat,
                    moyen=self.moyen_debit
        )
        fille.mere=self.ope
        fille.save()
        with self.assertRaises(Lecture_plist_exception) as exception_context_manager:
            lecture_plist.import_items(lastmaj=self.lastmaj,request=self.request)
        self.assertEqual(exception_context_manager.exception.args, (u"impossible de supprimer cette opé '(66) le 15/06/2013 : -10.25 EUR a tiers2 cpt: Ghh2' car elle est mère", ))
    @override_settings(DIR_DROPBOX=os.path.join(settings.PROJECT_PATH,"gsb","test_files","import_plist_31"))
    def test_money_journal_element_import33(self):
        """test si ope fille"""
        mere=models.Ope.objects.create(
                    pk=67,
                    compte=self.cpt,
                    date=datetime.date(2014, 6, 15),
                    montant = -10.25,
                    tiers=self.tiers,
                    cat=self.cat,
                    moyen=self.moyen_debit
        )
        self.ope.mere=mere
        self.ope.save()
        with self.assertRaises(Lecture_plist_exception) as exception_context_manager:
            lecture_plist.import_items(lastmaj=self.lastmaj,request=self.request)
        self.assertEqual(exception_context_manager.exception.args, (u"impossible de supprimer cette opé '(66) le 15/06/2013 : 25 EUR a tiers2 cpt: Ghh2' car elle est fille", ))
    @override_settings(DIR_DROPBOX=os.path.join(settings.PROJECT_PATH,"gsb","test_files","import_plist_31"))
    def test_money_journal_element_import34(self):
        """test si ope rapprochee"""
        rapp=models.Rapp.objects.create(
                    nom="test_rapp"
        )
        self.ope.rapp=rapp
        self.ope.save()
        with self.assertRaises(Lecture_plist_exception) as exception_context_manager:
            lecture_plist.import_items(lastmaj=self.lastmaj,request=self.request)
        self.assertEqual(exception_context_manager.exception.args, (u"impossible de supprimer cette opé '(66) le 15/06/2013 : 25 EUR a tiers2 cpt: Ghh2' car elle est rapprochée", ))
    @override_settings(DIR_DROPBOX=os.path.join(settings.PROJECT_PATH,"gsb","test_files","import_plist_31"))
    def test_money_journal_element_import35(self):
        """test si ope avec compte ferme"""
        self.cpt2.ouvert=False
        self.cpt2.save()
        with self.assertRaises(Lecture_plist_exception) as exception_context_manager:
            lecture_plist.import_items(lastmaj=self.lastmaj,request=self.request)
        self.assertEqual(exception_context_manager.exception.args, (u"impossible de supprimer cette opé '(66) le 15/06/2013 : 25 EUR a tiers2 cpt: Ghh2' car son compte est fermé", ))
    @override_settings(DIR_DROPBOX=os.path.join(settings.PROJECT_PATH,"gsb","test_files","import_plist_31"))
    def test_money_journal_element_import36(self):
        """test si ope jumelle"""
        jumelle=models.Ope.objects.create(
                    pk=67,
                    compte=self.cpt,
                    date=datetime.date(2014, 6, 15),
                    montant = 10.25,
                    tiers=self.tiers,
                    cat=self.cat,
                    moyen=self.moyen_credit
        )
        self.ope.jumelle=jumelle
        self.ope.save()
        with self.assertRaises(Lecture_plist_exception) as exception_context_manager:
            lecture_plist.import_items(lastmaj=self.lastmaj,request=self.request)
        self.assertEqual(exception_context_manager.exception.args, (u"impossible de supprimer cette opé '(66) le 15/06/2013 : 25 EUR a tiers2 cpt: Ghh2' car elle est jumellée", ))
    @override_settings(DIR_DROPBOX=os.path.join(settings.PROJECT_PATH,"gsb","test_files","import_plist_31"))
    def test_money_journal_element_import37(self):
        """test si modif d'ope pointee"""
        self.ope.pointe=True
        self.ope.save()
        with self.assertRaises(Lecture_plist_exception) as exception_context_manager:
            lecture_plist.import_items(lastmaj=self.lastmaj,request=self.request)
        self.assertEqual(exception_context_manager.exception.args, (u"impossible de supprimer cette opé '(66) le 15/06/2013 : 25 EUR a tiers2 cpt: Ghh2' car elle est pointée", ))
    @override_settings(DIR_DROPBOX=os.path.join(settings.PROJECT_PATH,"gsb","test_files","import_plist_31"))
    def test_money_journal_element_import38(self):
        """test si ope modifie sans probleme"""
        self.ope.delete()
        self.ope=models.Ope.objects.create(
                    pk=66,
                    compte=self.cpt,
                    date=datetime.date(2014, 6, 16),
                    montant = -10.25,
                    tiers=self.tiers,
                    cat=self.cat,
                    moyen=self.moyen_debit
        )
        lecture_plist.import_items(lastmaj=self.lastmaj,request=self.request)
        self.assertmessagecontains(self.request,u"opération (66) le 16/06/2014 : -10.25 EUR a Ope standart cpt: Ghh supprimée")
    @override_settings(DIR_DROPBOX=os.path.join(settings.PROJECT_PATH,"gsb","test_files","import_plist_31"))
    def test_money_journal_element_import39(self):
        """test si ope modifie"""
        self.ope.delete()
        self.ope=models.Ope.objects.create(
                    pk=66,
                    compte=self.cpt,
                    date=datetime.date(2014, 6, 15),
                    montant = -10.25,
                    tiers=self.tiers,
                    cat=self.cat,
                    moyen=self.moyen_debit
        )
        with self.assertRaises(Lecture_plist_exception) as exception_context_manager:
            lecture_plist.import_items(lastmaj=self.lastmaj,request=self.request)
        self.assertEqual(exception_context_manager.exception.args, (u"attention cette opé '66' existe alors qu'on demande de le supprimer mais elle est différente :\nCPT:\t1==1\nDATE:\t2014-06-15!=2014-06-16\nmontant:\t-10.25==-10.25\ntiers:\tOpe standart==Ope standart\ncat:\t1==1",))

class Test_import_money_journal_gestion_maj(Test_import_abstract):

    def setUp(self):
        self.request = self.request_get('outils')

    @override_settings(DIR_DROPBOX=os.path.join(settings.PROJECT_PATH,"gsb","test_files","import_plist_20"))
    def test_money_journal_element_import20(self):
        """test ope cree sans probleme"""
        self.cat=models.Cat.objects.create(
                    pk=1,
                    nom=u"Cat aded",
                    type="d",
                    couleur=0)
        self.cpt=models.Compte.objects.create(
                    pk=1,
                    nom='Ghh',
                    couleur=0)
        self.moyen_debit=models.Moyen.objects.create(
            id=settings.MD_DEBIT,
            nom=u"dd",
            type="d"
        )
        reponse=lecture_plist.gestion_maj(self.request).content
        self.assertfileequal(reponse,os.path.join('export_plist_views','sortie_import_view.html'),nom="import_normal")



@override_settings(CODE_DEVICE_POCKET_MONEY='totototo')
@override_settings(DIR_DROPBOX=os.path.join(settings.PROJECT_PATH,"gsb","test_files","export_plist"))
class Test_import_money_journal_export(Test_import_abstract):
    fixtures = ['test_money_journal.yaml',]
    def setUp(self):
        self.request = self.request_get('outils')
        self.exp=export_icompta_plist(72,69,3)
        self.nettoyage()
    def __tearDown(self):
        self.nettoyage()

    def nettoyage(self,file_only=True):
        directory=os.path.join(settings.PROJECT_PATH,"gsb","test_files","export_plist", 'Applications', 'Money Journal', 'log')
        efface=list()
        for root, dirs, files in os.walk(directory, topdown=False):
            for name in files:
                efface.append(os.path.join(root, name))
                os.remove(os.path.join(root, name))
        if not file_only:
            for root, dirs, files in os.walk(directory, topdown=False):
                for name in dirs:
                    efface.append(os.path.join(root, name))
                    os.rmdir(os.path.join(root, name))
        for d in sorted(efface):
            #print "%s efface"%d
            pass
    def rep(self,filename,nom):
        attendu=os.path.join("export_plist_attendu", 'Applications', 'Money Journal', 'log','140','3','5',filename)
        recu=os.path.join("export_plist", 'Applications', 'Money Journal', 'log','140','3','5',filename)
        self.assert2filesequal(recu,attendu,nom=nom)
    def strptime(self,txt):
        txt=force_unicode(txt)
        return  parse(txt)
    def test_global(self):
        with Replacer() as r:
            r.replace('gsb.utils.datetime.datetime',test_datetime(2014,06,23,21,25,14,delta=1,delta_type='minutes'))
            #on efface la table db_log
            models.Db_log.objects.all().delete()
            models.Db_log.objects.create(datamodel="cat",id_model=1,memo="U", uuid="51a6674d-7f28-427b-8cf7-25ad2ac07901", date_created=self.strptime("2014-06-23 18:51:40.571000+00:00"))
            models.Db_log.objects.create(datamodel="cat",id_model=2,memo="I", uuid="51a6674d-7f28-427b-8cf7-25ad2ac07902", date_created=self.strptime("2014-06-23 18:51:40.571000+00:00"))
            models.Db_log.objects.create(datamodel="cat",id_model=72,memo="I", uuid="51a0004d-7f28-427b-8cf7-44ad2ac07972", date_created=self.strptime("2014-06-23 18:51:40.571000+00:00"))
            #on modifie afin d'avoir les bons
            models.Cat.objects.filter(id=4).delete()#la cat 4 a ete efface
            models.Compte.objects.filter(id=1).update(nom="compte_modifie")
            models.Compte.objects.create(nom="Compte nouveau")
            models.Db_log.objects.create(datamodel="ope",id_model=1,memo="U", uuid="51a6674d-7f28-427b-8cf7-25ad2ac07a01", date_created=self.strptime("2014-06-23 18:51:40.571000+00:00"))
            models.Db_log.objects.create(datamodel="ope",id_model=2,memo="U", uuid="51a6674d-7f28-427b-8cf7-25ad2ac07a02", date_created=self.strptime("2014-06-23 18:51:40.571000+00:00"))
            models.Db_log.objects.create(datamodel="ope",id_model=3,memo="U", uuid="51a6674d-7f28-427b-8cf7-25ad2ac07a03", date_created=self.strptime("2014-06-23 18:51:40.571000+00:00"))
            models.Db_log.objects.create(datamodel="ope",id_model=8,memo="U", uuid="51a6674d-7f28-427b-8cf7-25ad2ac07a08", date_created=self.strptime("2014-06-23 18:51:40.571000+00:00"))
            models.Db_log.objects.create(datamodel="ope",id_model=9,memo="U", uuid="51a6674d-7f28-427b-8cf7-25ad2ac07a09", date_created=self.strptime("2014-06-23 18:51:40.571000+00:00"))
            models.Db_log.objects.create(datamodel="ope",id_model=11,memo="U", uuid="51a6674d-7f28-427b-8cf7-25ad2ac07a10", date_created=self.strptime("2014-06-23 18:51:40.571000+00:00"))
            models.Db_log.objects.create(datamodel="ope",id_model=12,memo="U", uuid="51a6674d-7f28-427b-8cf7-25ad2ac07a11", date_created=self.strptime("2014-06-23 18:51:40.571000+00:00"))
            models.Db_log.objects.create(datamodel="ope",id_model=13,memo="U", uuid="51a6674d-7f28-427b-8cf7-25ad2ac07a12", date_created=self.strptime("2014-06-23 18:51:40.571000+00:00"))
            models.Db_log.objects.create(datamodel="ope",id_model=14,memo="I", uuid="51a6674d-7f28-427b-8cf7-25ad2ac07a13", date_created=self.strptime("2014-06-23 18:51:40.571000+00:00"))
            models.Db_log.objects.create(datamodel="ope",id_model=15,memo="I", uuid="51a6674d-7f28-427b-8cf7-25ad2ac07a14", date_created=self.strptime("2014-06-23 18:51:40.571000+00:00"))
            models.Db_log.objects.create(datamodel="ope",id_model=16,memo="I", uuid="51a6674d-7f28-427b-8cf7-25ad2ac07a15", date_created=self.strptime("2014-06-23 18:51:40.571000+00:00"))
            models.Db_log.objects.create(datamodel="ope",id_model=17,memo="I", uuid="51a6674d-7f28-427b-8cf7-25ad2ac07a16", date_created=self.strptime("2014-06-23 18:51:40.571000+00:00"))
            models.Db_log.objects.create(datamodel="ope",id_model=18,memo="I", uuid="51a6674d-7f28-427b-8cf7-25ad2ac07a17", date_created=self.strptime("2014-06-23 18:51:40.571000+00:00"))
            models.Db_log.objects.create(datamodel="ope",id_model=19,memo="D", uuid="51a6674d-7f28-427b-8cf7-25ad2ac07a18", date_created=self.strptime("2014-06-23 18:51:40.571000+00:00"))

            #test effectif
            nb=self.exp.all_since_date(pytz.utc.localize(datetime.datetime(2014, 01, 21, 19, 27, 14)))
            print nb
            #compare la liste des fichier
            attendu=os.path.join(settings.PROJECT_PATH,"gsb","test_files","export_plist_attendu", 'Applications', 'Money Journal')
            recu=os.path.join(settings.PROJECT_PATH,"gsb","test_files","export_plist", 'Applications', 'Money Journal')
            list_fic_recu=list()
            list_fic_attendu=list()
            for root, dirs, files in os.walk(recu, topdown=False):
                for name in files:
                    list_fic_recu.append(os.path.basename(os.path.join(root, name)))
            for root, dirs, files in os.walk(attendu, topdown=False):
                for name in files:
                    list_fic_attendu.append(os.path.basename(os.path.join(root, name)))

            #compare chaque fichier
            self.rep('1403559794000.log',"export_plist_cat_modif")
            self.rep('1403559854000.log',"export_plist_cat_crea")
            self.rep('1403559914000.log',"export_plist_cat_vir")
            self.rep('1403559974000.log',"export_plist_cat_vir_eff")
            compare(nb,collections.Counter({u'ope': 14, u'cat': 4, u'compte': 2}))
            #compare(list_fic_recu,list_fic_attendu)


