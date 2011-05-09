# -*- coding: utf-8 -*-
# Create your views here.
from django.template import RequestContext, loader
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.conf import settings
from django.shortcuts import render_to_response, get_object_or_404
from mysite.gsb.models import *
import mysite.gsb.forms as gsb_forms
import mysite.gsb.import_gsb as import_gsb
import logging

def index(request):
    t = loader.get_template('gsb/index.django.html')
    bq = Compte.objects.filter(type__in=(u'b', u'e'))
    pl = Compte.objects.filter(type__in=(u'a', u'p'))
    total_pla = 0
    total_bq = 0
    for compte in bq:
        total_bq = total_bq + compte.solde()
    for compte in pl:
        total_pla = total_pla + compte.solde()
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


def ope_detail(request, ope_id):
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


def import_file(request):
    import mysite.gsb.import_gsb
    if request.method == 'POST':
        form = gsb_forms.ImportForm(request.POST, request.FILES)
        if form.is_valid():

            mysite.gsb.import_gsb.import_gsb(request.FILES['file'], 1)
            return HttpResponseRedirect(reverse('mysite.gsb.views.index'))
    else:
        form = gsb_forms.ImportForm()
    return render_to_response('gsb/import.django.html',
                              {'form': form,
                               'titre':"importation d'un fichier"},
                              context_instance=RequestContext(request))

def options(request):
    return render_to_response('gsb/options.django.html', context_instance=RequestContext(request))

