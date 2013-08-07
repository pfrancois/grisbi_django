# -*- coding: utf-8 -*
'''
Created on 25 mars 2013

@author: francois
'''

from __future__ import absolute_import
from django.test import RequestFactory
from .test_base import TestCase
from django.core.urlresolvers import reverse
from gsb.io import export_base
import gsb.io.export_csv as ex_csv
import logging

import re

class Test_view_base(TestCase):
    fixtures = ['test.json', 'auth.json']

    def setUp(self):
        super(Test_view_base, self).setUp()
        self.client.login(username='admin', password='mdp')

class Test_export_csv(Test_view_base):
    def test_csv_global(self):
        logger = logging.getLogger('gsb')
        logger.setLevel(40)  # change le niveau de log (10 = debug, 20=info)
        rep = self.client.post(reverse('export_csv'), data={'collection':(1, 2, 3, 4, 5, 6), "date_min": "2011-01-01", "date_max": "2012-09-24"})
        reponse_attendu = u"""id;cpt;date;montant;r;p;moyen;cat;tiers;notes;projet;numchq;id jumelle lie;has_fille;id_ope_m;ope_titre;ope_pmv;mois\r
4;cpte1;11/08/2011;-100,00;cpte1201101;0;moyen_dep1;cat1;tiers1;;;;;0;;;;08\r
5;cpte1;11/08/2011;10,00;cpte1201101;0;moyen_rec1;cat2;tiers1;;;;;0;;;;08\r
7;cpte1;11/08/2011;10,00;;1;moyen_rec1;cat1;tiers1;;ib1;;;0;;;;08\r
6;cpte1;21/08/2011;10,00;;0;moyen_rec1;cat2;tiers2;fusion avec ope1;ib2;;;0;;;;08\r
3;cpt_titre2;29/10/2011;-100,00;cpt_titre2201101;0;moyen_dep3;Operation Sur Titre;titre_ t2;20@5;;;;0;;3;;10\r
8;cpte1;30/10/2011;-100,00;;0;moyen_vir4;Virement;virement;;;;9;0;;;;10\r
9;cptb3;30/10/2011;100,00;;0;moyen_vir4;Virement;virement;;;;8;0;;;;10\r
2;cpt_titre2;30/11/2011;-1500,00;;0;moyen_dep3;Operation Sur Titre;titre_ t2;150@10;;;;0;;2;;11\r
1;cpt_titre1;18/12/2011;-1,00;;0;moyen_dep2;Operation Sur Titre;titre_ t1;1@1;;;;0;;1;;12\r
10;cpt_titre1;24/09/2012;-5,00;;0;moyen_dep2;Operation Sur Titre;titre_ autre;5@1;;;;0;;4;;09\r
11;cpte1;24/09/2012;100,00;;0;moyen_rec1;Opération Ventilée;tiers2;;;;;1;;;;09\r
12;cpte1;24/09/2012;99,00;;0;moyen_rec1;cat1;tiers2;;;;;0;11;;;09\r
13;cpte1;24/09/2012;1,00;;0;moyen_rec1;cat2;tiers2;;;;;0;11;;;09\r
"""
        reponse_recu = rep.content
        # on coupe ligne par ligne
        ra_iter = reponse_attendu.split('\r\n')
        rr_iter = reponse_recu.split('\r\n')
        for ra, rr in zip(ra_iter, rr_iter):
            self.assertEqual(ra, unicode(rr, 'cp1252'))
    def test_csv_debug(self):
        # on cree ce les entree de la vue
        req = RequestFactory()
        request = req.post(reverse('export_csv'), data={'collection':(1, 2, 3, 4, 5, 6), "date_min": "2011-01-01", "date_max": "2012-09-24"})
        # initialisation de la vue
        view = self.setup_view(ex_csv.Export_ope_csv(), request)
        # choix des parametre du test proprement dit
        view.debug = True
        # de la ligne d'export
        data = u"4;cpte1;11/08/2011;-100,00;cpte1201101;0;moyen_dep1;cat1;tiers1;;;;;0;;;;08".split(";")
        header = view.fieldnames
        final = dict()
        for d, h in zip(data, header):
            final[h] = d
        # on compare a ce qui est attendu
        reponse_recu = view.export_csv_view(data=[final], nomfich='test_file').content
        reponse_attendu = u"""id;cpt;date;montant;r;p;moyen;cat;tiers;notes;projet;numchq;id jumelle lie;has_fille;id_ope_m;ope_titre;ope_pmv;mois\r
4;cpte1;11/08/2011;-100,00;cpte1201101;0;moyen_dep1;cat1;tiers1;;;;;0;;;;08\r
"""
        ra_iter = reponse_attendu.split('\r\n')
        rr_iter = reponse_recu.split('\r\n')
        for ra, rr in zip(ra_iter, rr_iter):
            self.assertEqual(ra, unicode(rr, 'cp1252'))

    def test_export_form1(self):
        form_data = {'date_min':"01/01/2010",
                   'date_max':"31/12/2013",
                   'collection':""
                   }
        form = export_base.Exportform_ope(data=form_data)
        r = form.is_valid()
        self.assertTrue(r)
    def test_export_form1bis(self):
        form_data = {'date_min':"01/01/2010",
                   'date_max':"31/12/2013",
                   'collection':(1, 2, 3, 4, 5, 6)
                   }
        form = export_base.Exportform_ope(data=form_data)
        r = form.is_valid()
        self.assertTrue(r)

    def test_export_form2(self):
        form_data = {'date_min':"01/01/2010",
                   'date_max':"31/12/2013",
                   'collection':(1, 2, 3, 6)
                   }
        form = export_base.Exportform_ope(data=form_data)
        r = form.is_valid()
        self.assertTrue(r)
    def test_export_formcours1(self):
        form_data = {'date_min':"01/01/2010",
                   'date_max':"31/12/2013",
                   'collection':(1, 2, 3, 4)
                   }
        form = ex_csv.Exportform_cours(data=form_data)
        r = form.is_valid()
        self.assertTrue(r)
    def test_export_formcpt_titre1(self):
        form_data = {'date_min':"01/01/2010",
                   'date_max':"31/12/2013",
                   'collection':(4, 5)
                   }
        form = ex_csv.Exportform_Compte_titre(data=form_data)
        r = form.is_valid()
        self.assertTrue(r)

    def test_export_formcpt_titre2(self):
        form_data = {'date_min':"01/01/2010",
                   'date_max':"31/12/2013",
                   'collection':(4, 6)
                   }
        form = ex_csv.Exportform_Compte_titre(data=form_data)
        r = form.is_valid()
        self.assertFalse(r)

    def test_sql_money_iphone(self):
        # on cree ce les entree de la vue
        reponse_recu = self.client.post(reverse('export_sql_money_iphone'),
                                         data={'collection':(1, 2, 3, 4, 5, 6), "date_min": "2011-01-01", "date_max": "2012-09-24"}
                                         ).content
        # print len(reponse_recu)
        chaine1 = r'INSERT INTO "category" VALUES\(68,\'placement\',2,13369344,8,\d+.\d+\);'
        chaine2 = 'INSERT INTO "category" VALUES(68,\'placement\',2,13369344,8,1375886177.0);'
        reponse_recu = re.sub(chaine1, chaine2, reponse_recu)
        reponse_attendu = """BEGIN TRANSACTION;
CREATE TABLE account (id INTEGER PRIMARY KEY,
                    name TEXT,
                    place INTEGER
                    , lastupdate DOUBLE);
INSERT INTO "account" VALUES(1,'account.name1',0,NULL);
CREATE TABLE budget (id INTEGER PRIMARY KEY,
                    month INTEGER,
                    year INTEGER,
                    amount    Double
                , lastupdate DOUBLE);
INSERT INTO "budget" VALUES(1,8,2011,0.0,1312149600.0);
INSERT INTO "budget" VALUES(2,9,2011,0.0,1314828000.0);
INSERT INTO "budget" VALUES(3,10,2011,0.0,1317420000.0);
INSERT INTO "budget" VALUES(4,11,2011,0.0,1320102000.0);
INSERT INTO "budget" VALUES(5,12,2011,0.0,1322694000.0);
INSERT INTO "budget" VALUES(6,1,2012,0.0,1325372400.0);
INSERT INTO "budget" VALUES(7,2,2012,0.0,1328050800.0);
INSERT INTO "budget" VALUES(8,3,2012,0.0,1330556400.0);
INSERT INTO "budget" VALUES(9,4,2012,0.0,1333231200.0);
INSERT INTO "budget" VALUES(10,5,2012,0.0,1335823200.0);
INSERT INTO "budget" VALUES(11,6,2012,0.0,1338501600.0);
INSERT INTO "budget" VALUES(12,7,2012,0.0,1341093600.0);
INSERT INTO "budget" VALUES(13,8,2012,0.0,1343772000.0);
INSERT INTO "budget" VALUES(14,9,2012,0.0,1346450400.0);
CREATE TABLE category (
    id INTEGER PRIMARY KEY,
    name TEXT,
    type INTEGER,
    color INTEGER,
    place INTEGER,
    lastupdate DOUBLE);
INSERT INTO "category" VALUES(1,'cat1',1,35840,5,1369245100.0);
INSERT INTO "category" VALUES(2,'cat2',1,35840,6,1369245100.0);
INSERT INTO "category" VALUES(3,'cat3',2,13369344,7,1369245100.0);
INSERT INTO "category" VALUES(64,'Operation Sur Titre',2,13369344,1,1369245100.0);
INSERT INTO "category" VALUES(65,'Virement',2,13369344,4,1369245100.0);
INSERT INTO "category" VALUES(66,'Opération Ventilée',2,13369344,2,1369245100.0);
INSERT INTO "category" VALUES(67,'Revenus de placement:Plus-values',2,13369344,3,1369245100.0);
INSERT INTO "category" VALUES(68,'placement',2,13369344,8,1375886177.0);
CREATE TABLE subcategory (
    id INTEGER PRIMARY KEY,
    category INTEGER,
    name TEXT,
    place INTEGER,
    lastupdate DOUBLE);
CREATE TABLE currency (
    id INTEGER PRIMARY KEY,
    name TEXT,
    sign TEXT,
    decimal INTEGER,
    lastupdate DOUBLE);
INSERT INTO "currency" VALUES(1,'Dollar','$',2,'');
INSERT INTO "currency" VALUES(2,'Euro','EUR',2,'');
CREATE TABLE payment (
    id INTEGER PRIMARY KEY,
    name TEXT,
    symbol INTEGER,
    color INTEGER,
    place INTEGER,
    lastupdate DOUBLE);
INSERT INTO "payment" VALUES(1,'cpte1',4,35840,4,1369245100.0);
INSERT INTO "payment" VALUES(2,'cptb2',2,35840,2,1369245100.0);
INSERT INTO "payment" VALUES(3,'cptb3',3,35840,3,1369245100.0);
INSERT INTO "payment" VALUES(6,'cpt_ferme',1,35840,1,1369245100.0);
CREATE TABLE record (
    id INTEGER PRIMARY KEY,
    payment INTEGER,
    category INTEGER,
    subcategory INTEGER,
    memo TEXT,
    currency INTEGER,
    amount FLOAT,
    date DOUBLE,
    photo INTEGER,
    voice INTEGER,
    payee TEXT,
    note TEXT,
    account INTEGER,
    type INTEGER,
    repeat INTEGER,
    place INTEGER,
    lastupdate DOUBLE,
    day INTEGER);
INSERT INTO "record" VALUES(4,1,1,NULL,'tiers1',2,-100.0,'2011-08-11',0,0,NULL,'',0,2,0,1,20110811.0,1369245100);
INSERT INTO "record" VALUES(5,1,2,NULL,'tiers1',2,10.0,'2011-08-11',0,0,NULL,'',0,1,0,3,20110811.0,1369245100);
INSERT INTO "record" VALUES(6,1,2,NULL,'tiers2',2,10.0,'2011-08-21',0,0,NULL,'',0,1,0,4,20110821.0,1369245100);
INSERT INTO "record" VALUES(7,1,1,NULL,'tiers1',2,10.0,'2011-08-11',0,0,NULL,'',0,1,0,5,20110811.0,1369245100);
INSERT INTO "record" VALUES(8,1,65,NULL,'virement',2,-100.0,'2011-10-30',0,0,NULL,'',0,2,0,6,20111030.0,1369245100);
INSERT INTO "record" VALUES(9,3,65,NULL,'virement',2,100.0,'2011-10-30',0,0,NULL,'',0,2,0,2,20111030.0,1369245100);
INSERT INTO "record" VALUES(12,1,1,NULL,'tiers2',2,99.0,'2012-09-24',0,0,NULL,'',0,1,0,7,20120924.0,1369245100);
INSERT INTO "record" VALUES(13,1,2,NULL,'tiers2',2,1.0,'2012-09-24',0,0,NULL,'',0,1,0,8,20120924.0,1369245100);
CREATE INDEX budget_month_index on budget(month);
CREATE INDEX record_day_index on record(day);
CREATE INDEX record_repeat_index on record(repeat);
COMMIT;
"""
        # on coupe ligne par ligne
        ra_iter = reponse_attendu.split('\n')
        rr_iter = reponse_recu.split('\n')
        self.assertEqual(len(ra_iter), len(rr_iter))
        for ra, rr in zip(ra_iter, rr_iter):
            self.assertEqual(ra, rr)
        # erreur
"""
    def test_csv_erreur(self):
        rep = self.client.post(reverse('export_csv'), data={"compte": 2, "date_min": "2011-01-01", "date_max": "2011-02-01"})
        self.assertFormError(rep, 'form', '', u"attention pas d'opérations pour la selection demandée")
"""
