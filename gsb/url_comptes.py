from django.conf.urls.defaults import patterns, include, url

urlpatterns = patterns('gsb.views',
    (r'^(?P<cpt_id>\d+)/$','cpt_detail'),
    (r'(?P<cpt_id>\d+)/ope/new','creation_ope'),
    (r'^(?P<cpt_id>\d+)/virement/new','creation_virement'),

)
