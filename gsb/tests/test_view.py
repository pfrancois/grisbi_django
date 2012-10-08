# -*- coding: utf-8 -*
"""
test models
"""
from __future__ import absolute_import
from .test_base import TestCase
import decimal
from gsb import forms as gsb_forms
from django.core.urlresolvers import reverse
import os.path
from django.conf import settings
from ..models import Compte
import pprint
class Test_view_base(TestCase):
    fixtures = ['test.json', 'auth.json']

    def setUp(self):
        super(Test_view_base, self).setUp()
        self.client.login(username='admin', password='mdp')


class Test_urls(Test_view_base):
    def test_404(self):
        self.assertEqual(self.client.get('/ope/2200/').status_code, 404)
        self.assertEqual(self.client.get('/gestion_bdd/gsb/ope/49810/').status_code, 404)
        self.assertEqual(self.client.get('/compte/1/especes').status_code, 404)

    def test_normaux(self):
        self.assertEqual(self.client.get('/').status_code, 200)
        self.assertEqual(self.client.get('/gestion_bdd/doc/').status_code, 200)
        self.assertEqual(self.client.get('/login').status_code, 200)

    def test_normaux2(self):
        self.assertEqual(self.client.get('/options').status_code, 200)
        self.assertEqual(self.client.get(reverse('export_cours')).status_code, 200)
        self.assertEqual(self.client.get('/options/import').status_code, 200)
        self.assertEqual(self.client.get('/options/ech').status_code, 200)
        self.assertEqual(self.client.get('/options/verif_config').status_code, 200)
        self.assertEqual(self.client.get(reverse('export_gsb_050')).status_code, 200)
        self.assertEqual(self.client.get(reverse('export_csv')).status_code, 200)
        self.assertEqual(self.client.get(reverse('export_qif')).status_code, 200)
        self.assertEqual(self.client.get('/options/export_autres').status_code, 200)
        self.assertEqual(self.client.get(reverse('export_ope_titre')).status_code, 200)

    def test_normaux3(self):
        self.assertEqual(self.client.get('/maj_cours/1').status_code, 200)
        self.assertEqual(self.client.get('/ope/1/').status_code, 200)
        self.assertEqual(self.client.get('/ope/1/delete').status_code, 302)
        self.assertEqual(self.client.get('/ope/new').status_code, 200)
        self.assertEqual(self.client.get('/vir/new').status_code, 200)
        self.assertEqual(self.client.get('/ope_titre/1/').status_code, 200)
        self.assertEqual(self.client.get('/ope_titre/1/delete').status_code, 302)
        self.assertEqual(self.client.get('/search').status_code, 200)

    def test_normaux4(self):
        self.assertEqual(self.client.get('/compte/1/').status_code, 200)
        self.assertEqual(self.client.get('/compte/1/rapp').status_code, 200)
        self.assertEqual(self.client.get('/compte/1/all').status_code, 200)
        self.assertEqual(self.client.get('/compte/1/new').status_code, 200)
        self.assertEqual(self.client.get('/compte/4/especes/all').status_code, 200)
        self.assertEqual(self.client.get('/compte/4/especes/rapp').status_code, 200)
        self.assertEqual(self.client.get('/compte/4/titre/1').status_code, 200)
        self.assertEqual(self.client.get('/compte/4/titre/1/all').status_code, 200)
        self.assertEqual(self.client.get('/compte/4/titre/1/rapp').status_code, 200)
        self.assertEqual(self.client.get('/compte/4/achat').status_code, 200)
        self.assertEqual(self.client.get('/compte/4/vente').status_code, 200)
        self.assertEqual(self.client.get('/compte/4/maj').status_code, 200)


class Test_export_csv(Test_view_base):
    def test1(self):
        rep=self.client.post(reverse('export_csv'),data={"compte":1,"date_min":"2011-01-01","date_max":"2012-09-24"})
        self.assertEqual(rep.content,"'id;account name;date;montant;p;m;moyen;cat;tiers;notes;projet;n chq;id jumelle lie;fille;num op vent m;mois\r\n4;cpte1;11/8/2011;-100,0000000;1;0;moyen_dep1;(r)cat1;tiers1;;;;;0;;2011_08\r\n5;cpte1;11/8/2011;10,0000000;1;0;moyen_rec1;(r)cat2;tiers1;;;;;0;;2011_08\r\n7;cpte1;11/8/2011;10,0000000;0;1;moyen_rec1;(r)cat1;tiers1;;ib1;;;0;;2011_08\r\n6;cpte1;21/8/2011;10,0000000;0;0;moyen_rec1;(r)cat2;tiers2;fusion avec ope1;ib2;;;0;;2011_08\r\n3;cpt_titre2;29/10/2011;-100,0000000;1;0;moyen_dep3;(d)Operation Sur Titre;titre_t2;20@5;;;;0;;2011_10\r\n8;cpte1;30/10/2011;-100,0000000;0;0;moyen_vir4;(d)Virement;Virement;;;;9;0;;2011_10\r\n9;cptb3;30/10/2011;100,0000000;0;0;moyen_vir4;(d)Virement;Virement;;;;8;0;;2011_10\r\n2;cpt_titre2;30/11/2011;-1500,0000000;0;0;moyen_dep3;(d)Operation Sur Titre;titre_ t2;150@10;;;;0;;2011_11\r\n1;cpt_titre1;18/12/2011;-1,0000000;0;0;moyen_dep2;(d)Operation Sur Titre;titre_t1;1@1;;;;0;;2011_12\r\n10;cpt_titre1;24/9/2012;-5,0000000;0;0;moyen_dep2;(d)Operation Sur Titre;titre_ autre;5@1;;;;0;;2012_09\r\n11;cpte1;24/9/2012;100,0000000;0;0;moyen_rec1;(d)Op\xe9rationVentil\xe9e;tiers2;;;;;0;;2012_09\r\n12;cpte1;24/9/2012;99,0000000;0;0;moyen_rec1;(r)cat1;tiers2;;;;;1;11;2012_09\r\n13;cpte1;24/9/2012;1,0000000;0;0;moyen_rec1;(r)cat2;tiers2;;;;;1;11;2012_09\r\n'")

class Test_import_csv(Test_view_base):
    def test(self):
        with open(os.path.join(settings.PROJECT_PATH,'gsb','test_files','export_ope_07_10_2012-21_18_25.csv')) as fp:
            self.client.post(reverse('import_csv'),data={'attachment': fp})



class Test_views(Test_view_base):
    def test_form_ope_normal(self):
        form_data = {'compte': "1",
                     'date': "02/09/2012",
                     'date_val': "",
                     'montant': decimal.Decimal(24),
                     'tiers': "1",
                     'cat': "3",
                     "notes": "",
                     'moyen': "1",
                     "num_cheque": "",
                     'rapp': "",
                     "exercice": "",
                     "ib": "",
                     "piece_comptable": "",
                     "nouveau_tiers": "",
                     "operation_mere": "",
        }
        form = gsb_forms.OperationForm(data=form_data, initial=form_data)
        r = form.is_valid()
        self.assertTrue(r)
        r = form.cleaned_data['montant']
        self.assertEqual(r, decimal.Decimal(-24))

    def test_form_ope_clean(self):
        """pas de tiers  ni de nouveau tiers"""
        form_data = {'compte': "1",
                     'date': "02/09/2012",
                     'date_val': "",
                     'montant': "24",
                     'tiers': "",
                     'cat': "3",
                     "notes": "",
                     'moyen': "1",
                     "num_cheque": "",
                     'rapp': "",
                     "exercice": "",
                     "ib": "",
                     "piece_comptable": "",
                     "nouveau_tiers": "",
                     "operation_mere": "",
        }
        form = gsb_forms.OperationForm(data=form_data)
        self.assertEqual(form.is_valid(), False)
        form.is_valid()
        self.assertEqual(form._errors, {'nouveau_tiers':
                                            [u'si vous ne choisissez pas un tiers, vous devez taper le nom du nouveau'],
                                        'tiers':
                                            [
                                                u"si vous ne choisissez pas un tiers, vous devez taper le nom du nouveau dans le champs 'nouveau tiers'"]})
