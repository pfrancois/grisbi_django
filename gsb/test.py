# -*- coding: utf-8 -*-
if __name__ == "__main__":
    from django.core.management import setup_environ
    import sys, os

    sys.path.append(os.path.realpath(os.path.join(os.path.dirname(__file__), '../..')))
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
from annoying.functions import get_config


def test(request):
    from mysite.gsb.forms_perso import majPEE
    if request.method == 'POST':
        form = majPEE(request.POST)
    else:
        form = majPEE()
    return render(request, 'gsb/achat_PEE.djhtm', {'form':form})

if __name__ == "__main__":
    pass

