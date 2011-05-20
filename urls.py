# -*- coding: utf-8 -*-
from django.conf.urls.defaults import patterns, include
from django.contrib import admin
from django.contrib import databrowse
from mysite.gsb.models import *
admin.autodiscover()
databrowse.site.register(Tiers)
databrowse.site.register(Cat)
databrowse.site.register(Compte)
databrowse.site.register(Ope)
databrowse.site.register(Titre)
databrowse.site.register(Cours)
databrowse.site.register(Banque)
databrowse.site.register(Ib)
databrowse.site.register(Exercice)
databrowse.site.register(Rapp)
databrowse.site.register(Moyen)
databrowse.site.register(Echeance)
databrowse.site.register(Generalite)

urlpatterns = patterns('',
                       # Common stuff... files, admin...
                       (r'^admin/doc/', include('django.contrib.admindocs.urls')),
                       (r'^admin/', include(admin.site.urls)),
                       (r'^databrowse/(.*)', databrowse.site.root),
                       (r'^login$', 'django.contrib.auth.views.login', { 'template_name': 'login.django.html' }),

                       )

# les vues generales
urlpatterns += patterns('gsb',
                        (r'^$', 'views.index'),
                        (r'^test$', 'test.test'),
                        )
#les vues relatives aux outils
urlpatterns += patterns('gsb',
                        (r'^options$', 'outils.options'),
                        (r'^import$', 'outils.import_file'),
                        (r'^xml$', 'gsb_0_5_0.export'),
                        )
#les vues relatives aux operations
urlpatterns += patterns('gsb.views',

                        (r'^ope/(?P<ope_id>\d+)/$', 'ope_detail'),
                        )
#les vues relatives aux comptes
urlpatterns += patterns('gsb.views',
                        (r'^compte/(?P<cpt_id>\d+)/$', 'cpt_detail'),
                        (r'^compte_titre/(?P<cpt_id>\d+)/$', 'cpt_titre_detail'),

                        )


