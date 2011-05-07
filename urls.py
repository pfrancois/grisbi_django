# -*- coding: utf-8 -*-
from django.conf.urls.defaults import patterns, include
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('',
                       # Common stuff... files, admin...
                       (r'^admin/doc/', include('django.contrib.admindocs.urls')),
                       (r'^admin/', include(admin.site.urls)),
                       )

# les vues generales
urlpatterns += patterns('gsb',
                        (r'^$', 'views.index'),
                        (r'^xml$', 'gsb_0_5_0.export'),
                        (r'^import$', 'import_gsb.import_gsb'),
                        (r'^options$', 'views.options'),
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
