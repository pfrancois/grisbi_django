# -*- coding: utf-8 -*-
from __future__ import absolute_import
from django.conf.urls import patterns, url
# from django.conf.urls import include #non utilise actuellement
from . import views, outils
from .io import import_csv, export_sql_money, export_csv, export_qif
from .io import import_titre_csv as import_titres
# les vues generales
urlpatterns = patterns('gsb',
                       url(r'^$', views.Index_view.as_view(), name='index'),
                       #url(r'^test$',import_sg.testimport_view.as_view() )
)

# les vues relatives aux outils
urlpatterns += patterns('gsb.outils',
                        url(r'^options$',
                            views.Mytemplateview.as_view(template_name="gsb/options.djhtm",
                                                         titre="liste des outils disponible"),
                            name="outils_index"
                        ),
                        #echeances echues
                        url(r'^options/ech$',
                            outils.Echeance_view.as_view(),
                            name='gestion_echeances'
                        ),
                        #affiche config
                        url(r'^options/verif_config$', 'verif_config', name='verif_config'),
)
#export index
urlpatterns += patterns('gsb',
                        url(r'^options/export$',
                            views.Mytemplateview.as_view(template_name="gsb/export_index.djhtm"),
                            name='export_index'
                        ),
                        #export au format 0_5_0 grisbi
                        url(r'^options/export/gsb050$',
                            'io.export_gsb_0_5_0.export',
                            name='export_gsb_050'
                        ),
                        #export au format general en csv
                        url(r'^options/export/csv/ope$',
                            export_csv.Export_ope_csv.as_view(),
                            name='export_csv'
                        ),
                        #export en qif
                        url(r'^options/export/qif$',
                            export_qif.Export_qif.as_view(),
                            name='export_qif'
                        ),
                        #export des ope titres
                        url(r'^options/export/csv/ope_titres$',
                            export_csv.Export_ope_titre_csv.as_view(),
                            name='export_ope_titre'
                        ),
                        #export des cours
                        url(r'^options/export/csv/cours$',
                            export_csv.Export_cours_csv.as_view(),
                            name='export_cours'
                        ),
                        url(r'^options/export/sql/pm$',
                            export_sql_money.Export_view_sql.as_view(),
                            name='export_sql_pm'
                        )
)
#impor gsb 0_5_0
urlpatterns += patterns('gsb.io.import_gsb',
                        url(r'options/import_gsb$',
                            'import_gsb_0_5_x',
                            name="import_gsb")
)
#import csv format general
urlpatterns += patterns('',
                        url(r'options/import_csv_all$',
                            import_csv.Import_csv_ope.as_view(),
                            name="import_csv_ope_all")
)
#import csv ope titre
urlpatterns += patterns('',
                        url(r'import_titre$',
                            import_titres.Import_csv_ope_titre.as_view(),
                            name="import_csv_ope_all")
)


# les vues relatives aux operations
urlpatterns += patterns('gsb.views',
                        url(r'^ope/(?P<pk>\d+)/delete', 'ope_delete', name='gsb_ope_delete'),
                        url(r'^ope/(?P<pk>\d+)/$', 'ope_detail', name='gsb_ope_detail'),
                        url(r'^ope/new$', 'ope_new', name="gsb_ope_new"),
                        url(r'^vir/new$', 'vir_new', name="gsb_vir_new"),
                        url(r'^ope_titre/(?P<pk>\d+)/$', 'ope_titre_detail', name='ope_titre_detail'),
                        url(r'^ope_titre/(?P<pk>\d+)/delete$', 'ope_titre_delete', name='ope_titre_delete'),
                        url(r'^search$', 'search_opes', name='g_search_ope'),
                        url(r'^majcours/(?P<pk>\d+)/$', 'maj_cours', name='maj_cours')
)

# les vues relatives aux comptes
urlpatterns += patterns('gsb.views',
                        url(r'^compte/(?P<cpt_id>\d+)/$', views.Cpt_detail_view.as_view(), name='gsb_cpt_detail'),
                        url(r'^compte/(?P<cpt_id>\d+)/rapp$',
                            views.Cpt_detail_view.as_view(rapp=True),
                            name='gsb_cpt_detail_rapp'
                        ),
                        url(r'^compte/(?P<cpt_id>\d+)/all$',
                            views.Cpt_detail_view.as_view(all=True),
                            name='gsb_cpt_detail_all'
                        ),
                        url(r'^compte/(?P<cpt_id>\d+)/especes$',
                            views.Cpt_detail_view.as_view(cpt_titre_espece=True),
                            name="gsb_cpt_titre_espece"
                        ),
                        url(r'^compte/(?P<cpt_id>\d+)/especes/all$',
                            views.Cpt_detail_view.as_view(cpt_titre_espece=True, all=True),
                            name="gsb_cpt_titre_espece_all"
                        ),
                        url(r'^compte/(?P<cpt_id>\d+)/especes/rapp$',
                            views.Cpt_detail_view.as_view(cpt_titre_espece=True, rapp=True),
                            name="gsb_cpt_titre_espece_rapp"
                        ),
                        url(r'^compte/(?P<cpt_id>\d+)/new$', 'ope_new', name="gsb_cpt_ope_new"),
                        url(r'^compte/(?P<cpt_id>\d+)/vir/new$', 'vir_new', name="gsb_cpt_vir_new"),

                        url(r'^compte/(?P<cpt_id>\d+)/titre/(?P<titre_id>\d+)$',
                            'titre_detail_cpt',
                            name="gsb_cpt_titre_detail"
                        ),
                        url(r'^compte/(?P<cpt_id>\d+)/titre/(?P<titre_id>\d+)/all$',
                            'titre_detail_cpt',
                            {'all': True},
                            name="gsb_cpt_titre_detail_all"
                        ),
                        url(r'^compte/(?P<cpt_id>\d+)/titre/(?P<titre_id>\d+)/rapp$',
                            'titre_detail_cpt',
                            {'rapp': True},
                            name="gsb_cpt_titre_detail_rapp"
                        ),
                        url(r'^compte/(?P<cpt_id>\d+)/achat$', 'ope_titre_achat', name="cpt_titre_achat"),
                        url(r'^compte/(?P<cpt_id>\d+)/vente$', 'ope_titre_vente', name="cpt_titre_vente"),
                        url(r'^compte/(?P<cpt_id>\d+)/dividende$', 'dividende', name="cpt_titre_dividende"),
                        url(r'^perso$', 'perso'),
)

# gestion de mes trucs perso
perso = False  # ya plus rien dedans
# form tester
# if settings.DEBUG and perso:
#    from gsb.form_tester import SomeModelFormPreview

# urlpatterns += patterns('gsb',
#    (r'^testform/$', SomeModelFormPreview(gsb_forms.MajCoursform)),
#                        url(r'^test$', 'test.test')
# )
# import gsb.forms_perso

# urlpatterns += patterns('', (r'^perso/', include(gsb.forms_perso)) )
