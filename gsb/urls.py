# -*- coding: utf-8 -*-
from django.conf.urls.defaults import patterns, url
from django.views.generic import RedirectView
import mysite.gsb.forms as gsb_forms
from django.conf import settings

# les vues generales
urlpatterns = patterns('mysite.gsb',
                        (r'^$', 'views.index'),
                        )

#les vues relatives aux outils
urlpatterns += patterns('mysite.gsb.outils',
                        (r'^options$', 'options_index'),
                        (r'^options/import$', 'import_file'),
                        url(r'^options/modif_gen$', 'modif_gen', name = 'modification_preference_generalite'),
                        )
urlpatterns += patterns('mysite.gsb',
                        url(r'^options/gsb050$', 'export_gsb_0_5_0.export', name = 'export_gsb_050'),
                        url(r'^options/csv$', 'export_csv.export', name = 'export_csv'),
                        )
urlpatterns += patterns('',
                        (r'^favicon\.ico$', RedirectView.as_view(url = '/static/img/favicon.ico')),
                        url(r'^maj_cours/(?P<pk>\d+)$', 'mysite.gsb.views.maj_cours', name = 'maj_cours')
                        )
 
#les vues relatives aux operations
urlpatterns += patterns('mysite.gsb.views',
                        url(r'^ope/(?P<pk>\d+)/delete', 'ope_delete', name = 'gsb_ope_delete'),
                        url(r'^ope/(?P<pk>\d+)/$', 'ope_detail', name = 'gsb_ope_detail'),
                        url(r'^ope/new$', 'ope_new', name = "gsb_ope_new"),
                        url(r'^vir/new$', 'vir_new', name = "gsb_vir_new"),
                        url(r'^ope_titre/(?P<pk>\d+)/$', 'ope_titre_detail', name = 'ope_titre_detail'),
                        url(r'^ope_titre/(?P<pk>\d+)/delete', 'ope_titre_delete', name = 'ope_titre_delete'),
                        )

#les vues relatives aux comptes
urlpatterns += patterns('mysite.gsb.views',
                        (r'^compte/(?P<cpt_id>\d+)/$', 'cpt_detail'),
                        url(r'^compte/(?P<cpt_id>\d+)/new$', 'ope_new', name = "gsb_cpt_ope_new"),
                        url(r'^compte/(?P<cpt_id>\d+)/vir/new$', 'vir_new', name = "gsb_cpt_vir_new"),
                        url(r'^compte/(?P<cpt_id>\d+)/especes', 'cpt_titre_espece', name = "gsb_cpt_titre_espece"),
                        url(r'^compte/(?P<cpt_id>\d+)/titre/(?P<titre_id>\d+)', 'titre_detail_cpt', name = "gsb_cpt_titre_detail"),
                        url(r'^compte/(?P<cpt_id>\d+)/achat', 'ope_titre_achat', name = "cpt_titre_achat"),
                        url(r'^compte/(?P<cpt_id>\d+)/vente', 'ope_titre_vente', name = "cpt_titre_vente"),
                        )


#form tester
if settings.DEBUG:
    from mysite.gsb.form_tester import SomeModelFormPreview
    urlpatterns += patterns('mysite.gsb',
                            (r'^testform/$', SomeModelFormPreview(gsb_forms.Ope_titre_addForm)),
                            (r'^test$', 'test.test'),
                            )
