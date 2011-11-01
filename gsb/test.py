# -*- coding: utf-8 -*-
try:
    from mysite import settings

    main = False
except ImportError:
    main = True
    from django.core.management import setup_environ
    import sys, os
    #sys.path.append(os.path.realpath(os.path.join(os.path.dirname(__file__), '../..')))
    s = os.path.realpath(os.path.join(os.path.dirname(__file__), '../..'))
    sys.path.append(s)
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
from mysite.gsb.utils import validrib

def test(request):
    cpt_id = 6
    cpt = get_object_or_404(Compte_titre.objects.select_related(), pk=cpt_id)
    formset = modelformset_factory(Ope_titre, max_num=4, extra=4)
    if request.method == 'POST':
        form = modelformset_factory(request.POST)
    else:
        form = formset(queryset=Ope_titre.objects.none())
    return render(request, 'gsb/test.djhtm', {'formset':form, 'titre':'test'})

if main:
    s = 'abcd'
    before = ['&#232', '&#233', '&#234', '&#244']
    after = ['&#xE8', '&#xE9', '&#xEA', '&#xF4']
    for car in before:
        s = s.replace(car, after[before.index(car)])
