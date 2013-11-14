# -*- coding: utf-8 -*
"""
test models
"""
from __future__ import absolute_import
from .test_base import TestCase
import decimal
from gsb import forms as gsb_forms
from django.core.urlresolvers import reverse
# import os.path
# from django.conf import settings
import gsb.utils as utils
import mock
import datetime
from .. import models

__all__ = ['Test_urls', 'Test_views_general', 'Test_forms']


class Test_view_base(TestCase):
    fixtures = ['test.json', 'auth.json']

    def setUp(self):
        super(Test_view_base, self).setUp()
        self.client.login(username='admin', password='mdp')


class Test_urls(Test_view_base):
    def test_404(self):
        self.assertEqual(self.client.get('/gestion_bdd/gsb/ope/49810/').status_code, 404)
"""
a tester ailleurs
    @mock.patch('gsb.utils.today')
    def test_echeance(self, today_mock):
        today_mock.return_value = datetime.date(2010, 1, 1)
        self.assertEqual(self.client.get('/options/ech').status_code, 200)
"""


class Test_views_general(Test_view_base):
    def test_view_index(self):
        """page d'acceuil"""
        resp = self.client.get('/')
        self.assertEqual(resp.context['titre'], 'liste des comptes')
        self.assertEqual(len(resp.context['liste_cpt_bq']), 3)
        self.assertEqual(len(resp.context['liste_cpt_pl']), 2)
        self.assertEqual(resp.context['total_bq'], 30)
        self.assertEqual(resp.context['total_pla'], 100)
        self.assertEqual(resp.context['total'], 130)
        self.assertEqual(resp.context['nb_clos'], 1)

    @mock.patch('gsb.utils.today')
    def test_view_cpt_detail(self, today_mock):
        """vois le detail du compte 1 au 14/10/2012"""
        today_mock.return_value = datetime.date(2012, 10, 14)
        resp = self.client.get(reverse('gsb_cpt_detail', args=(1,)))
        self.assertTemplateUsed(resp, template_name="gsb/cpt_detail.djhtm")
        self.assertEqual(resp.context['titre'], 'cpte1')
        self.assertEqual(resp.context['compte'].id, 1)
        self.assertEqual(resp.context['nbrapp'], 2)
        self.assertEqual(resp.context['solde'], -70)
        self.assertEqual(resp.context['date_r'], utils.strpdate('2011-08-12'))
        self.assertEqual(resp.context['solde_r'], -90)
        self.assertEqual(resp.context['solde_p_pos'], 10)
        self.assertEqual(resp.context['solde_p_neg'], 0)
        self.assertEqual(resp.context['solde_pr'], -80)
        self.assertQueryset_list(resp.context['list_opes'], [8, 12, 13])

    def test_view_cpt_detail_rapp(self):
        """vois le detail des ope rapp du compte 1 """
        resp = self.client.get(reverse('gsb_cpt_detail_rapp', args=(1,)))
        self.assertTemplateUsed(resp, template_name="gsb/cpt_detail.djhtm")
        self.assertEqual(resp.context['titre'], 'cpte1')
        self.assertEqual(resp.context['compte'].id, 1)
        self.assertEqual(resp.context['nbrapp'], 0)
        self.assertEqual(resp.context['solde'], -70)
        self.assertEqual(resp.context['date_r'], utils.strpdate('2011-08-12'))
        self.assertEqual(resp.context['solde_r'], -90)
        self.assertEqual(resp.context['solde_p_pos'], 10)
        self.assertEqual(resp.context['solde_p_neg'], 0)
        self.assertEqual(resp.context['solde_pr'], -80)
        self.assertQueryset_list(resp.context['list_opes'], [4, 5])

    def test_view_cpt_detail_all(self):
        """vois le detail du compte 1 aujourdhui (y compris les ope rapp)"""
        resp = self.client.get(reverse('gsb_cpt_detail_all', args=(1,)))
        self.assertTemplateUsed(resp, template_name="gsb/cpt_detail.djhtm")
        self.assertEqual(resp.context['titre'], 'cpte1')
        self.assertEqual(resp.context['compte'].id, 1)
        self.assertEqual(resp.context['nbrapp'], 0)
        self.assertEqual(resp.context['solde'], -70)
        self.assertEqual(resp.context['date_r'], utils.strpdate('2011-08-12'))
        self.assertEqual(resp.context['solde_r'], -90)
        self.assertEqual(resp.context['solde_p_pos'], 10)
        self.assertEqual(resp.context['solde_p_neg'], 0)
        self.assertEqual(resp.context['solde_pr'], -80)
        self.assertQueryset_list(resp.context['list_opes'], [4, 5, 6, 7, 8, 12, 13])

    @mock.patch('gsb.utils.today')
    def test_view_cpt_espece(self, today_mock):
        """detail du compte espece du compte titre 5 au 14/10/2012"""
        today_mock.return_value = datetime.date(2012, 10, 14)
        resp = self.client.get(reverse('gsb_cpt_titre_espece', args=(5,)))
        self.assertTemplateUsed(resp, template_name="gsb/cpt_placement_espece.djhtm")
        self.assertEqual(resp.context['titre'], 'cpt_titre2')
        self.assertEqual(resp.context['compte'].id, 5)
        self.assertEqual(resp.context['nbrapp'], 1)
        self.assertEqual(resp.context['solde'], -1600)
        self.assertEqual(resp.context['date_r'], utils.strpdate('2011-10-30'))
        self.assertEqual(resp.context['solde_r'], -100)
        self.assertEqual(resp.context['solde_p_pos'], 0)
        self.assertEqual(resp.context['solde_p_neg'], 0)
        self.assertEqual(resp.context['solde_pr'], -100)
        self.assertQueryset_list(resp.context['list_opes'], [2, ])

    def test_view_cpt_especes_all(self):
        """detail du compte espece rapproche ou non du compte titre 5"""
        resp = self.client.get(reverse('gsb_cpt_titre_espece_all', args=(5,)))
        self.assertTemplateUsed(resp, template_name="gsb/cpt_placement_espece.djhtm")
        self.assertEqual(resp.context['titre'], 'cpt_titre2')
        self.assertEqual(resp.context['titre_long'], u'cpt_titre2 (Ensemble des opérations)')
        self.assertEqual(resp.context['compte'].id, 5)
        self.assertEqual(resp.context['nbrapp'], 0)
        self.assertEqual(resp.context['solde'], -1600)
        self.assertEqual(resp.context['date_r'], utils.strpdate('2011-10-30'))
        self.assertEqual(resp.context['solde_r'], -100)
        self.assertEqual(resp.context['solde_p_pos'], 0)
        self.assertEqual(resp.context['solde_p_neg'], 0)
        self.assertEqual(resp.context['solde_pr'], -100)
        self.assertQueryset_list(resp.context['list_opes'], [2, 3])

    def test_view_cpt_especes_rapp(self):
        """detail du compte espece rapproche du compte titre 5 au 14/10/2012"""
        resp = self.client.get(reverse('gsb_cpt_titre_espece_rapp', args=(5,)))
        self.assertTemplateUsed(resp, template_name="gsb/cpt_placement_espece.djhtm")
        self.assertEqual(resp.context['titre'], 'cpt_titre2')
        self.assertEqual(resp.context['titre_long'], u'cpt_titre2 (Opérations rapprochées)')
        self.assertEqual(resp.context['compte'].id, 5)
        self.assertEqual(resp.context['nbrapp'], 0)
        self.assertEqual(resp.context['solde'], -1600)
        self.assertEqual(resp.context['date_r'], utils.strpdate('2011-10-30'))
        self.assertEqual(resp.context['solde_r'], -100)
        self.assertEqual(resp.context['solde_p_pos'], 0)
        self.assertEqual(resp.context['solde_p_neg'], 0)
        self.assertEqual(resp.context['solde_pr'], -100)
        self.assertQueryset_list(resp.context['list_opes'], [3, ])


class Test_forms(Test_view_base):
    def test_form_ope_normal(self):
        """test form nouvel ope sans probleme"""
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
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['compte'].id, 1)
        self.assertEqual(form.cleaned_data['date'], utils.strpdate("2012-09-02"))
        self.assertEqual(form.cleaned_data['montant'], decimal.Decimal(-24))

    def test_form_ope_sans_tiers(self):
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
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors, {'nouveau_tiers': [u'si vous ne choisissez pas un tiers, vous devez taper le nom du nouveau'],
                                       'tiers': [u"si vous ne choisissez pas un tiers, vous devez taper le nom du nouveau dans le champs 'nouveau tiers'"]
                                      }
                         )

    def test_virement_forms(self):
        form_data = {'date': "02/09/2012",
                   'compte_origine': '1',
                   'moyen_origine': '5',
                   'compte_destination': '2',
                   'moyen_destination': '5',
                   'montant': decimal.Decimal("13.50"),
                   'notes': 'ceci est des notes',
                   'pointe': ""

                   }
        form = gsb_forms.VirementForm(data=form_data)
        r = form.is_valid()
        self.assertTrue(r)
        r = form.cleaned_data['montant']
        self.assertEqual(r, decimal.Decimal("13.50"))
        form.save()
        self.assertEqual(models.Ope.objects.count(), 15)

    def test_virement_forms2(self):
        form_data = {'date': "02/09/2012",
                   'compte_origine': '1',
                   'moyen_origine': '5',
                   'compte_destination': '2',
                   'moyen_destination': '5',
                   'montant': decimal.Decimal("13.50"),
                   'notes': 'ceci est des notes',
                   'pointe': ""

                   }
        ope = models.Ope.objects.get(id=8)
        form = gsb_forms.VirementForm(data=form_data, ope=ope)
        r = form.is_valid()
        self.assertTrue(r)
        r = form.cleaned_data['montant']
        self.assertEqual(r, decimal.Decimal("13.50"))
        form.save()
        self.assertEqual(models.Ope.objects.count(), 13)

    def test_virement_forms_erreur(self):
        form_data = {'date': "02/09/2012",
                   'compte_origine': '1',
                   'moyen_origine': '5',
                   'compte_destination': '1',
                   'moyen_destination': '5',
                   'montant': decimal.Decimal("13.50"),
                   'notes': 'ceci est des notes',
                   'pointe': ""

                   }
        form = gsb_forms.VirementForm(data=form_data)
        r = form.is_valid()
        self.assertFalse(r)
        self.assertEqual(form.errors, {'compte_origine': [u"pas possible de faire un virement vers le même compte"],
                                       'compte_destination': [u"pas possible de faire un virement vers le même compte"]
                                      }
                        )

    def test_Ope_titre_addForm1(self):
        form_data = {'date': "02/09/2012",
                   'titre': "1",
                   'compte_titre': '4',
                   'compte_espece': '2',
                   'nombre': '0',
                   'cours': '1.56',
                   'frais': '10'
                   }
        form = gsb_forms.Ope_titre_addForm(data=form_data)
        r = form.is_valid()
        self.assertFalse(r)
        self.assertEqual(form.errors, {'nombre': [u'le nombre de titre ne peut être nul']})

    def test_Ope_titre_addForm3(self):
        form_data = {'date': "02/09/2012",
                   'titre': "1",
                   'compte_titre': '4',
                   'compte_espece': '2',
                   'nombre': '10',
                   'cours': '1.56',
                   'frais': '10'
                   }
        form = gsb_forms.Ope_titre_addForm(data=form_data)
        r = form.is_valid()
        self.assertTrue(r)
        self.assertEqual(form.cleaned_data['frais'], -10)

    def test_Ope_titre_dividendeForm2(self):
        form_data = {'date': "02/09/2012",
                   'titre': "3",
                   'compte_titre': '5',
                   'compte_espece': '2',
                   'montant': '10'
                   }
        cpt_titre = models.Compte.objects.get(id=5)
        form = gsb_forms.Ope_titre_dividendeForm(data=form_data, cpt=cpt_titre)
        r = form.is_valid()
        self.assertTrue(r)

    def test_Ope_titre_dividendeForm3(self):
        form_data = {'date': "02/09/2012",
                   'titre': "1",
                   'compte_titre': '5',
                   'compte_espece': '2',
                   'montant': '10'
                   }
        cpt_titre = models.Compte.objects.get(id=5)
        form = gsb_forms.Ope_titre_dividendeForm(data=form_data, cpt=cpt_titre)
        r = form.is_valid()
        self.assertFalse(r)

    def test_Ope_titre_dividendeForm4(self):
        form_data = {'date': "02/09/2012",
                   'titre': "3",
                   'compte_titre': '5',
                   'compte_espece': '2',
                   'montant': '10'
                   }
        cpt_titre = models.Compte.objects.get(id=1)
        form = gsb_forms.Ope_titre_dividendeForm(data=form_data, cpt=cpt_titre)
        r = form.is_valid()
        self.assertTrue(r)

    def test_Ope_titre_add_achatForm1(self):
        form_data = {'date': "02/09/2012",
                   'titre': "1",
                   'compte_titre': '4',
                   'compte_espece': '2',
                   'nombre': '10',
                   'cours': '1.56',
                   'frais': '10',
                   'nouveau_titre': '',
                   'nouveau_isin': '',
                   }
        form = gsb_forms.Ope_titre_add_achatForm(data=form_data)
        r = form.is_valid()
        self.assertTrue(r)

    def test_Ope_titre_add_achatForm2(self):
        form_data = {'date': "02/09/2012",
                   'titre': "",
                   'compte_titre': '4',
                   'compte_espece': '2',
                   'nombre': '10',
                   'cours': '1.56',
                   'frais': '10',
                   'nouveau_titre': 'ceci est un nouveau titre',
                   'nouveau_isin': '',
                   }
        form = gsb_forms.Ope_titre_add_achatForm(data=form_data)
        r = form.is_valid()
        self.assertTrue(r)

    def test_Ope_titre_add_achatForm3(self):
        form_data = {'date': "02/09/2012",
                   'compte_titre': '4',
                   'compte_espece': '2',
                   'nombre': '10',
                   'cours': '1.56',
                   'frais': '10',
                   }
        form = gsb_forms.Ope_titre_add_achatForm(data=form_data)
        r = form.is_valid()
        self.assertFalse(r)
        self.assertEqual(form.errors, {'nouveau_titre': [u'si vous ne choisissez pas un titre, vous devez taper le nom du nouveau']})

    def test_Ope_titre_add_achatForm4(self):
        form_data = {'date': "02/09/2012",
                   'titre': "1",
                   'compte_titre': '4',
                   'compte_espece': '2',
                   'nombre': '10',
                   'cours': '1.56',
                   'frais': '10',
                   'nouveau_titre': '',
                   'nouveau_isin': 'isis',
                   }
        form = gsb_forms.Ope_titre_add_achatForm(data=form_data)
        r = form.is_valid()
        self.assertTrue(r)
        self.assertNotIn('nouvel_isin', form.cleaned_data)

    def test_Ope_titre_add_venteForm1(self):
        form_data = {'date': "02/09/2012",
                   'titre': "3",
                   'compte_titre': '5',
                   'compte_espece': '2',
                   'nombre': '10',
                   'cours': '1.56',
                   'frais': '10',
                   }
        form = gsb_forms.Ope_titre_add_venteForm(data=form_data)
        r = form.is_valid()
        self.assertTrue(r)
        self.assertQueryset_list(form.fields['titre'].queryset, models.Titre.objects.all().order_by('pk').values_list('pk', flat=True))

    def test_Ope_titre_add_venteForm2(self):
        form_data = {'date': "02/09/2012",
                   'titre': "3",
                   'compte_titre': '5',
                   'compte_espece': '2',
                   'nombre': '10',
                   'cours': '1.56',
                   'frais': '10',
                   }
        cpt_titre = models.Compte.objects.get(id=5)
        form = gsb_forms.Ope_titre_add_venteForm(data=form_data, cpt=cpt_titre)
        self.assertQueryset_list(form.fields['titre'].queryset, cpt_titre.liste_titre().order_by('pk').values_list('pk', flat=True))
        r = form.is_valid()
        self.assertTrue(r)

    def test_Ope_titre_add_venteForm3(self):
        form_data = {'date': "01/07/2011",
                   'titre': "3",
                   'compte_titre': '5',
                   'compte_espece': '2',
                   'nombre': '1000',
                   'cours': '1.56',
                   'frais': '10',
                   }
        cpt_titre = models.Compte.objects.get(id=5)
        form = gsb_forms.Ope_titre_add_venteForm(data=form_data, cpt=cpt_titre)
        r = form.is_valid()
        self.assertFalse(r)
        self.assertEqual(form.errors, {'titre': [u"titre pas en portefeuille", ]})

    def test_Ope_titre_add_venteForm4(self):
        form_data = {'date': "01/01/2013",
                   'titre': "3",
                   'compte_titre': '5',
                   'compte_espece': '2',
                   'nombre': '1000',
                   'cours': '1.56',
                   'frais': '10',
                   }
        cpt_titre = models.Compte.objects.get(id=5)
        form = gsb_forms.Ope_titre_add_venteForm(data=form_data, cpt=cpt_titre)
        r = form.is_valid()
        self.assertFalse(r)
        self.assertEqual(form.errors, {'titre': [u"titre pas assez en portefeuille pour que l'opération puisse s'effectuer", ]})

    def testOpe_titreForm(self):
        ope = models.Ope_titre.objects.get(id=2)
        form = gsb_forms.Ope_titreForm(instance=ope)
        self.assertTrue('titre' in [k for k in form.fields.keys()])
        self.assertTrue('compte' in [k for k in form.fields.keys()])

    def testMajCoursform(self):
        gsb_forms.MajCoursform()

    def testMajtitre(self):
        form = gsb_forms.Majtitre(models.Titre.objects.all())
        k = [k for k in form.fields.keys()]
        self.assert_(len(k) == 7)

    def testSearchForm(self):
        gsb_forms.SearchForm()
