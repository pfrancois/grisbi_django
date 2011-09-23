# -*- coding: utf-8 -*-
if __name__ == "__main__":
    from django.core.management import setup_environ
    import sys, os

    sys.path.append(os.path.realpath(os.path.join(os.path.dirname(__file__), '../..')))
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
    nomfich = "%s/20040701.gsb" % (os.path.dirname(os.path.abspath(__file__)))
    #nomfich = "%s/test_files/test_original.gsb" % (os.path.dirname(os.path.abspath(__file__)))
    nomfich = os.path.normpath(nomfich)
    logger.setLevel(40)#change le niveau de log (10 = debug, 20=info)
    xml_tree = et.parse(nomfich)
    xml_tree.getroot()
    list_ope = xml_tree.findall('//Operation')
    nb_ope_final = len(list_ope)
    percent = 1
    for xml_ope in list_ope:
        if xml_ope.get('N'):
            print smart_unicode(xml_ope.get('N'))
            print xml_ope.get('N')


