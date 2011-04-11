from django.conf.urls.defaults import patterns, include, url


# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('mysite.gsb',
    # Examples:
    # url(r'^$', 'mysite.views.home', name='home'),
    # url(r'^mysite/', include('mysite.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),

    (r'^$','views.index'),
    (r'^compte/',include('gsb.url_comptes')),
    (r'^ope/',include('gsb.url_ope')),
    (r'^xml$','gsb_0_5_0.export')
)
