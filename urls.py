# -*- coding: utf-8 -*-
from django.conf.urls import patterns, include, url
from django.contrib import admin

admin.autodiscover()
import gsb.urls

urlpatterns = patterns('',
                       # Common stuff... files, admin...
    (r'^gestion_bdd/doc/', include('django.contrib.admindocs.urls')),
    (r'^gestion_bdd/', include(admin.site.urls)),
    url(r'^login$', 'django.contrib.auth.views.login', {'template_name': 'login.djhtm'}),
    (r'^logout$', 'django.contrib.auth.views.logout', {'next_page': '/'}),
    # reset pass word
    url(r'^admin/password_reset/$', 'django.contrib.auth.views.password_reset', name='admin_password_reset'),
    (r'^admin/password_reset/done/$', 'django.contrib.auth.views.password_reset_done'),
    (r'^reset/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/$', 'django.contrib.auth.views.password_reset_confirm'),
    (r'^reset/done/$', 'django.contrib.auth.views.password_reset_complete'),
                       # attention catch all vers gsb le mettre en dernier
    (r'^', include(gsb.urls)),
)
