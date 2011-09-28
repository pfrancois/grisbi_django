# -*- coding: utf-8
from django import forms
from mysite.gsb.models import Compte, Cat, Moyen, Ope, Virement, Generalite, Compte_titre, Cours, Titre, Tiers, Ope_titre, Ib, Rapp
#from mysite.gsb import widgets
from django.conf import settings
import datetime
#import decimal
from django.utils.encoding import force_unicode
from django.utils.safestring import mark_safe
from django.forms.util import flatatt
from forms import Dategsbwidget, DateFieldgsb, Readonlywidget, ReadonlyField, CurField,Curwidget,Titrewidget,TitreField
from django.template import RequestContext, loader
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.shortcuts import render, get_object_or_404
import mysite.gsb.forms as gsb_forms
from django.db import models
from decimal import Decimal
from django.conf.urls.defaults import patterns, url
from django.core.exceptions import ValidationError
#import logging #@UnusedImport
from django.contrib.auth.decorators import login_required

#-----------les urls.py
urlpatterns =patterns('mysite.gsb.forms_perso',
                url(r'^pee$','view_majPEE'),
                )

#---------------les fields, widgets  et forms tres perso
input_format_date = ('%Y-%m-%d', '%d/%m/%Y', '%d/%m/%y', '%d%m%y', '%d%m%Y')
error_css_class = 'error'
required_css_class = 'required'

liste_opcvm = ('A', 'B', 'D', 'E')
class MajPEE(forms.Form):
    error_css_class = error_css_class
    required_css_class = required_css_class
    date = DateFieldgsb()
    def __init__(self, *args, **kwargs):
        super (MajPEE, self).__init__(*args, **kwargs)
        for i in liste_opcvm:
             self.fields[i] = TitreField()

#----------les views tres perso
@login_required
def view_majPEE(request):
    cpt=Compte_titre.objects.get(id=6)
    if request.method == 'POST':
        form = MajPEE(data=request.POST)
        if form.is_valid():
            for i in liste_opcvm:
                s=form.cleaned_data[i].partition('@')
                nb=Decimal(s[0])
                cours=Decimal(s[2])
                if nb<>'0' and nb:
                    cpt.achat(Titre.objects.get(nom='PEE%s'%str.lower(i)), nb, cours, date = form.cleaned_data['date'])
            return HttpResponseRedirect(reverse('mysite.gsb.views.cpt_detail', kwargs = {'cpt_id':6}))
    else:
        form = MajPEE()
    return render(request, 'templates_perso/achat_PEE.djhtm',
                {   'titre_long':u'operation sur le PEE' ,
                   'titre':u'ope PEE',
                    'form':form}
                )
