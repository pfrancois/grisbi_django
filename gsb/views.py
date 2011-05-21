# -*- coding: utf-8 -*-
# Create your views here.
from django.template import RequestContext, loader
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.conf import settings
from django.shortcuts import render_to_response, get_object_or_404
from mysite.gsb.models import *
import mysite.gsb.forms as gsb_forms
from django.db import models
import decimal
import logging
from django.contrib.auth.decorators import login_required

def index(request):
    t = loader.get_template('gsb/index.django.html')
    if Generalite.gen().affiche_clot:
        bq = Compte.objects.filter(type__in=('b', 'e')).select_related()
        pl = Compte.objects.filter(type__in=('a', 'p')).select_related()
        total_bq = Ope.objects.filter(mere__exact=None,compte__type__in=('b','e')).aggregate(solde=models.Sum('montant'))['solde']
        total_pla = Ope.objects.filter(mere__exact=None,compte__type__in=('a','p')).aggregate(solde=models.Sum('montant'))['solde']
    else:
        bq = Compte.objects.filter(type__in=('b', 'e'),cloture=False).select_related()
        pl = Compte.objects.filter(type__in=('a', 'p'),cloture=False).select_related()
        total_bq = Ope.objects.filter(mere__exact=None,compte__type__in=('b','e'),compte__cloture=False).aggregate(solde=models.Sum('montant'))['solde']
        total_pla = Ope.objects.filter(mere__exact=None,compte__type__in=('a','p'),compte__cloture=False).aggregate(solde=models.Sum('montant'))['solde']
    solde_init_bq=bq.aggregate(init=models.Sum('solde_init'))['init']
    if total_bq:
        if solde_init_bq:
            total_bq=total_bq+solde_init_bq
        else:
            total_bq=total_bq
    else:
        if solde_init_bq:
            total_bq=solde_init_bq
        else:
            total_bq=decimal.Decimal('0')
    solde_init_pla=pl.aggregate(init=models.Sum('solde_init'))['init']
    if total_pla:
        if solde_init_pla:
            total_pla=total_pla+solde_init_pla
        else:
            total_pla=total_pla
    else:
        if solde_init_pla:
            total_pla=solde_init_pla
        else:
            total_pla=decimal.Decimal('0')
    nb_clos = len(Compte.objects.filter(cloture=True))
    c = RequestContext(request, {
        'titre': 'liste des comptes',
        'liste_cpt_bq': bq,
        'liste_cpt_pl': pl,
        'total_bq': total_bq,
        'total_pla': total_pla,
        'total': total_bq + total_pla,
        'nb_clos': nb_clos,

        })
    return HttpResponse(t.render(c))


def cpt_detail(request, cpt_id):
    c = get_object_or_404(Compte, pk=cpt_id)
    if c.type == 'a':
        return HttpResponseRedirect(reverse('mysite.gsb.views.index'))
    if c.type == 'p':
        return HttpResponseRedirect(reverse('mysite.gsb.views.index'))
    t = loader.get_template('gsb/cpt_detail.django.html')
    date_limite = datetime.date.today() - datetime.timedelta(days=settings.NB_JOURS_AFF)
    q = Ope.non_meres().filter(compte__pk=cpt_id).order_by('-date').filter(date__gte=date_limite).filter(rapp__isnull=True)
    nb_ope_vielles = Ope.non_meres().filter(compte__pk=cpt_id).filter(date__lte=date_limite).filter(rapp__isnull=True).count()
    nb_ope_rapp = Ope.non_meres().filter(compte__pk=cpt_id).filter(rapp__isnull=False).count()
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
                    }
            )
        )
    )


def cpt_titre_detail(request, cpt_id):
    c = get_object_or_404(Compte, pk=cpt_id)
    if c.type == 'b':
        return HttpResponseRedirect(reverse('mysite.gsb.views.index'))
    if c.type == 'e':
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

def ope_creation(request, cpt_id=0):
    cpt = get_object_or_404(Compte, pk=cpt_id)
    devise = cpt.devise
    ope = Ope(compte=cpt, date=datetime.date.today(), montant=0, devise=devise, tiers=None, cat=None, Notes=None, moyen=None, numcheque="", )
    pass

def virement_creation(request, cpt_id):
    pass
    
def ope_detail(request, ope_id):
    ope = get_object_or_404(Ope, pk=ope_id)
    if request.method == 'POST':
        pass
    else:
        gen=Generalite.gen()
        form = gsb_forms.OperationForm(instance=ope)
        cats=Cat.objects.all().order_by('type')
        return  render_to_response('gsb/test.django.html',
            {   'titre':u'édition opération',
                'form':form,
                'gen':gen,
                'ope':ope,
                'cats':cats},
            context_instance=RequestContext(request)
        )

