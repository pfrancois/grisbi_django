# -*- coding: utf-8

#import relatif views
from django.template import RequestContext, loader
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.contrib import messages

#import relatif urls
from django.core.urlresolvers import reverse
from django.conf import settings
from django.conf.urls.defaults import patterns, url, include

#import relatif forms
import mysite.gsb.forms as gsb_forms
import mysite.gsb.widgets as gsb_field
from django import forms
#models
from mysite.gsb.models import Generalite, Compte, Ope, Compte_titre, Moyen, Titre, Cours, Tiers, Ope_titre, Cat, Rapp
from django.db import models
from django.db.models import Q
#divers
import datetime
import decimal
import logging #@UnusedImport
from django.contrib.auth.decorators import login_required
from django.utils.encoding import smart_unicode

#-----------les urls.py


#-----------les urls.py
urlpatterns = patterns('mysite.gsb.forms_perso',
    url(r'search/(?P<pk>\d+)/$', 'search_opes', name='g_search_ope'),
    (r'^ope$', 'pel'))

#---------------les fields, widgets  et forms tres perso
class SearchForm(gsb_forms.Baseform):
    date_max = gsb_field.DateFieldgsb()
    date_min = gsb_field.DateFieldgsb()
    rapp = forms.BooleanField(required=False, label=u"rapprochés?")
    tiers = forms.ModelChoiceField(Tiers.objects.all(), required=False)
    cat = forms.ModelChoiceField(Cat.objects.all().order_by('type', 'nom'), required=False)
    moyen = forms.ModelChoiceField(Moyen.objects.all().order_by('type'), required=False)
    pointe = forms.BooleanField(required=False)
    rapp_detail = forms.ModelChoiceField(Rapp.objects.all(), required=False)
    def __init__(self, *args, **kwargs):
        cpt_id = kwargs.pop('cpt')
        super(SearchForm, self).__init__(*args, **kwargs)
        self.fields['tiers'].queryset = Tiers.objects.filter(ope__compte_id=cpt_id).distinct()
        self.fields['cat'].queryset = Cat.objects.filter(ope__compte_id=cpt_id).distinct()
        self.fields['moyen'].queryset = Moyen.objects.filter(ope__compte_id=cpt_id).distinct()
        self.fields['rapp_detail'].queryset = Rapp.objects.filter(ope__compte_id=cpt_id).distinct()
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
    annee = [2005, 2006, 2007, 2008, 2009]
    mois = range(1, 13)
    for a in annee:
        for m in mois:
            c = Compte_titre.objects.get(id=4)
            if m + 1 != 13:
                jour = datetime.date(a, m + 1, 1) - datetime.timedelta(days=1)
            else:
                jour = datetime.date(a + 1, 1, 1) - datetime.timedelta(days=1)
            t = Titre.objects.get(nom='PEL')
            c.achat(titre=t, nombre=45, date=jour)
            print 'otot'
    return render(request, 'generic.djhtm', {'titre':'pel'})
@login_required
def search_opes(request, pk):
    cpt = get_object_or_404(Compte.objects.select_related(), pk=pk)
    opes = cpt.ope_set.all().order_by('-date').filter(mere__exact=None)#definition du set par defaut
    first = cpt.ope_set.order_by('date')[0].date#recuperation de la date extreme
    if request.method == 'POST':
        form = SearchForm(data=request.POST, cpt=cpt)
        if form.is_valid():
            #comme c'est bon, on peut filter plus
            if form.cleaned_data['date_max'] != datetime.date.today():
                opes = opes.filter(date__lte=form.cleaned_data['date_max'])
            if form.cleaned_data['rapp']:
                opes = opes.filter(Q(rapp__isnull=False) | Q(jumelle__rapp__isnull=False))
            if form.cleaned_data['tiers']:
                opes = opes.filter(tiers=form.cleaned_data['tiers'])
            if form.cleaned_data['cat']:
                opes = opes.filter(cat=form.cleaned_data['cat'])
            if form.cleaned_data['moyen']:
                opes = opes.filter(moyen=form.cleaned_data['moyen'])
            if form.cleaned_data['pointe']:
                opes = opes.filter(pointe=form.cleaned_data['pointe'])
            if form.cleaned_data['rapp_detail']:
                opes = opes.filter(rapp=form.cleaned_data['rap_detail'])
    else:
        form = SearchForm(initial={'date_max':datetime.date.today(), 'date_min':first}, cpt=cpt)
    solde = opes.aggregate(solde=models.Sum('montant'))['solde']
    return render(request, 'templates_perso/test.djhtm',
            {'form':form,
             'opes':opes,
             'titre':"liste %s" % cpt.nom,
             'solde':solde})

