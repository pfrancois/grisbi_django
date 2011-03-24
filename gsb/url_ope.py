from django.conf.urls.defaults import patterns, include, url

urlpatterns = patterns('mysite.gsb.views',
    (r'^(?P<ope_id>\d+)','ope_detail'),
)
