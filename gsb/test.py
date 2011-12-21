# -*- coding: utf-8 -*-
from __future__ import absolute_import

try:
    if DJANGO_SETTINGS_MODULE:
        pass
    main = False
except NameError:
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

#logger = logging.getLogger('gsb.test')
from django.shortcuts import render, get_object_or_404
from django.forms.models import modelformset_factory
from mysite.gsb.utils import validrib
from django.contrib import messages
from django.db import models
import decimal

def test(request):
    messages.info(request, 'This is an info message.')
    messages.info(request, 'This is another info message.')
    messages.success(request, 'This is a success message.')
    messages.warning(request, 'This is a warning message.')
    messages.error(request, 'This is an error message.')
    messages.error(request, 'This is another error message.')
    return render(request, 'generic.djhtm', )

if main:
    #c = Compte_titre.objects.get(id=4)
    #print  c.solde(rapp=True)
    print decimal.Decimal("%.2f" % (2/3*4))

