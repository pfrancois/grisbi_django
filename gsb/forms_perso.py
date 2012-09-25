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
from django.conf.urls import patterns, url, include

#import relatif forms
from . import forms as gsb_forms
from . import widgets as gsb_field
from django import forms
#models
from .models import Compte, Ope, Compte_titre, Moyen, Titre, Cours, Tiers, Ope_titre, Cat, Rapp
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
urlpatterns = patterns('gsb.forms_perso',
                       url(r'^search$', 'search_opes', name='g_search_ope'),
                       )

#---------------les fields, widgets  et forms tres perso
class SearchField(gsb_forms.Baseform):
    compte = forms.ModelChoiceField(Compte.objects.all(), required=False)
    date_min = forms.DateField(label='date_min', widget=forms.DateInput)
    date_max = forms.DateField(label='date_max', widget=forms.DateInput)
    #----------les views tres perso


@login_required
def search_opes(request):
    if request.method == 'POST':
        form = SearchField(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            compte = data['compte']
            q = Ope.objects.filter(compte=compte, date__gte=data['date_min'], date__lte=data['date_max'])
            sort = request.GET.get('sort')
            if sort:
                sort = unicode(sort)
                q = q.order_by(sort)
                sort_get = u"&sort=%s" % sort
            else:
                sort_get = ""
                q = q.order_by('-date')
            q = q.select_related('tiers', 'cat', 'rapp', 'moyen', 'jumelle', 'ope_titre')[:100]
            return render(request, 'templates_perso/search.djhtm', {'form':form,
                                                                    'list_ope':q,
                                                                    'titre':u'recherche des %s premières opérations du compte %s' % (q.count(), compte.nom),
                                                                    "sort":sort_get,
                                                                    'date_max':data['date_max'],
                                                                    'solde':compte.solde(datel=data['date_max'])})
        else:
            date_max = Ope.objects.aggregate(element=models.Max('date'))['element']
    else:
        date_min = Ope.objects.aggregate(element=models.Min('date'))['element']
        date_max = Ope.objects.aggregate(element=models.Max('date'))['element']
        form = SearchField(initial={'date_min':date_min, 'date_max':date_max})

    return render(request, 'templates_perso/search.djhtm', {'form':form,
                                                            'list_ope':None,
                                                            'titre':'recherche',
                                                            "sort":"",
                                                            'date_max':'',
                                                            'solde':None})
