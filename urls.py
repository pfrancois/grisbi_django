# -*- coding: utf-8 -*-
from django.conf.urls.defaults import patterns, include, url
from django.contrib import admin

admin.autodiscover()
import gsb.urls

urlpatterns = patterns('',
                       # Common stuff... files, admin...
                       # qbe
   url(r'^qbe/', include('mysite.django_qbe.urls')),
    (r'^gestion_bdd/doc/', include('django.contrib.admindocs.urls')),
    (r'^gestion_bdd/', include(admin.site.urls)),
                       url(r'^login$', 'django.contrib.auth.views.login', {'template_name':'login.djhtm'}),
    (r'^logout$', 'django.contrib.auth.views.logout', {'next_page':'/'}),
                       #attention catch all vers gsb le mettre en dernier
    (r'^', include(gsb.urls)),
)
