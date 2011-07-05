# -*- coding: utf-8 -*-
# Create your views here.
from django.template import RequestContext, loader
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.conf import settings
from django.shortcuts import render, get_object_or_404
from mysite.gsb.models import *
import mysite.gsb.forms as gsb_forms
from django.db import models
import decimal
import logging
from django.contrib.auth.decorators import login_required

def index(request):
    t = loader.get_template('gsb/index.django.html')
    if Generalite.gen().affiche_clot:
        bq = Compte.objects.filter(type__in=('b', 'e', 'p')).select_related()
        pl = Compte.objects.filter(type__in=('t',)).select_related()
    else:
        bq = Compte.objects.filter(type__in=('b', 'e', 'p'),ouvert=True).select_related()
        pl = Compte.objects.filter(type__in=('t',),ouvert=True).select_related()
    total_bq=decimal.Decimal('0')
    total_pla=decimal.Decimal('0')
    if settings.UTIDEV:
        for c in bq:
            total_bq=total_bq+c.solde(devise_generale=True)
        for p in pl:
            total_pla=total_pla+p.solde(devise_generale=True)
    else:
        total_bq=Ope.objects.filter(mere__exact=None,compte__type__in=('b', 'e', 'p')).aggregate(solde=models.Sum('montant'))['solde']
        total_pla=Ope.objects.filter(mere__exact=None,compte__type__in=('t')).aggregate(solde=models.Sum('montant'))['solde']
    nb_clos = len(Compte.objects.filter(ouvert=False))
    c = RequestContext(request, {
        'titre': 'liste des comptes',
        'liste_cpt_bq': bq,
        'liste_cpt_pl': pl,
        'total_bq': total_bq,
        'total_pla': total_pla,
        'total': total_bq + total_pla,
        'nb_clos': nb_clos,
        'dev':settings.DEVISE_GENERALE
        })
    return HttpResponse(t.render(c))


def cpt_detail(request, cpt_id):
    c = get_object_or_404(Compte, pk=cpt_id)
    if c.type in ('t',):
        return HttpResponseRedirect(reverse('mysite.gsb.views.index'))
    t = loader.get_template('gsb/cpt_detail.django.html')
    date_limite = datetime.date.today() - datetime.timedelta(days=settings.NB_JOURS_AFF)
    q = Ope.non_meres().filter(compte__pk=cpt_id).order_by('-date').filter(date__gte=date_limite).filter(rapp__isnull=True)
    nb_ope_vielles = Ope.non_meres().filter(compte__pk=cpt_id).filter(date__lte=date_limite).filter(rapp__isnull=True).count()
    nb_ope_rapp = Ope.non_meres().filter(compte__pk=cpt_id).filter(rapp__isnull=False).count()
    if settings.UTIDEV:
        dev=c.devise.isin
    else:
        dev=settings.DEVISE_GENERALE
    return HttpResponse(
        t.render(
            RequestContext(
                request,
                {
                    'compte': c,
                    'list_ope': q,
                    'nbrapp': nb_ope_rapp,
                    'nbvielles': nb_ope_vielles,
                    'titre': c.nom,
                    'solde': c.solde(),
                    'date_limite':date_limite,
                    'dev':dev
                }

            )
        )
    )


def cpt_titre_detail(request, cpt_id):
    c = get_object_or_404(Compte_titre, pk=cpt_id)
    if c.type not in ('t'):
        return HttpResponseRedirect(reverse('gsb.views.index'))
    titre_sans_sum = Tiers.objects.filter(is_titre=True).filter(ope__compte=cpt_id).distinct()
    titres = []
    total_titres = 0
    for t in titre_sans_sum:
        mise = t.ope_set.filter(mere=None,).exclude(cat__nom='plus values latentes').aggregate(sum=models.Sum('montant'))['sum']
        pmv = t.ope_set.filter(mere=None,cat__nom='plus values latentes').aggregate(sum=models.Sum('montant'))['sum']
        total_titres = total_titres + mise + pmv
        titres.append({'nom': t.nom[7:], 'type': t.titre_set.get().get_type_display(), 'mise': mise, 'pmv': pmv, 'total': mise + pmv})
    especes = c.solde() - total_titres
    if settings.UTIDEV:
        dev=c.devise.isin
    else:
        dev=settings.DEVISE_GENERALE
    template = loader.get_template('gsb/cpt_placement.django.html')
    return HttpResponse(
        template.render(
            RequestContext(
                request,
                {
                    'compte': c,
                    'titre': c.nom,
                    'solde': c.solde(),
                    'titres': titres,
                    'especes': especes,
                }
            )
        )
    )

from django.db import connection
@login_required
def ope_detail(request, pk):
    ope = get_object_or_404(Ope, pk=pk)
    gen=Generalite.gen().dev_g()
    logger=logging.getLogger('gsb')
    if ope.jumelle is not None: #c'est un virement
        #TODO message
        #TODO redirection
        HttpResponseRedirect(reverse('mysite.gsb.views.cpt_detail',kwargs={'cpt_id':ope.compte_id}))
    if ope.filles_set.all().count()>0: #c'est une ope mere
        #TODO message
        HttpResponseRedirect(reverse('mysite.gsb.views.cpt_detail',kwargs={'cpt_id':ope.compte_id}))
    if request.method == 'POST':
        form = gsb_forms.OperationForm(request.POST)
        if form.is_valid():
            ope=form.save()
            return HttpResponseRedirect(reverse('mysite.gsb.views.cpt_detail',kwargs={'cpt_id':ope.compte_id}))
        else:
            return render(request,'gsb/ope.django.html',
            {   'titre_long':u'modification opération %s'%ope.id,
               'titre':u'modification',
                'form':form,
                'dev':gen,
                'ope':ope}
            )
    else:
        form = gsb_forms.OperationForm(instance=ope)
        t=render(request,'gsb/ope.django.html',
            {   'titre':u'modification',
               'titre_long':u'modification opération %s'%ope.id,
                'form':form,
                'dev':gen,
                'ope':ope,}
            )
        return t

@login_required
def ope_new(request,cpt=None):
    if cpt:
        cpt = get_object_or_404(Compte, pk=cpt)
    cats=Cat.objects.all().order_by('type')
    gen=Generalite.gen()
    logger=logging.getLogger('gsb')
    if request.method == 'POST':
        if cpt:
            form = gsb_forms.OperationForm(request.POST,initial={'moyen':cpt.moyen_credit_defaut})
        else:
            form = gsb_forms.OperationForm(request.POST)
        if form.is_valid():
            ope=form.save()
            #TODO message
            return HttpResponseRedirect(reverse('mysite.gsb.views.cpt_detail',kwargs={'cpt_id':ope.compte_id}))
        else:
            #TODO message
            return render(request,'gsb/ope.django.html',
            {   'titre':u'création',
                'titre_long':u'création opération',
                'form':form,
                'dev':gen.dev_g(),
                'cats':cats,
                'cpt':cpt}
            )
    else:
        form = gsb_forms.OperationForm()
        return render(request,'gsb/ope.django.html',
            {   'titre':u'création',
                'titre_long':u'création opération',
                'form':form,
                'dev':gen.dev_g(),
                'cats':cats,
                'cpt':cpt}

            )

@login_required
def vir_detail(request, pk):
    ope = get_object_or_404(Ope, pk=pk)
    if ope.jumelle is None: #ce n'est pas un virement
        #TODO message
        HttpResponseRedirect(reverse('mysite.gsb.views.ope_detail',kwargs={'pk':ope.id}))
    if ope.filles_set.all().count()>0: #c'est une ope mere (normalement ca ne doit pas exisqter)
        #TODO message
        HttpResponseRedirect(reverse('mysite.gsb.views.cpt_detail',kwargs={'cpt_id':ope.compte_id}))
    gen=Generalite.gen()
    logger=logging.getLogger('gsb')
    if request.method == 'POST':
        #TODO forms a faire
        form = gsb_forms.VirementForm(request.POST)
        if form.is_valid():
            #TODO definir le nom en fonction des comptes
            #TODO gestion des devises ou des non devises
            ope=form.save()
            return HttpResponseRedirect(reverse('mysite.gsb.views.cpt_detail',kwargs={'cpt_id':ope.compte_id}))
        else:
            #TODO template a faire
            return render(request,'gsb/vir.django.html',
            {   'titre_long':u'modification virement %s'%ope.id,
               'titre':u'modification',
                'form':form,
                'gen':gen,
                'ope':ope}
            )
    else:
        form = gsb_forms.VirementForm(instance=ope)
        t=render(request,'gsb/vir.django.html',
            {   'titre':u'modification',
               'titre_long':u'modification virement %s'%ope.id,
                'form':form,
                'gen':gen,
                'ope':ope}
            )
        return t

@login_required
def vir_new(request, pk=None):
    if pk:
        ope = get_object_or_404(Ope, pk=pk)
