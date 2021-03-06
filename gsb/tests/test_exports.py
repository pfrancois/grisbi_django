# -*- coding: utf-8 -*
"""
Created on 25 mars 2013
@author: francois
"""


from django.test import RequestFactory
from django.core.urlresolvers import reverse
#from django.conf import settings
from django.utils.encoding import smart_text

from gsb.io import export_base
import gsb.io.export_csv as ex_csv

from .. import models
from .. import utils

from .test_view import Test_view_base

__all__ = ['Test_export']


class Test_export(Test_view_base):

    def test_csv_global(self):
        # on recupere un compte
        models.Virement.create(compte_origine=models.Compte.objects.get(nom='cpte1'),
                               compte_dest=models.Compte.objects.get(nom='cptb3'),
                               montant=100,
                               date=utils.strpdate("18/12/2012", fmt='%d/%m/%Y'))
        o = models.Ope.objects.get(id=15)
        o.rapp = models.Rapp.objects.get(id=1)
        o.save()
        models.Virement.create(compte_origine=models.Compte.objects.get(nom='cpte1'),
                               compte_dest=models.Compte.objects.get(nom='cptb3'),
                               montant=100,
                               date=utils.strpdate("18/12/2013", fmt='%d/%m/%Y'))
        o = models.Ope.objects.get(id=17)
        o.pointe = True
        o.save()
        # on rapproche l'ope mere
        ope_mere = models.Ope.objects.get(id=11)
        ope_mere.rapp = models.Rapp.objects.get(id=1)
        ope_mere.save()
        rep = self.client.post(reverse('export_csv'), data={'collection': (1, 2, 3, 4, 5, 6), "date_min": "2011-01-01", "date_max": "2014-09-24"})
        reponse_attendu = """id;cpt;date;date_val;montant;r;p;moyen;cat;tiers;notes;ib;num_cheque\r
4;cpte1;11/08/2011;;-100,00;cpte1201101;0;moyen_dep1;cat1;tiers1;;;\r
5;cpte1;11/08/2011;;10,00;cpte1201101;0;moyen_rec1;cat2;tiers1;;;\r
7;cpte1;11/08/2011;;10,00;;1;moyen_rec1;cat1;tiers1;;ib1;\r
6;cpte1;21/08/2011;;10,00;;0;moyen_rec1;cat2;tiers2;fusion avec ope1;ib2;\r
3;cpt_titre2;29/10/2011;;-100,00;cpt_titre2201101;0;moyen_dep3;Opération sur titre;titre_ t2;20@5;;\r
8;cpte1;30/10/2011;;-100,00;;0;moyen_vir4;Virement;cpte1 => cptb3;;;\r
9;cptb3;30/10/2011;;100,00;;0;moyen_vir4;Virement;cpte1 => cptb3;;;\r
2;cpt_titre2;30/11/2011;;-1500,00;;0;moyen_dep3;Opération sur titre;titre_ t2;150@10;;\r
1;cpt_titre1;18/12/2011;;-1,00;;0;moyen_dep2;Opération sur titre;titre_ t1;1@1;;\r
10;cpt_titre1;24/09/2012;;-5,00;;0;moyen_dep2;Opération sur titre;titre_ autre;5@1;;\r
12;cpte1;24/09/2012;;99,00;cpte1201101;0;moyen_rec1;cat1;tiers2;;;\r
13;cpte1;24/09/2012;;1,00;cpte1201101;0;moyen_rec1;cat2;tiers2;;;\r
14;cpte1;18/12/2012;;-100,00;;0;moyen_vir4;Virement;cpte1 => cptb3;>Rcpte1201101;;\r
15;cptb3;18/12/2012;;100,00;cpte1201101;0;moyen_vir4;Virement;cpte1 => cptb3;;;\r
16;cpte1;18/12/2013;;-100,00;;0;moyen_vir4;Virement;cpte1 => cptb3;>P;;\r
17;cptb3;18/12/2013;;100,00;;1;moyen_vir4;Virement;cpte1 => cptb3;;;\r
"""
        # on coupe ligne par ligne
        reponse_recu = smart_text(rep.content, 'latin-1')
        self.assertreponsequal(reponse_recu, reponse_attendu, nom="csv_global")

    def test_csv_debug(self):
        # on cree ce les entree de la vue
        req = RequestFactory()
        request = req.post(reverse('export_csv'),
                           data={'collection': (1, 2, 3, 4, 5, 6), "date_min": "2011-01-01", "date_max": "2012-09-24"})
        # initialisation de la vue
        view = self.setup_view(ex_csv.Export_ope_csv(), request)
        # choix des parametre du test proprement dit
        view.debug = True
        # de la ligne d'export
        data = "4;cpte1;11/08/2011;;-100,00;cpte1201101;0;moyen_dep1;cat1;tiers1;;;".split(";")
        header = view.fieldnames
        final = dict()
        for d, h in zip(data, header):
            final[h] = d
            # on compare a ce qui est attendu
        reponse_attendu = """id;cpt;date;date_val;montant;r;p;moyen;cat;tiers;notes;ib;num_cheque\r
4;cpte1;11/08/2011;;-100,00;cpte1201101;0;moyen_dep1;cat1;tiers1;;;\r
"""
        reponse_recu = smart_text(view.export_csv_view(data=[final]).content, encoding='cp1252')
        self.assertreponsequal(reponse_recu, reponse_attendu, nom="csv_debug")

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
        self.assertTrue(form.errors['__all__'] != "attention pas d'opérations pour la selection demandée")

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

    def test_export_cours(self):
        reponse_recu = smart_text(self.client.post(reverse('export_cours'),
                                                   data={'collection': (1, 2, 3, 4, 5),
                                                         "date_min": "2011-01-01",
                                                         "date_max": "2012-09-24"}
                                                   ).content, encoding='cp1252')

        reponse_attendu = """id;date;nom;isin;cours
1;24/09/2012;autre;a;1,0000000
5;23/09/2012;autre 2;svjkdfkjh;2,0000000
2;18/12/2011;t1;1;1,0000000
3;29/10/2011;t2;2;5,0000000
3;30/11/2011;t2;2;10,0000000
"""
        self.assertreponsequal(reponse_recu, reponse_attendu, nom="test_export_cours")

    def test_export_ope_titre(self):
        c = models.Compte.objects.get(id=5)
        t = models.Titre.objects.get(nom='t2')
        c.vente(titre=t, nombre=10, prix=20, date="2011-12-01")
        reponse_recu = smart_text(self.client.post(reverse('export_ope_titre'),
                                                   data={'collection': (4, 5),
                                                         "date_min": "2011-01-01",
                                                         "date_max": "2012-09-24"}
                                                   ).content, encoding='cp1252')

        reponse_attendu = """id;date;compte;nom;isin;sens;nombre;cours;montant_ope
1;18/12/2011;cpt_titre1;t1;1;achat;1,0000000;1,0000000;1,0000000
4;24/09/2012;cpt_titre1;autre;a;achat;5,0000000;1,0000000;5,0000000
3;29/10/2011;cpt_titre2;t2;2;achat;20,0000000;5,0000000;100,0000000
2;30/11/2011;cpt_titre2;t2;2;achat;150,0000000;10,0000000;1500,0000000
5;01/12/2011;cpt_titre2;t2;2;vente;-10,0000000;20,0000000;-200,0000000
"""
        self.assertreponsequal(reponse_recu, reponse_attendu, nom="test_export_ope_titre")
