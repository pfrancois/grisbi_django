# -*- coding: utf-8
from django import forms
from mysite.gsb.models import Compte_titre, Titre
from forms import  DateFieldgsb, TitreField
from django.http import  HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.shortcuts import render
from decimal import Decimal
from django.conf.urls.defaults import patterns, url
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
