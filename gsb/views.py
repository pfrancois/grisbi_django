# -*- coding: utf-8 -*-
# Create your views here.
from django.template import RequestContext, loader
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.conf import settings
from django.shortcuts import render, get_object_or_404
from mysite.gsb.models import Generalite, Compte, Ope, Compte_titre, Tiers, Virement, Cat
import datetime
import mysite.gsb.forms as gsb_forms
from django.db import models
import decimal
import logging #@UnusedImport
from django.contrib.auth.decorators import login_required

def index(request):
    """
    view index
    """
    t = loader.get_template('gsb/index.django.html')
    if Generalite.gen().affiche_clot:
        bq = Compte.objects.filter(type__in=('b', 'e', 'p')).select_related()
        pl = Compte_titre.objects.all().select_related()
    else:
        bq = Compte.objects.filter(type__in=('b', 'e', 'p'), ouvert=True).select_related()
        pl = Compte_titre.objects.filter(ouvert=True).select_related()
    total_bq = Ope.objects.filter(mere__exact=None, compte__type__in=('b', 'e', 'p')).aggregate(solde=models.Sum('montant'))['solde']
    total_pla = decimal.Decimal('0')
    for p in pl:
        total_pla = total_pla + p.solde()
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
    '''
    view qui affiche la liste des operation de ce compte
    @param request:
    @param cpt_id: id du compte demande
    '''
    c = get_object_or_404(Compte, pk=cpt_id)
    date_limite = datetime.date.today() - datetime.timedelta(days=settings.NB_JOURS_AFF)
    if c.type in ('t',):
        c = get_object_or_404(Compte_titre, pk=cpt_id)
        titre = True
    else:
        titre = False
    t = loader.get_template('gsb/cpt_detail.django.html')
    if not titre:
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
    else:
        #recupere la liste des titres qui sont utilise dans ce compte
        titre_sans_sum = Tiers.objects.filter(is_titre=True).filter(ope__compte=cpt_id).distinct()
        titres = []
        total_titres = 0
        for t in titre_sans_sum:
            invest = t.ope_set.filter(mere=None,).aggregate(sum=models.Sum('montant'))['sum']
            print invest
            total = 0
            titres.append({'nom': t.nom[7:], 'type': t.titre_set.get().get_type_display(), 'invest': invest, 'pmv': total - invest, 'total': total})
        especes = c.solde - total_titres
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

@login_required
def ope_detail(request, pk):
    '''
    view, une seule operation
    @param request:
    @param pk: id de l'ope
    '''
    ope = get_object_or_404(Ope, pk=pk)
    #logger = logging.getLogger('gsb')
    if ope.jumelle is not None: #c'est un virement
        if request.method == 'POST':#creation du virement
            form = gsb_forms.VirementForm(request.POST)
            if form.is_valid():
                return HttpResponseRedirect(reverse('mysite.gsb.views.cpt_detail', kwargs={'cpt_id':ope.compte_id}))
            else:
                return render(request, 'gsb/vir.django.html',
                {   'titre_long':u'modification virement interne %s' % ope.id,
                   'titre':u'modification',
                    'form':form,
                    'ope':ope}
                )
        else:#modification du virement
            #initialisation form
            form = gsb_forms.VirementForm(Virement(ope).init_form())
            return render(request, 'gsb/vir.django.html',
                {   'titre':u'modification',
                   'titre_long':u'modification virement interne %s' % ope.id,
                    'form':form,
                    'ope':ope}
                )
    else:#sinon c'est une operation normale
        if ope.filles_set.all().count() > 0: #c'est une ope mere
            #TODO message
            HttpResponseRedirect(reverse('mysite.gsb.views.cpt_detail', kwargs={'cpt_id':ope.compte_id}))
        if request.method == 'POST':
            form = gsb_forms.OperationForm(request.POST)
            if form.is_valid():
                ope = form.save()
                return HttpResponseRedirect(reverse('mysite.gsb.views.cpt_detail', kwargs={'cpt_id':ope.compte_id}))
            else:
                return render(request, 'gsb/ope.django.html',
                {   'titre_long':u'modification opération %s' % ope.id,
                   'titre':u'modification',
                    'form':form,
                    'ope':ope}
                )
        else:
            form = gsb_forms.OperationForm(instance=ope)
            t = render(request, 'gsb/ope.django.html',
                {   'titre':u'modification',
                   'titre_long':u'modification opération %s' % ope.id,
                    'form':form,
                    'ope':ope, }
                )
            return t

@login_required
def ope_new(request, cpt_id=None):
    if cpt_id:
        cpt = get_object_or_404(Compte, pk=cpt_id)
    else:
        cpt = None
    cats = Cat.objects.all().order_by('type')
    #logger = logging.getLogger('gsb')
    if request.method == 'POST':
        form = gsb_forms.OperationForm(request.POST)
        if form.is_valid():
            ope = form.save()
            #TODO message
            return HttpResponseRedirect(reverse('mysite.gsb.views.cpt_detail', kwargs={'cpt_id':ope.compte_id}))
        else:
            #TODO message
            return render(request, 'gsb/ope.django.html',
            {   'titre':u'création',
                'titre_long':u'création opération',
                'form':form,
                'cats':cats,
                'cpt':cpt}
            )
    else:
        if cpt_id:
            form = gsb_forms.OperationForm(initial={'moyen':cpt.moyen_debit_defaut})
        else:
            form = gsb_forms.OperationForm()

        return render(request, 'gsb/ope.django.html',
            {   'titre':u'création',
                'titre_long':u'création opération',
                'form':form,
                'cats':cats,
                'cpt':cpt}
            )

@login_required
def vir_new(request, cpt_id=None):
    if cpt_id:
        cpt = get_object_or_404(Compte, pk=cpt_id)
    else:
        cpt = None
    #logger = logging.getLogger('gsb')
    if request.method == 'POST':
        form = gsb_forms.VirementForm(request.POST)
        if form.is_valid():
            ope = form.save()
            return HttpResponseRedirect(reverse('mysite.gsb.views.cpt_detail', kwargs={'cpt_id':ope.compte_id}))
        else:
            return render(request, 'gsb/vir.django.html',
            {   'titre_long':u'création virement interne ',
               'titre':u'Création',
                'form':form,
                'cpt':cpt}
            )
    else:
        if cpt_id:
            form = gsb_forms.VirementForm(initial={'moyen_origine':cpt.moyen_debit_defaut})
        else:
            form = gsb_forms.VirementForm()
        return render(request, 'gsb/vir.django.html',
            {   'titre':u'Création',
               'titre_long':u'Création virement interne ',
                'form':form,
                'cpt':cpt}
            )
