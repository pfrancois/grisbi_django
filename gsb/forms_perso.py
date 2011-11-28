# -*- coding: utf-8
from __future__ import absolute_import
#import relatif views
from django.template import RequestContext, loader
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404, render
from django.contrib import messages

#import relatif urls
from django.core.urlresolvers import reverse
from django.conf import settings
from django.conf.urls.defaults import patterns, url, include

#import relatif forms
from . import forms as gsb_forms
from . import widgets as gsb_field
from django import forms
#models
from .models import Generalite, Compte, Ope, Compte_titre, Moyen, Titre, Cours, Tiers, Ope_titre, Cat, Rapp
from django.db import models
from django.db.models import Q
#divers
import datetime
import decimal
import logging #@UnusedImport
from django.contrib.auth.decorators import login_required
from django.utils.encoding import smart_unicode
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from . import utils as utils
#-----------les urls.py


#-----------les urls.py
urlpatterns = patterns('mysite.gsb.forms_perso',
                       url(r'^search$', 'search_opes', name='g_search_ope'),
                            )

#---------------les fields, widgets  et forms tres perso
class SearchField(gsb_forms.Baseform):
    Compte = forms.ModelChoiceField(Compte.objects.all(), required=False)
    date_min = forms.DateTimeField(label='date_min', widget=forms.DateTimeInput)
    date_max = forms.DateTimeField(label='date_max', widget=forms.DateTimeInput)


    #----------les views tres perso

@login_required
def search_opes(request):
    if request.method == 'POST':
        form = SearchField(request.POST)
        if form.is_valid():
            q = Ope
            sort = request.GET.get('sort')
            if sort:
                sort = unicode(sort)
                q = q.order_by(sort)
                sort_get = u"&sort=%s" % sort
            else:
                sort_get = u""
            paginator = Paginator(q, 50)
            try:
                page = int(request.GET.get('page'))
            except (ValueError, TypeError):
                page = 1
            try:
                ope = paginator.page(page)
            except PageNotAnInteger:
                # If page is not an integer, deliver first page.
                ope = paginator.page(1)
            except (EmptyPage, InvalidPage):
                ope = paginator.page(paginator.num_pages)
            return render(request, 'templates_perso/search.djhtm', {'list_ope':ope, 'titre':'recherche', "sort":sort_get})
