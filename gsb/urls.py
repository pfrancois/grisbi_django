# -*- coding: utf-8 -*-

from django.conf.urls import include, url
# from django.conf.urls import include #non utilise actuellement
from . import views, outils
from .io import import_csv, export_csv, lecture_plist
from .io import import_titre_csv as import_titres
from django.conf import settings
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf.urls.static import static

# les vues generales
# TODO enlever les patterns
urlpatterns = [url(r'^$', views.Index_view.as_view(), name='index'),
               url(r'^rest/', include('gsb.rest.url')),
                # les vues relatives aux outils
                url(r'^options$',
                    views.Mytemplateview.as_view(template_name="gsb/options.djhtm", titre="liste des outils disponible"),
                    name="outils_index"),
                # echeances echues
                url(r'^options/ech$', outils.Echeance_view.as_view(), name='gestion_echeances'),
                # affiche config
                url(r'^outils/verif_config$', outils.verif_config, name='verif_config'),
                url(r'^options/maj_money_journal$', lecture_plist.gestion_maj, name='gestion_maj_iphone_money_journal'),
                # export index
                url(r'^options/export$',
                    views.Mytemplateview.as_view(template_name="gsb/export_index.djhtm"),
                    name='export_index'),
                # export au format general en csv
                url(r'^options/export/csv/ope$', export_csv.Export_ope_csv.as_view(), name='export_csv'),
                # export des ope titres
                url(r'^options/export/csv/ope_titres$',
                    export_csv.Export_ope_titre_csv.as_view(),
                    name='export_ope_titre'),
                # export des cours
                url(r'^options/export/csv/cours$', export_csv.Export_cours_csv.as_view(), name='export_cours'),
                url(r'options/import/csv/simple$',
                    import_csv.Import_csv_ope_sans_jumelle_et_ope_mere.as_view(),
                    name="import_csv_ope_simple"),
                url(r'options/import/csv/titres$',
                    import_titres.Import_csv_ope_titre.as_view(),
                    name="import_csv_ope_titre_all"),
                # les vues relatives aux operations
                url(r'^ope/(?P<pk>\d+)/delete', views.ope_delete, name='gsb_ope_delete'),
                url(r'^ope/(?P<pk>\d+)/$', views.ope_detail, name='gsb_ope_detail'),
                url(r'^ope/new$', views.ope_new, name="gsb_ope_new"),
                url(r'^compte/(?P<cpt_id>\d+)/new$', views.ope_new, name="gsb_cpt_ope_new"),
                url(r'^vir/new$', views.vir_new, name="gsb_vir_new"),
                url(r'^compte/(?P<cpt_id>\d+)/vir/new$', views.vir_new, name="gsb_cpt_vir_new"),
                url(r'^ope_titre/(?P<pk>\d+)/$', views.ope_titre_detail, name='ope_titre_detail'),
                url(r'^ope_titre/(?P<pk>\d+)/delete$', views.ope_titre_delete, name='ope_titre_delete'),
                url(r'^majcours/(?P<pk>\d+)/$', views.maj_cours, name='maj_cours'),
                # les vues relatives aux comptes
                url(r'^compte/(?P<cpt_id>\d+)/$', views.Cpt_detail_view.as_view(), name='gsb_cpt_detail'),
                url(r'^compte/(?P<cpt_id>\d+)/rapp$', views.Cpt_detail_view.as_view(rapp=True), name='gsb_cpt_detail_rapp'),
                url(r'^compte/(?P<cpt_id>\d+)/all$', views.Cpt_detail_view.as_view(all=True), name='gsb_cpt_detail_all'),
                url(r'^compte/(?P<cpt_id>\d+)/especes$',
                    views.Cpt_detail_view.as_view(cpt_titre_espece=True),
                    name="gsb_cpt_titre_espece"),
                url(r'^compte/(?P<cpt_id>\d+)/especes/all$',
                    views.Cpt_detail_view.as_view(cpt_titre_espece=True, all=True),
                    name="gsb_cpt_titre_espece_all"),
                url(r'^compte/(?P<cpt_id>\d+)/especes/rapp$',
                     views.Cpt_detail_view.as_view(cpt_titre_espece=True, rapp=True),
                    name="gsb_cpt_titre_espece_rapp"),
                url(r'^compte/(?P<cpt_id>\d+)/titre/(?P<titre_id>\d+)$',
                    views.titre_detail_cpt,
                    name="gsb_cpt_titre_detail"),
                url(r'^compte/(?P<cpt_id>\d+)/titre/(?P<titre_id>\d+)/rapp$',
                    views.titre_detail_cpt,
                    {'rapp': True},
                    name="gsb_cpt_titre_detail_rapp"),
                url(r'^compte/(?P<cpt_id>\d+)/achat$', views.ope_titre_achat, name="cpt_titre_achat"),
                url(r'^compte/(?P<cpt_id>\d+)/vente$', views.ope_titre_vente, name="cpt_titre_vente"),
                url(r'^compte/(?P<cpt_id>\d+)/dividende$', views.dividende, name="cpt_titre_dividende"),
                url(r'^titres$', views.Rdt_titres_view.as_view(), name="Rdt_titres_view"),
                url(r'^compte/(?P<cpt_id>\d+)/titre_new$', views.ajout_ope_titre_bulk, name="titre_bulk"),
                url(r'^compte/(?P<cpt_id>\d+)/ajustement$', views.ajustement_titre, name="ajustement_titre"),
                url(r'^search$', views.search_opes, name='g_search_ope'),
                staticfiles_urlpatterns(),
                static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)]

# gestion de mes trucs perso
# form tester
# if settings.DEBUG and perso:
#   from gsb.form_tester import SomeModelFormPreview

# urlpatterns += patterns('gsb',
#   (r'^testform/$', SomeModelFormPreview(gsb_forms.MajCoursform)),
#                       url(r'^test$', 'test.test')
# )
# import gsb.forms_perso
"""
try:
    # noinspection PyUnresolvedReferences
    import perso
    urlpatterns += patterns('', (r'^perso/', include(perso)), )
except ImportError:
    pass
"""
urlpatterns += [url(r'^adminactions/', include('adminactions.urls'))]
