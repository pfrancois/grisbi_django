# -*- coding: utf-8 -*-
if __name__ == "__main__":
    from django.core.management import setup_environ
    import sys, os

    sys.path.append(os.path.realpath(os.path.join(os.path.dirname(__file__), '../..')))
    sys.path.append(os.path.realpath(os.path.join(os.path.dirname(__file__), '..')))
    from mysite import settings

    setup_environ(settings)

import logging
from django.shortcuts import render_to_response
from django.template import RequestContext
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP #@UnusedImport
from mysite.gsb.models import * #@UnusedWildImport
from django.utils import formats#@UnusedImport
from django.utils.encoding import smart_unicode #@UnusedImport
from django.utils.safestring import mark_safe #@UnusedImport
logger = logging.getLogger('gsb.test')
from annoying.functions import get_config


def test(request):
    logger = logging.getLogger('gsb.test')
    logger.debug('test')
    logger.info(3)
    logger.critical('attention ce est un test critique')
    print get_config('ADMIN_EMAIL', 'default@email.com')
    return render_to_response('gsb/test.djhtm',
                                            {'titre':"TEST",
                                                'test':'test'},
                                            context_instance = RequestContext(request))

if __name__ == "__main__":
        c = Compte_titre.objects.get(id = 4)
        t = Titre.objects.get(nom = "t1")
        c.achat(titre = t, nombre = 20, date = '2011-01-01', virement_de = Compte.objects.get(id = 1))
        t.cours_set.create(date = '2011-02-01', valeur = 2)
        c.vente(t, 10, 3, '2011-06-30', virement_vers = Compte.objects.get(id = 1))
        print Ope_titre.investi(c, t)



