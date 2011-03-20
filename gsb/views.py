# -*- coding: utf-8 -*-
# Create your views here.
from django.template import RequestContext, loader
from mysite.gsb.models import Compte, Ope
from django.http import HttpResponse
from django.http import Http404
def index(request):
    t=loader.get_template('index.html')
    bq=Compte.objects.filter(type__in=(u'b',u'e'))
    pl=Compte.objects.filter(type__in=(u'a',u'p'))
    total_pla = 0
    total_bq = 0
    for compte in bq:
        total_bq=total_bq+compte.solde()
    for compte in pl:
        total_pla=total_pla+compte.solde()
    nb_clos = len(Compte.objects.filter(compte_cloture=False))
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
#    return render_to_response('detail_ope.html', {'ope': p})
#
def cpt_index(request,cpt_id):
    p = get_object_or_404(Compte,pk=cpt_id)
    return render_to_response('cpt_detail.html', {'cpt': p})
# Create your views here.
