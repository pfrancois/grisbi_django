# -*- coding: utf-8 -*-
from django.conf.urls.defaults import patterns, include
from django.contrib import admin
admin.autodiscover()


urlpatterns = patterns('',
                       # Common stuff... files, admin...
                       (r'^admin/doc/', include('django.contrib.admindocs.urls')),
                       (r'^admin/', include(admin.site.urls)),
                       (r'^login$', 'django.contrib.auth.views.login', { 'template_name': 'login.django.html' }),
                       (r'^logout$', 'django.contrib.auth.views.logout',{'next_page':'/'}),
                       )

# les vues generales
urlpatterns += patterns('gsb',
                        (r'^$', 'views.index'),
#                        (r'^test$', 'test.test'),
                        )
#les vues relatives aux outils
urlpatterns += patterns('gsb.outils',
                        (r'^options$', 'options_index'),
                        (r'^import$', 'import_file'),
                        (r'^modif_gen$', 'modif_gen'),
                        )
urlpatterns += patterns('gsb',
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


