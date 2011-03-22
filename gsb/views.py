# -*- coding: utf-8 -*-
# Create your views here.
from django.template import RequestContext, loader
from mysite.gsb.models import Compte, Ope
from django.http import HttpResponse, Http404
import datetime
import settings
from django.shortcuts import render_to_response, get_list_or_404,get_object_or_404
def index(request):
    t=loader.get_template('index.django.html')
    bq=Compte.objects.filter(type__in=(u'b',u'e'))
    pl=Compte.objects.filter(type__in=(u'a',u'p'))
    total_pla = 0
    total_bq = 0
    for compte in bq:
        total_bq=total_bq+compte.solde()
    for compte in pl:
        total_pla=total_pla+compte.solde()
    nb_clos = len(Compte.objects.filter(cloture=True))
    c = RequestContext(request, {
        'titre':'liste des comptes',
        'liste_cpt_bq': bq,
        'liste_cpt_pl': pl,
        'total_bq' : total_bq,
        'total_pla' : total_pla,
        'total' : total_bq + total_pla,
        'nb_clos' : nb_clos,

    })
    return HttpResponse(t.render(c))

#def ope_index(request,ope_id):
#    p = get_object_or_404(Ope,pk=ope_id)
#    return render_to_response('detail_ope.django.html', {'ope': p})
#
def cpt_detail(request,cpt_id):
    #p = get_list_or_404(Ope,compte__pk=cpt_id)
    #return render_to_response('cpt_detail.django.html', {'list_ope': p}, context_instance=RequestContext(request))
    t = loader.get_template('cpt_detail.django.html')
    date_limite=datetime.date.today()-datetime.timedelta(days=settings.NB_JOURS_AFF)
    p = list(Ope.objects.filter(compte__pk=cpt_id).order_by('-date').filter(date__gte=date_limite).filter(is_mere=False))
    if not p:
        raise Http404
    c = get_object_or_404(Compte,pk=cpt_id)
    return HttpResponse(t.render(RequestContext(request, {
        'compte':c,
        'list_ope': p,
        'nbrapp': 0,
        'titre': c.nom,
        'tiers': Tiers.objects.all()
        })))

def creation_ope(request,cpt_id):
    pass

def ope_detail(request,ope_id):
    p = get_object_or_404(Ope,pk=ope_id)
    return render_to_response('operation.django.html',
                                            {'ope': p,
                                              'titre':"edition ",
                                              'compte_id':p.compte.id,
                                              'action':'edit'},
                                            context_instance=RequestContext(request)
                                        )

def creation_virement(request,cpt_id):
    pass
