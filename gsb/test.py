# -*- coding: utf-8 -*-
if __name__ == "__main__":
    from django.core.management import setup_environ
    import sys, os

    #sys.path.append(os.path.realpath(os.path.join(os.path.dirname(__file__), '../..')))
    sys.path.append(os.path.realpath(os.path.join(os.path.dirname(__file__), '..')))
    from mysite import settings

    setup_environ(settings)

import logging
from django.shortcuts import render
from django.template import RequestContext
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP #@UnusedImport
from mysite.gsb.models import * #@UnusedWildImport
from django.utils import formats#@UnusedImport
from django.utils.encoding import smart_unicode #@UnusedImport
from django.utils.safestring import mark_safe #@UnusedImport
logger = logging.getLogger('gsb.test')
from django.shortcuts import render, get_object_or_404
from django.forms.models import modelformset_factory
def test(request):
    cpt_id = 6
    cpt = get_object_or_404(Compte_titre.objects.select_related(), pk = cpt_id)
    formset = modelformset_factory(Ope_titre, max_num = 4, extra = 4)
    if request.method == 'POST':
        form = modelformset_factory(request.POST)
    else:
        form = formset(queryset = Ope_titre.objects.none())
    return render(request, 'gsb/test.djhtm', {'formset':form, 'titre':'test'})

if __name__ == "__main__":
    c = Compte_titre.objects.get(id = 4)
    t = Titre.objects.get(id=1)
    v=Compte.objects.get(id = 1)
    Ope_titre.objects.create(titre = t,
                                    compte = c,
                                    nombre = 20,
                                    date = '2011-01-01',
                                    cours = 1)


