# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Example:
    # (r'^grisbi/', include('grisbi.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    (r'^admin/', include(admin.site.urls)),
    # (r'^ope/(?P<ope_id>\d+)/$',include('grisbi.gsb.views.ope_index')),
    #(r'^compte/(?P<cpt_id>\d+)/$',include('grisbi.gsb.views.cpt_index')),
    (r'^comptes$','grisbi.gsb.views.index'),

)
