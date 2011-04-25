from django.conf.urls.defaults import *

urlpatterns = patterns('gsb.views',
                       (r'^(?P<cpt_id>\d+)/$', 'cpt_detail'),
                       (r'^titres/(?P<cpt_id>\d+)/$', 'cpt_titre_detail'),
                       (r'^(?P<cpt_id>\d+)/ope/new', 'creation_ope'),
                       (r'^(?P<cpt_id>\d+)/virement/new', 'creation_virement'),

                       )
