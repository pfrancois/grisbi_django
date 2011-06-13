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
        bq = Compte.objects.filter(type__in=('b', 'e')).select_related()
        pl = Compte.objects.filter(type__in=('a', 'p')).select_related()
    else:
        bq = Compte.objects.filter(type__in=('b', 'e'),ouvert=True).select_related()
        pl = Compte.objects.filter(type__in=('a', 'p'),ouvert=True).select_related()
    total_bq=decimal.Decimal('0')
    total_pla=decimal.Decimal('0')
    for c in bq:
        total_bq=total_bq+c.solde(devise_generale=True)
    for p in pl:
        total_pla=total_pla+p.solde(devise_generale=True)
    nb_clos = len(Compte.objects.filter(ouvert=False))
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
    c = get_object_or_404(Compte_titre, pk=cpt_id)
    if c.type == 'b':
        return HttpResponseRedirect(reverse('gsb.views.index'))
    if c.type == 'e':
        return HttpResponseRedirect(reverse('gsb.views.index'))
    if c.type == 'p':
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

@login_required
def ope_detail(request, pk):
    ope = get_object_or_404(Ope, pk=pk)
    cats=Cat.objects.all().order_by('type')
    gen=Generalite.gen()
    logger=logging.getLogger('gsb')
    if request.method == 'POST':
        form = gsb_forms.OperationForm(request.POST)
        if form.is_valid():
            ope=form.save()
            return HttpResponseRedirect(reverse('mysite.gsb.views.cpt_detail',kwargs={'cpt_id':ope.compte_id}))
        else:
            return render(request,'gsb/ope.django.html',
            {   'titre':u'édition opération',
                'form':form,
                'gen':gen,
                'ope':ope,
                'cats':cats}
            )
    else:
        form = gsb_forms.OperationForm(instance=ope)
        return render(request,'gsb/ope.django.html',
            {   'titre':u'édition opération',
                'form':form,
                'gen':gen,
                'ope':ope,
                'cats':cats}
            )
