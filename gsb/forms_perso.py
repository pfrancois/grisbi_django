# -*- coding: utf-8
from mysite.gsb.models import Compte_titre
from mysite.gsb.forms import  error_css_class, required_css_class
from django.http import  HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.shortcuts import render
from decimal import Decimal
from django.conf.urls.defaults import patterns, url
from django.contrib.auth.decorators import login_required
from django.utils.encoding import force_unicode

#-----------les urls.py
#urlpatterns = patterns('mysite.gsb.forms_perso', '' )

#---------------les fields, widgets  et forms tres perso



#----------les views tres perso
