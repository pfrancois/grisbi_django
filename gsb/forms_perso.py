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
                        url(r'^ope$', 'pel'))

#---------------les fields, widgets  et forms tres perso
class SearchField(gsb_forms.Baseform):
    Compte=forms.ModelChoiceField(Compte.objects.all(),required=False)
    date_min = forms.DateTimeField(label='date_min', widget=forms.DateTimeInput)
    date_max = forms.DateTimeField(label='date_max', widget=forms.DateTimeInput)
    rapp = forms.BooleanField(required=False, label=u"rapprochés?")
    rapp_detail = forms.ModelChoiceField(Rapp.objects.all(), required=False)
    pointeourapp=forms.BooleanField(required=False)


    #----------les views tres perso
def chgt_ope_titre(request):
    nb_ope = 0
    for ope in Ope_titre.objects.all():
        if not ope.ope:
            print ope.id
            if  ope.nombre < 0:#vente
                ope.moyen = ope.compte.moyen_credit_defaut
            else:#achat
                ope.moyen = ope.compte.moyen_credit_defaut
            nb_ope += 1
            ope.montant = ope.cours * ope.nombre * -1
            ope.save()
            print ope.ope
    print nb_ope
    return render(request, 'generic.djhtm', {'titre':'chgt'})

def pel(request):
    now=datetime.date(2004, 4, 1)
    t = Titre.objects.get(nom='PEL')
    c = Compte_titre.objects.get(id=4)
    for ope in Ope_titre.objects.filter(ope=None):
        ope.save()

        #~ c.achat(titre=t, nombre=s, date=now)
    #~ print '----'
    #~ while now < datetime.date(2008, 2,1):
        #~ now=utils.addmonths(now,1)
        #~ s=50
        #~ c.achat(titre=t, nombre=s, date=now)
    #~ print '----'
    #~ while now < datetime.date(2010, 4, 1):
        #~ now=utils.addmonths(now,1)
        #~ s=100
        #~ c.achat(titre=t, nombre=s, date=now)
    #~ print '----'
    #~ while now < datetime.date(2011, 02, 1):
        #~ now=utils.addmonths(now,1)
        #~ c.achat(titre=t, nombre=50, date=now)
    #~ print '----'
    #~ while now < datetime.date.today():
        #~ now=utils.addmonths(now,1,first=True)
        #~ c.achat(titre=t, nombre=50, date=now,virement_de=Compte.objects.get(id=12))
    return render(request, 'generic.djhtm', {'titre':'pel'})


@login_required
def search_opes(request):
    q=Ope.objects.filter(mere__exact=None).filter(compte__id=12).filter(montant__gte=0)
    sort=request.GET.get('sort')
    if sort:
        sort=unicode(sort)
        q=q.order_by(sort)
        sort_get=u"&sort=%s"%sort
    else:
        sort_get=u""
    paginator=Paginator(q, 50)
    try:
        page = int(request.GET.get('page'))
    except (ValueError,TypeError):
        page = 1
    try:
        ope = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        ope = paginator.page(1)
    except (EmptyPage, InvalidPage):
            ope = paginator.page(paginator.num_pages)
    return render(request,'templates_perso/test.djhtm', {'list_ope':ope,'titre':'recherche',"sort":sort_get})
