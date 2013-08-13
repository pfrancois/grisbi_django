# -*- coding: utf-8 -*
'''
Created on 25 mars 2013

@author: francois
'''

from __future__ import absolute_import
from django.test import RequestFactory
from django.core.urlresolvers import reverse
from gsb.io import export_base
import gsb.io.export_csv as ex_csv
import logging
from .. import models
from .. import utils

import re
from .test_view import Test_view_base

__all__ = ['Test_export']


class Test_export(Test_view_base):
    def test_csv_global(self):
        logger = logging.getLogger('gsb')
        logger.setLevel(40)  # change le niveau de log (10 = debug, 20=info)
        rep = self.client.post(reverse('export_csv'), data={'collection': (1, 2, 3, 4, 5, 6), "date_min": "2011-01-01", "date_max": "2012-09-24"})
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
        # on coupe ligne par ligne
        self.assertreponsequal(rep.content, reponse_attendu, unicode_encoding='cp1252', nom="csv_global")

    def test_csv_debug(self):
        # on cree ce les entree de la vue
        req = RequestFactory()
        request = req.post(reverse('export_csv'), data={'collection': (1, 2, 3, 4, 5, 6), "date_min": "2011-01-01", "date_max": "2012-09-24"})
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
        reponse_attendu = u"""id;cpt;date;montant;r;p;moyen;cat;tiers;notes;projet;numchq;id jumelle lie;has_fille;id_ope_m;ope_titre;ope_pmv;mois\r
4;cpte1;11/08/2011;-100,00;cpte1201101;0;moyen_dep1;cat1;tiers1;;;;;0;;;;08\r
"""
        self.assertreponsequal(view.export_csv_view(data=[final], nomfich='test_file').content, reponse_attendu, unicode_encoding='cp1252', nom="csv_debug")

    def test_export_form1(self):
        # test normal avec aucune selection
        form_data = {'date_min': "01/01/2010",
                   'date_max': "31/12/2013",
                   'collection': ""
                   }
        form = export_base.Exportform_ope(data=form_data)
        r = form.is_valid()
        self.assertTrue(r)

    def test_export_form1bis(self):
        # test normal avec selection de tous comptes
        form_data = {'date_min': "01/01/2010",
                   'date_max': "31/12/2013",
                   'collection': (1, 2, 3, 4, 5, 6)
                   }
        form = export_base.Exportform_ope(data=form_data)
        r = form.is_valid()
        self.assertTrue(r)

    def test_export_form2(self):
        # test normal avec selection de certains comptes
        form_data = {'date_min': "01/01/2010",
                   'date_max': "31/12/2013",
                   'collection': (1, 2, 3, 6)
                   }
        form = export_base.Exportform_ope(data=form_data)
        r = form.is_valid()
        self.assertTrue(r)

    def test_export_form3(self):
        # test normal avec aucune operation
        form_data = {'date_min': "01/01/2013",
                   'date_max': "31/12/2013",
                   'collection': (1, 2, 3, 6)
                   }
        form = export_base.Exportform_ope(data=form_data)
        r = form.is_valid()
        self.assertFalse(r)
        self.assert_(form.errors['__all__'] != u"attention pas d'opérations pour la selection demandée")

    def test_export_formcours1(self):
        form_data = {'date_min': "01/01/2010",
                   'date_max': "31/12/2013",
                   'collection': (1, 2, 3, 4)
                   }
        form = ex_csv.Exportform_cours(data=form_data)
        r = form.is_valid()
        self.assertTrue(r)

    def test_export_formcpt_titre1(self):
        form_data = {'date_min': "01/01/2010",
                   'date_max': "31/12/2013",
                   'collection': (4, 5)
                   }
        form = ex_csv.Exportform_Compte_titre(data=form_data)
        r = form.is_valid()
        self.assertTrue(r)

    def test_export_formcpt_titre2(self):
        form_data = {'date_min': "01/01/2010",
                   'date_max': "31/12/2013",
                   'collection': (4, 6)
                   }
        form = ex_csv.Exportform_Compte_titre(data=form_data)
        r = form.is_valid()
        self.assertFalse(r)

    def test_sql_money_iphone(self):
        # on cree ce les entree de la vue
        reponse_recu = self.client.post(reverse('export_sql_money_iphone'),
                                         data={'collection': (1, 2, 3, 4, 5, 6), "date_min": "2011-01-01", "date_max": "2012-09-24"}
                                         ).content
        # on remplace pour que ca marche 'version special du mock'
        chaine1 = r'INSERT INTO "category" VALUES\(68,\'placement\',2,13369344,8,\d+.\d+\);'
        chaine2 = 'INSERT INTO "category" VALUES(68,\'placement\',2,13369344,8,1375886177.0);'
        reponse_recu = re.sub(chaine1, chaine2, reponse_recu)

        # on coupe ligne par ligne
        self.assertfileequal(reponse_recu, "money_iphone.txt", nom="csv_sql_money_iphone")

    def test_csv_pocket_money_iphone(self):
        reponse_recu = self.client.post(reverse('export_csv_pocket_money'),
                                        data={'collection': (1, 2, 3, 4, 5, 6), "date_min": "2011-01-01", "date_max": "2012-09-24"}
                                         ).content

        reponse_attendu = """"account name","date","ChkNum","Payee","Category","Class","Memo","Amount","Cleared","CurrencyCode","ExchangeRate"
"cpte1","11/8/11","","tiers1","cat1","","","-100.00","*","EUR","1"
"cpte1","11/8/11","","tiers1","cat2","","","10.00","*","EUR","1"
"cpte1","11/8/11","","tiers1","cat1","ib1","","10.00","","EUR","1"
"cpte1","21/8/11","","tiers2","cat2","ib2","fusion avec ope1","10.00","","EUR","1"
"cpt_titre2","29/10/11","","titre_ t2","Operation Sur Titre","","20@5","-100.00","*","EUR","1"
"cpte1","30/10/11","","<cptb3>","Virement","","","-100.00","","EUR","1"
"cptb3","30/10/11","","<cpte1>","Virement","","","100.00","","EUR","1"
"cpt_titre2","30/11/11","","titre_ t2","Operation Sur Titre","","150@10","-1500.00","","EUR","1"
"cpt_titre1","18/12/11","","titre_ t1","Operation Sur Titre","","1@1","-1.00","","EUR","1"
"cpt_titre1","24/9/12","","titre_ autre","Operation Sur Titre","","5@1","-5.00","","EUR","1"
"cpte1","24/9/12","","tiers2","cat1","","","99.00","","EUR","1"
"cpte1","24/9/12","","tiers2","cat2","","","1.00","","EUR","1"
"""
        self.assertreponsequal(reponse_recu, reponse_attendu, nom="test_csv_pocket_money_iphone")

    def test_export_cours(self):
        reponse_recu = self.client.post(reverse('export_cours'),
                                        data={'collection': (1, 2, 3, 4, 5), "date_min": "2011-01-01", "date_max": "2012-09-24"}
                                         ).content

        reponse_attendu = """id;date;nom;isin;cours
1;24/9/2012;autre;a;1,0000000
5;23/9/2012;autre 2;svjkdfkjh;2,0000000
2;18/12/2011;t1;1;1,0000000
3;29/10/2011;t2;2;5,0000000
3;30/11/2011;t2;2;10,0000000
"""
        self.assertreponsequal(reponse_recu, reponse_attendu, nom="test_export_cours")

    def test_export_ope_titre(self):
        c = models.Compte.objects.get(id=5)
        t = models.Titre.objects.get(nom='t2')
        c.vente(titre=t, nombre=10, prix=20, date="2011-12-01")
        reponse_recu = self.client.post(reverse('export_ope_titre'),
                                        data={'collection': (4, 5), "date_min": "2011-01-01", "date_max": "2012-09-24"}
                                         ).content

        reponse_attendu = """id;date;compte;nom;isin;sens;nombre;cours;montant_ope
1;18/12/2011;cpt_titre1;t1;1;achat;1,0000000;1,0000000;1,0000000
4;24/9/2012;cpt_titre1;autre;a;achat;5,0000000;1,0000000;5,0000000
3;29/10/2011;cpt_titre2;t2;2;achat;20,0000000;5,0000000;100,0000000
2;30/11/2011;cpt_titre2;t2;2;achat;150,0000000;10,0000000;1500,0000000
5;1/12/2011;cpt_titre2;t2;2;vente;-10,0000000;20,0000000;-200,0000000
"""
        self.assertreponsequal(reponse_recu, reponse_attendu, nom="test_export_ope_titre")

    def test_export_gsb_0_5_0(self):
        c = models.Compte.objects.create(nom='test')
        models.Ope.objects.create(date=utils.strpdate('2011-08-13'), compte=c, date_val=utils.strpdate('2011-08-13'))
        models.Echeance.objects.create(date=utils.strpdate('2011-08-13'), compte=c, montant= -10, tiers_id=1, cat_id=1, moyen_id=1, intervalle=1, periodicite='j')
        models.Echeance.objects.create(date=utils.strpdate('2011-08-13'), compte=c, montant= -10, tiers_id=1, cat_id=1, moyen_id=1, intervalle=1, periodicite='m')
        models.Echeance.objects.create(date=utils.strpdate('2011-08-13'), compte=c, montant= -10, tiers_id=1, cat_id=1, moyen_id=1, intervalle=1, periodicite='s')
        reponse_recu = self.client.get(reverse('export_gsb_050')).content
        self.assertfileequal(reponse_recu, "export_050.xml", nom="test_gsb")
