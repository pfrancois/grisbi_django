# -*- coding: utf-8 -*-
from __future__ import absolute_import
from django.conf.urls import patterns, url, include
from django.views.generic import RedirectView
from django.views.generic import TemplateView
from . import forms as gsb_forms
from django.conf import settings
from . import views as gsb_views
from . import export_csv,export_qif

# les vues generales
urlpatterns = patterns('gsb',
                       url(r'^$', 'views.index', name='index'),
                       #url(r'^test$', 'test.test')
)

#les vues relatives aux outils
urlpatterns += patterns('gsb.outils',
                        url(r'^options$', 'options_index',name="outils_index"),
                        url(r'^options/import$', 'import_file'),
                        url(r'^options/modif_gen$', 'modif_gen', name='modification_preference_generalite'),
                        url(r'^options/ech$', 'gestion_echeances', name='gestion_echeances')
)
urlpatterns += patterns('gsb',
                        url(r'^options/gsb050$', 'export_gsb_0_5_0.export', name='export_gsb_050'),
                        url(r'^options/csv$', export_csv.Export_ope_csv.as_view(), name='export_csv'),
                        url(r'^options/qif$', export_qif.Export_qif.as_view(), name='export_qif'),
                        url(r'^options/export_autres$', TemplateView.as_view(template_name="gsb/export_autres.djhtm"), name='export_autres'),
                        url(r'^options/export_ope_titres$', 'export_csv.export_ope_titres', name='export_ope_titre'),
                        url(r'^options/cours$', 'export_csv.export_cours', name='export_cours'),

                        )
urlpatterns += patterns('',
                        (r'^favicon\.ico$', RedirectView.as_view(url='/static/img/favicon.ico')),
                        url(r'^maj_cours/(?P<pk>\d+)$', 'gsb.views.maj_cours', name='maj_cours')
)

#les vues relatives aux operations
urlpatterns += patterns('gsb.views',
                        url(r'^ope/(?P<pk>\d+)/delete', 'ope_delete', name='gsb_ope_delete'),
                        url(r'^ope/(?P<pk>\d+)/$', 'ope_detail', name='gsb_ope_detail'),
                        url(r'^ope/new$', 'ope_new', name="gsb_ope_new"),
                        url(r'^vir/new$', 'vir_new', name="gsb_vir_new"),
                        url(r'^ope_titre/(?P<pk>\d+)/$', 'ope_titre_detail', name='ope_titre_detail'),
                        url(r'^ope_titre/(?P<pk>\d+)/delete$', 'ope_titre_delete', name='ope_titre_delete'),
                        url(r'^search$', 'search_opes', name='g_search_ope')
)

#les vues relatives aux comptes
urlpatterns += patterns('gsb.views',
                        url(r'^compte/(?P<cpt_id>\d+)/$', 'cpt_detail', name='gsb_cpt_detail'),
                        url(r'^compte/(?P<cpt_id>\d+)/rapp$', 'cpt_detail', {'rapp':True}, name='gsb_cpt_detail_rapp'),
                        url(r'^compte/(?P<cpt_id>\d+)/all$', 'cpt_detail', {'all':True}, name='gsb_cpt_detail_all'),
                        url(r'^compte/(?P<cpt_id>\d+)/new$', 'ope_new', name="gsb_cpt_ope_new"),
                        url(r'^compte/(?P<cpt_id>\d+)/vir/new$', 'vir_new', name="gsb_cpt_vir_new"),
                        url(r'^compte/(?P<cpt_id>\d+)/especes$', 'cpt_titre_espece', name="gsb_cpt_titre_espece"),
                        url(r'^compte/(?P<cpt_id>\d+)/especes/all$', 'cpt_titre_espece', {'all':True}, name="gsb_cpt_titre_espece_all"),
                        url(r'^compte/(?P<cpt_id>\d+)/especes/rapp$', 'cpt_titre_espece', {'rapp':True}, name="gsb_cpt_titre_espece_rapp"),
                        url(r'^compte/(?P<cpt_id>\d+)/titre/(?P<titre_id>\d+)$', 'titre_detail_cpt', name="gsb_cpt_titre_detail"),
                        url(r'^compte/(?P<cpt_id>\d+)/titre/(?P<titre_id>\d+)/all$', 'titre_detail_cpt', {'all':True}, name="gsb_cpt_titre_detail_all"),
                        url(r'^compte/(?P<cpt_id>\d+)/titre/(?P<titre_id>\d+)/rapp$', 'titre_detail_cpt', {'rapp':True}, name="gsb_cpt_titre_detail_rapp"),
                        url(r'^compte/(?P<cpt_id>\d+)/achat$', 'ope_titre_achat', name="cpt_titre_achat"),
                        url(r'^compte/(?P<cpt_id>\d+)/vente$', 'ope_titre_vente', name="cpt_titre_vente"),
                        url(r'^compte/(?P<cpt_id>\d+)/maj$', 'view_maj_cpt_titre', name="cpt_titre_maj"),
                        url(r'^perso$', 'perso'),
                        )
#gestion de mes trucs perso
perso = False# ya plus rien dedans
#form tester
#if settings.DEBUG and perso:
#    from gsb.form_tester import SomeModelFormPreview

    #urlpatterns += patterns('gsb',
    #    (r'^testform/$', SomeModelFormPreview(gsb_forms.MajCoursform)),
    #                        url(r'^test$', 'test.test')
    #)
    #import gsb.forms_perso

    #urlpatterns += patterns('', (r'^perso/', include(gsb.forms_perso)) )
