# -*- coding: utf-8 -*-
# Create your views here.
from django.template import Context, loader
from grisbi.gsb.models import Compte, Ope
from django.http import HttpResponse
from django.http import Http404
#def index(request):
#    t=loader.get_template('index.html')
#    total_bq = 0
#    total_pla = 0
#    nb_clos = 0
#    c = Context({
#        'liste_cpt_bq': Compte.Objects.filter(type=(u'bq',u'esp')),
#        'liste_cpt_pl': Compte.Objects.filter(type=(u'a',u'p')),
#        'total_bq' : total_bq, #XXX
#        'total_pla' : total_pla, #XXX
#        'total' : total_bq + total_pla,
#        'nb_clos' : nbclos,
#
#    })
#    return HttpResponse(t.render(c))

#def ope_index(request,ope_id):
#    p = get_object_or_404(Ope,pk=ope_id)
#    return render_to_response('detail_ope.html', {'ope': p})
#
#def cpt_index(request,cpt_id):
#    p = get_object_or_404(Compte,pk=cpt_id)
#    return render_to_response('detail_cpt.html', {'cpt': p})
