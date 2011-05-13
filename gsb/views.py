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

def index(request):
    t = loader.get_template('gsb/index.django.html')
    bq = Compte.objects.filter(type__in=('b', 'e')).select_related()
    pl = Compte.objects.filter(type__in=('a', 'p')).select_related()
    total_bq = Ope.objects.filter(mere__exact=None,compte__type__in=('b','e')).aggregate(solde=models.Sum('montant'))['solde']
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

    total_pla = Ope.objects.filter(mere__exact=None,compte__type__in=('a','p')).aggregate(solde=models.Sum('montant'))['solde']
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
    q = Ope.objects.filter(compte__pk=cpt_id).order_by('-date').filter(date__gte=date_limite).filter(is_mere=False).filter(rapp__isnull=True).select_related()
    nb_ope_vielles = Ope.objects.filter(compte__pk=cpt_id).filter(date__lte=date_limite).filter(is_mere=False).filter(rapp__isnull=True).count()
    nb_ope_rapp = Ope.objects.filter(compte__pk=cpt_id).filter(is_mere=False).filter(rapp__isnull=False).count()
    p = list(q)
    return HttpResponse(
        t.render(
            RequestContext(
                request,
                {
                    'compte': c,
                    'list_ope': p,
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
        mise = t.ope_set.exclude(is_mere=True).exclude(cat__nom='plus values latentes').aggregate(sum=models.Sum('montant'))['sum']
        pmv = t.ope_set.exclude(is_mere=True).filter(cat__nom='plus values latentes').aggregate(sum=models.Sum('montant'))['sum']
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


def ope_detail2(request, ope_id):
    p = get_object_or_404(Ope, pk=ope_id)
    #depenses_cat=Cat.objects.filter(type='d').select_related()
    cats_debit=[]
    cats_credit=[]
    for  cat in Cat.objects.all().select_related():
        if cat.scat_set.all():
            for scat in cat.scat_set.all():
                if cat.type=='d':
                    cats_debit.append({'id':"%s : %s"%(cat.id,scat.id),
                                   'nom':"%s:%s"%(cat.nom,scat.nom),
                            })
                else:
                    cats_credit.append({'id':"%s : %s"%(cat.id,scat.id),
                                   'nom':"%s:%s"%(cat.nom,scat.nom),
                            })
        else:
            if cat.type=='d':
                cats_debit.append({'id':"%s : %s"%(cat.id,0),
                               'nom':"%s:%s"%(cat.nom,""),
                        })
            else:
                cats_credit.append({'id':"%s : %s"%(cat.id,0),
                               'nom':"%s:%s"%(cat.nom,""),
                        })


    return render_to_response('gsb/operation.django.html',
                              {'ope': p,
                               'titre': "edition",
                               'compte': p.compte,
                               'action': 'edit',
                               'cats_debit':cats_debit,
                               'cats_credit':cats_credit,
                               'tiers':Tiers.objects.filter(is_titre=False)},
                              context_instance=RequestContext(request)
    )


def ope_creation(request, cpt_id):
    cpt = get_object_or_404(Compte, pk=cpt_id)
    devise = cpt.devise
    ope = Ope(compte=cpt, date=datetime.date.today(), montant=0, devise=devise, tiers=None, cat=None, scat=None,
              Notes=None, moyen=None, numcheque="", )
    pass


def virement_creation(request, cpt_id):
    pass

def ope_detail(request, ope_id):
    form= gsb_forms.OperationForm
    return  render_to_response('gsb/test.django.html',
        {'form':form}
    )

