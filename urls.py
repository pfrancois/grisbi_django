# -*- coding: utf-8 -*-
from django.conf.urls.defaults import patterns, include, url
from django.contrib import admin
admin.autodiscover()
from django.views.generic import *
from mysite.gsb.models import *
import mysite.gsb.forms as gsb_forms
from django.core.urlresolvers import reverse

urlpatterns = patterns('',
                       # Common stuff... files, admin...
                       (r'^admin/doc/', include('django.contrib.admindocs.urls')),
                       (r'^admin/', include(admin.site.urls)),
                       (r'^login$', 'django.contrib.auth.views.login', { 'template_name': 'login.django.html' }),
                       (r'^logout$', 'django.contrib.auth.views.logout',{'next_page':'/'}),
                       )

# les vues generales
urlpatterns += patterns('mysite.gsb',
                        (r'^$', 'views.index'),
                        (r'^test$', 'test.test')
                        )
#les vues relatives aux outils
urlpatterns += patterns('mysite.gsb.outils',
                        (r'^options$', 'options_index'),
                        (r'^options/import$', 'import_file'),
                        (r'^options/modif_gen$', 'modif_gen'),
                        )
urlpatterns += patterns('mysite.gsb',
                        (r'^options/xml$', 'gsb_0_5_0.export'),
                        )
#les vues relatives aux operations
urlpatterns += patterns('mysite.gsb.views',
                        url(r'^ope/(?P<pk>\d+)/$', 'ope_detail',name='gsb_ope_detail'),
                        url(r'^ope/new$','ope_new',name="gsb_ope_new"),
                        url(r'^vir/new$','vir_new',name="gsb_vir_new"),
                        )

#les vues relatives aux comptes
urlpatterns += patterns('mysite.gsb.views',
                        (r'^compte/(?P<cpt_id>\d+)/$', 'cpt_detail'),
                        (r'^compte_titre/(?P<cpt_id>\d+)/$', 'cpt_titre_detail'),
                        url(r'^cpt/(?P<cpt_id>\d+)/new$','ope_new',name="gsb_cpt_ope_new"),
                        url(r'^cpt/(?P<cpt_id>\d+)/new_vir$','vir_new',name="gsb_cpt_vir_new"),
                        )

#les vues relatives aux tiers
class tierscreateview(CreateView):
    model=Tiers
    context_object_name = "tiers"
    template_name = 'gsb/tiers.django.html'
    def get_success_url(self):
        return reverse('gsb_close')
urlpatterns += patterns('mysite.gsb.views',
                        url(r'^tiers/new/$', tierscreateview.as_view(),name='gsb_tiers_create'),
                        url(r'^close/', TemplateView.as_view(template_name="close.django.html"),name="gsb_close"),
)

#form tester
from mysite.gsb.form_tester import SomeModelFormPreview

urlpatterns += patterns('mysite.gsb.views',
                        (r'^testform/$', SomeModelFormPreview(gsb_forms.VirementForm)),
)
