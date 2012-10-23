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
import gsb.utils as utils
import sys
import mock
import datetime
import logging


class Test_view_base(TestCase):
    fixtures = ['test.json', 'auth.json']

    def setUp(self):
        super(Test_view_base, self).setUp()
        self.client.login(username='admin', password='mdp')


class Test_urls(Test_view_base):
    def test_import(self):
        self.assertEqual(self.client.get('/import_csv').status_code, 200)

    def test_404(self):
        self.assertEqual(self.client.get('/ope/2200/').status_code, 404)
        self.assertEqual(self.client.get('/gestion_bdd/gsb/ope/49810/').status_code, 404)

    def test_normaux(self):
        self.assertEqual(self.client.get('/').status_code, 200)
        self.assertEqual(self.client.get('/gestion_bdd/doc/').status_code, 200)
        self.assertEqual(self.client.get('/login').status_code, 200)

    def test_normaux2(self):
        self.assertEqual(self.client.get('/options').status_code, 200)
        self.assertEqual(self.client.get(reverse('export_cours')).status_code, 200)
        self.assertEqual(self.client.get('/options/import').status_code, 200)
        self.assertEqual(self.client.get('/options/verif_config').status_code, 200)
        self.assertEqual(self.client.get(reverse('export_gsb_050')).status_code, 200)
        self.assertEqual(self.client.get(reverse('export_csv')).status_code, 200)
        self.assertEqual(self.client.get(reverse('export_qif')).status_code, 200)
        self.assertEqual(self.client.get('/options/export_autres').status_code, 200)
        self.assertEqual(self.client.get(reverse('export_ope_titre')).status_code, 200)

    @mock.patch('gsb.utils.today')
    def test_echeance(self, today_mock):
        today_mock.return_value = datetime.date(2010, 1, 1)
        self.assertEqual(self.client.get('/options/ech').status_code, 200)

    def test_normaux3(self):
        self.assertEqual(self.client.get('/maj_cours/1').status_code, 200)
        self.assertEqual(self.client.get(reverse('gsb_cpt_detail', args=(1, ))).status_code, 200)
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


class Test_export(Test_view_base):
    def test_csv1(self):
        logger = logging.getLogger('gsb')
        logger.setLevel(40)  # change le niveau de log (10 = debug, 20=info)
        rep = self.client.post(reverse('export_csv'),
                               data={"compte": 1, "date_min": "2011-01-01", "date_max": "2012-09-24"})
        self.assertEqual(rep.content,
                         'id;account name;date;montant;p;m;moyen;cat;tiers;notes;projet;n chq;id jumelle lie;fille;num op vent m;mois\r\n4;cpte1;11/8/2011;-100,0000000;1;0;moyen_dep1;(r)cat1;tiers1;;;;;0;;2011_08\r\n5;cpte1;11/8/2011;10,0000000;1;0;moyen_rec1;(r)cat2;tiers1;;;;;0;;2011_08\r\n7;cpte1;11/8/2011;10,0000000;0;1;moyen_rec1;(r)cat1;tiers1;;ib1;;;0;;2011_08\r\n6;cpte1;21/8/2011;10,0000000;0;0;moyen_rec1;(r)cat2;tiers2;fusion avec ope1;ib2;;;0;;2011_08\r\n3;cpt_titre2;29/10/2011;-100,0000000;1;0;moyen_dep3;(d)Operation Sur Titre;titre_ t2;20@5;;;;0;;2011_10\r\n8;cpte1;30/10/2011;-100,0000000;0;0;moyen_vir4;(d)Virement;Virement;;;;9;0;;2011_10\r\n9;cptb3;30/10/2011;100,0000000;0;0;moyen_vir4;(d)Virement;Virement;;;;8;0;;2011_10\r\n2;cpt_titre2;30/11/2011;-1500,0000000;0;0;moyen_dep3;(d)Operation Sur Titre;titre_ t2;150@10;;;;0;;2011_11\r\n1;cpt_titre1;18/12/2011;-1,0000000;0;0;moyen_dep2;(d)Operation Sur Titre;titre_ t1;1@1;;;;0;;2011_12\r\n10;cpt_titre1;24/9/2012;-5,0000000;0;0;moyen_dep2;(d)Operation Sur Titre;titre_ autre;5@1;;;;0;;2012_09\r\n11;cpte1;24/9/2012;100,0000000;0;0;moyen_rec1;(d)Op\xe9ration Ventil\xe9e;tiers2;;;;;0;;2012_09\r\n')
        #erreur
        rep = self.client.post(reverse('export_csv'),
                               data={"compte": 2, "date_min": "2011-01-01", "date_max": "2011-02-01"})
        self.assertFormError(rep, 'form', '', u"attention pas d'opérations pour la selection demandée")


class Test_views_general(Test_view_base):
    def test_view_index(self):
        resp = self.client.get('/')
        self.assertEqual(resp.context['titre'], 'liste des comptes')
        self.assertQueryset(resp.context['liste_cpt_bq'], [1, 2, 3])
        self.assertQueryset(resp.context['liste_cpt_pl'], [4, 5])
        self.assertEqual(resp.context['total_bq'], 30)
        self.assertEqual(resp.context['total_pla'], 100)
        self.assertEqual(resp.context['total'], 130)
        self.assertEqual(resp.context['nb_clos'], 1)

        #@mock.patch('gsb.utils.today')
    def test_view_cpt_detail(self):
        #today_mock.return_value=datetime.date(2012, 10, 14)
        resp = self.client.get(reverse('gsb_cpt_detail', args=(1, )))
        self.assertTemplateUsed(resp, template_name="gsb/cpt_detail.djhtm")
        self.assertEqual(resp.context['titre'], 'cpte1')
        self.assertEqual(resp.context['compte'].id, 1)
        self.assertEqual(resp.context['nbrapp'], 2)
        self.assertEqual(resp.context['solde'], -70)
        self.assertEqual(resp.context['date_r'], utils.strpdate('2011-08-12'))
        self.assertEqual(resp.context['solde_r'], -90)
        self.assertEqual(resp.context['solde_p'], 10)
        self.assertEqual(resp.context['solde_pr'], -80)
        self.assertQueryset(resp.context['list_ope'], [6, 7, 8, 12, 13])

    def test_view_cpt_detail_rapp(self):
        resp = self.client.get(reverse('gsb_cpt_detail_rapp', args=(1, )))
        self.assertTemplateUsed(resp, template_name="gsb/cpt_detail.djhtm")
        self.assertEqual(resp.context['titre'], 'cpte1')
        self.assertEqual(resp.context['compte'].id, 1)
        self.assertEqual(resp.context['nbrapp'], 0)
        self.assertEqual(resp.context['solde'], -70)
        self.assertEqual(resp.context['date_r'], utils.strpdate('2011-08-12'))
        self.assertEqual(resp.context['solde_r'], -90)
        self.assertEqual(resp.context['solde_p'], 10)
        self.assertEqual(resp.context['solde_pr'], -80)
        self.assertQueryset(resp.context['list_ope'], [4, 5])

    def test_view_cpt_detail_all(self):
        resp = self.client.get(reverse('gsb_cpt_detail_all', args=(1, )))
        self.assertTemplateUsed(resp, template_name="gsb/cpt_detail.djhtm")
        self.assertEqual(resp.context['titre'], 'cpte1')
        self.assertEqual(resp.context['compte'].id, 1)
        self.assertEqual(resp.context['nbrapp'], 0)
        self.assertEqual(resp.context['solde'], -70)
        self.assertEqual(resp.context['date_r'], utils.strpdate('2011-08-12'))
        self.assertEqual(resp.context['solde_r'], -90)
        self.assertEqual(resp.context['solde_p'], 10)
        self.assertEqual(resp.context['solde_pr'], -80)
        self.assertQueryset(resp.context['list_ope'], [4, 5, 6, 7, 8, 12, 13])

    def test_view_cpt_espece(self):
        resp = self.client.get(reverse('gsb_cpt_titre_espece', args=(5, )))
        self.assertTemplateUsed(resp, template_name="gsb/cpt_placement_espece.djhtm")
        self.assertEqual(resp.context['titre'], 'cpt_titre2')
        self.assertEqual(resp.context['compte'].id, 5)
        self.assertEqual(resp.context['nbrapp'], 1)
        self.assertEqual(resp.context['solde'], -1600)
        self.assertEqual(resp.context['date_r'], utils.strpdate('2011-10-30'))
        self.assertEqual(resp.context['solde_r'], -100)
        self.assertEqual(resp.context['solde_p'], 0)
        self.assertEqual(resp.context['solde_pr'], -100)
        self.assertQueryset(resp.context['list_ope'], [2, ])

    def test_view_cpt_especes_all(self):
        resp = self.client.get(reverse('gsb_cpt_titre_espece_all', args=(5, )))
        self.assertTemplateUsed(resp, template_name="gsb/cpt_placement_espece.djhtm")
        self.assertEqual(resp.context['titre'], 'cpt_titre2')
        self.assertEqual(resp.context['titre_long'], u'cpt_titre2 (Ensemble des opérations)')
        self.assertEqual(resp.context['compte'].id, 5)
        self.assertEqual(resp.context['nbrapp'], 0)
        self.assertEqual(resp.context['solde'], -1600)
        self.assertEqual(resp.context['date_r'], utils.strpdate('2011-10-30'))
        self.assertEqual(resp.context['solde_r'], -100)
        self.assertEqual(resp.context['solde_p'], 0)
        self.assertEqual(resp.context['solde_pr'], -100)
        self.assertQueryset(resp.context['list_ope'], [2, 3])

    def test_view_cpt_especes_rapp(self):
        resp = self.client.get(reverse('gsb_cpt_titre_espece_rapp', args=(5, )))
        self.assertTemplateUsed(resp, template_name="gsb/cpt_placement_espece.djhtm")
        self.assertEqual(resp.context['titre'], 'cpt_titre2')
        self.assertEqual(resp.context['titre_long'], u'cpt_titre2 (Opérations rapprochées)')
        self.assertEqual(resp.context['compte'].id, 5)
        self.assertEqual(resp.context['nbrapp'], 0)
        self.assertEqual(resp.context['solde'], -1600)
        self.assertEqual(resp.context['date_r'], utils.strpdate('2011-10-30'))
        self.assertEqual(resp.context['solde_r'], -100)
        self.assertEqual(resp.context['solde_p'], 0)
        self.assertEqual(resp.context['solde_pr'], -100)
        self.assertQueryset(resp.context['list_ope'], [3, ])


class Test_views_ope(Test_view_base):
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
