# -*- coding: utf-8 -*-
# Create your views here.
from django.db import models
from django.template import RequestContext, loader
from django.http import HttpResponse, Http404
from mysite.gsb.models import *
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.db import models
import datetime
import settings
from django.shortcuts import render_to_response, get_list_or_404,get_object_or_404
from django import forms


def cpt_detail(request,cpt_id):
    c = get_object_or_404(Compte,pk=cpt_id)
    if c.type == 'a':
        return HttpResponseRedirect(reverse('mysite.gsb.views.index'))
    if c.type == 'p':
        return HttpResponseRedirect(reverse('gsb.views.index'))
    t = loader.get_template('cpt_detail.django.html')
    date_limite = datetime.date.today()-datetime.timedelta(days=settings.NB_JOURS_AFF)
    q = Ope.objects.filter(compte__pk=cpt_id).order_by('-date').filter(date__gte=date_limite).filter(is_mere=False).filter(pointe__in=[u'na',u'p'])
    nb_ope_rapp=Ope.objects.filter(compte__pk=cpt_id).filter(is_mere=False).filter(pointe='r').count()
    p = list(q)
    return HttpResponse(
        t.render(
            RequestContext(
                request,
                {
                    'compte':c,
                    'list_ope': p,
                    'nbrapp': nb_ope_rapp,
                    'titre': c.nom,
                    'solde':c.solde(),
                    'nbrapp':nb_ope_rapp,
                }
            )
        )
    )

def ope_creation(request, cpt_id):
	cpt=get_object_or_404(Compte,pk=cpt_id)
	devise=get_object_or_404(Devise, pk=1)
	ope=new Ope(compte=cpt, date=datetime.date.today(), montant=0, devise=devise, tiers = None, cat = None, scat= None, Notes = None, moyen = None, numcheque="", )
	pass
