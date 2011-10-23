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
from mysite.gsb.models import Generalite, Compte, Ope, Compte_titre, Moyen, Titre, Cours, Tiers, Ope_titre, Cat
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
    url(r'test/(?P<pk>\d+)/$', 'search_ope',name='g_search_ope'),
    (r'^$', 'chgt_ope_titre'))

#---------------les fields, widgets  et forms tres perso
class searchForm(gsb_forms.Baseform):
    date_max = gsb_field.DateFieldgsb()
    date_min = gsb_field.DateFieldgsb()
    rapp=forms.BooleanField(required=False,label=u"rapprochés?")
    tiers = forms.ModelChoiceField(Tiers.objects.all(), required = False)
    cat = forms.ModelChoiceField(Cat.objects.all().order_by('type', 'nom'), empty_label = None)
    moyen = forms.ModelChoiceField(Moyen.objects.all().order_by('type'), required = False)
    pointe = forms.BooleanField(required = False)
    rapp_detail= forms.ModelChoiceField(Rapp.objects.all(), required = False)
#----------les views tres perso
def chgt_ope_titre(request):
    nb_ope=0
    for ope in Ope_titre.objects.all():
        if not ope.ope:
            print ope.id
            if ope.cours * ope.nombre * -1 >0:#vente
                moyen=ope.compte.moyen_credit_defaut
            else:#achat
                moyen=ope.compte.moyen_credit_defaut
            nb_ope+=1
            ope.ope=Ope.objects.create(date = ope.date,
                                            montant = ope.cours * ope.nombre * -1,
                                            tiers = ope.titre.tiers,
                                            cat = Cat.objects.get_or_create(nom = u"operation sur titre:",
                                                                        defaults = {'nom':u'operation sur titre:'})[0],
                                            notes = "%s@%s" % (ope.nombre, ope.cours),
                                            moyen = moyen,
                                            automatique = True,
                                            compte = ope.compte,
                                            )

            ope.ope.date = ope.date
            ope.ope.montant = ope.cours * ope.nombre * -1
            ope.ope.note = "%s@%s" % (ope.nombre, cours)
            ope.ope.save()
            ope.save()
            print nb_ope
    return render(request,'generic.djhtm',{'titre':'chgt'})

def search_opes(request,pk):
    cpt = get_object_or_404(Compte.objects.select_related(), pk = pk)
    opes=cpt.ope_set.all().order_by('-date').filter(mere__exact = None)#definition du set par defaut
    first=cpt.ope_set.order_by('date')[0].date#recuperation de la date extreme
    if request.method == 'POST':
        form = searchForm(data = request.POST)
        if form.is_valid():
            #comme c'est bon, on peut filter plus
            if form.cleaned_data['date_max'] != datetime.date.today():
                opes=opes.filter(date__lte=form.cleaned_data['date_max'])
            if form.cleaned_data['rapp']:
                opes=opes.filter(Q(rapp__isnull=False)|Q(jumelle__rapp__isnull=False))
    else:
        form = searchForm(initial={'date_max':datetime.date.today(),'date_min':first})
    solde=opes.aggregate(solde = models.Sum('montant'))['solde']
    return render(request,'templates_perso/test.djhtm',
            {'form':form,
             'opes':opes,
             'titre':"liste %s"%cpt.nom,
             'solde':solde})

