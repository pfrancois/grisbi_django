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

        # erreur
"""        
    def test_csv_erreur(self):
        rep = self.client.post(reverse('export_csv'), data={"compte": 2, "date_min": "2011-01-01", "date_max": "2011-02-01"})
        self.assertFormError(rep, 'form', '', u"attention pas d'opérations pour la selection demandée")
"""
