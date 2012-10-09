# -*- coding: utf-8 -*-
from __future__ import absolute_import
from django.conf.urls import patterns, url
#from django.conf.urls import include #non utilise actuellement
from .views import Mytemplateview,Myredirectview
from . import export_csv,export_qif
from django.core.urlresolvers import reverse_lazy
from .models import Echeance

# les vues generales
urlpatterns = patterns('gsb',
                       url(r'^$', 'views.index', name='index'),
                       url(r'^test$', 'test.test')
)

#les vues relatives aux outils
urlpatterns += patterns('gsb.outils',
                        url(r'^options$',
                            Mytemplateview.as_view(template_name="gsb/options.djhtm",
                                                   titre="liste des outils disponible")
                            ,name="outils_index"
                        ),
                        url(r'^options/import$', 'import_file',name="import_1"),
                        url(r'^options/ech$',
                            Myredirectview.as_view(url=reverse_lazy('outils_index'),
                                                   call=Echeance.check),
                            name='gestion_echeances'
                        ),
                        url(r'^options/verif_config$', 'verif_config', name='verif_config'),
)
urlpatterns += patterns('gsb',
                        url(r'^options/export/gsb050$',
                                'export_gsb_0_5_0.export',
                                name='export_gsb_050'
                        ),
                        url(r'^options/export/csv/ope$',
                                export_csv.Export_ope_csv.as_view(),
                                name='export_csv'
                        ),
                        url(r'^options/export/qif/ope$',
                                export_qif.Export_qif.as_view(),
                                name='export_qif'
                        ),
                        url(r'^options/export_autres$',
                                Mytemplateview.as_view(template_name="gsb/export_autres.djhtm"),
                                name='export_autres'
                        ),
                        url(r'^options/export/csv/ope_titres$',
                            export_csv.Export_ope_titre_csv.as_view(),
                            name='export_ope_titre'
                        ),
                        url(r'^options/export/csv/cours$',
                            export_csv.Export_cours_csv.as_view(),
                            name='export_cours'
                        ),
                        )
urlpatterns += patterns('',
                        (r'^favicon\.ico$', Myredirectview.as_view(url='/static/img/favicon.ico')),
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
                        url(r'^compte/(?P<cpt_id>\d+)/especes/all$',
                            'cpt_titre_espece',
                            {'all':True},
                            name="gsb_cpt_titre_espece_all"
                        ),
                        url(r'^compte/(?P<cpt_id>\d+)/especes/rapp$',
                            'cpt_titre_espece',
                            {'rapp':True},
                            name="gsb_cpt_titre_espece_rapp"
                        ),
                        url(r'^compte/(?P<cpt_id>\d+)/titre/(?P<titre_id>\d+)$',
                            'titre_detail_cpt',
                            name="gsb_cpt_titre_detail"
                        ),
                        url(r'^compte/(?P<cpt_id>\d+)/titre/(?P<titre_id>\d+)/all$',
                            'titre_detail_cpt',
                            {'all':True},
                            name="gsb_cpt_titre_detail_all"
                        ),
                        url(r'^compte/(?P<cpt_id>\d+)/titre/(?P<titre_id>\d+)/rapp$',
                            'titre_detail_cpt',
                            {'rapp':True},
                            name="gsb_cpt_titre_detail_rapp"
                        ),
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
