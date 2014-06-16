# -*- coding: utf-8 -*-
from __future__ import absolute_import
import logging
import os
import codecs
import pprint

from django.test import TestCase as Test_Case_django
from django.test.utils import override_settings
from django.test.client import RequestFactory
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.messages import get_messages
from django.conf import settings
from unittest.util import safe_repr
from gsb import utils

#from operator import attrgetter

__all__ = ['TestCase']


@override_settings(REV_PLAC=68)
@override_settings(ID_CPT_M=1)
@override_settings(MD_DEBIT=1)
@override_settings(MD_CREDIT=4)
@override_settings(ID_CAT_COTISATION=54)
@override_settings(ID_TIERS_COTISATION=256)
@override_settings(ID_CAT_PMV=67)
@override_settings(ID_CAT_OST=64)
@override_settings(ID_CAT_VIR=65)
class TestCase(Test_Case_django):
    #reset_sequences = True
    def setUp(self):
        # supprime l'affichage des probleme de 404
        logger = logging.getLogger('django.request')
        logger.setLevel(logging.ERROR)
        super(TestCase, self).setUp()

    def setup_view(self, view, request, *args, **kwargs):
        """Mimic as_view() returned callable, but returns view instance.
        args and kwargs are the same you would pass to ``reverse()``
        """
        view.request = request
        view.args = args
        view.kwargs = kwargs
        return view

    def request_get(self, url):
        factory = RequestFactory()
        request = factory.get(url)
        setattr(request, 'session', 'session')
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)
        return request

    def request_post(self, url):
        factory = RequestFactory()
        request = factory.post(url)
        setattr(request, 'session', 'session')
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)
        return request

    def assertQueryset_list(self, qs1, liste, element="pk"):
        # compare les id d'un query set avec une liste
        # mais avantil faut preparer la liste
        items = list()
        compfr = utils.Compfr()
        for obj in qs1:
            items.append(getattr(obj, element))
        items.sort(cmp=compfr)
        if not hasattr(liste, "__iter__"):
            liste = (liste,)
        diff = ([x for x in list(items) if x not in liste], [x for x in liste if x not in list(items)])
        return self.assertEqual(sorted(items), sorted(liste), diff)

    # noinspection PyProtectedMember
    def assertcountmessage(self, request, nb, liste=False):
        messages = get_messages(request)
        actual = len([e.message for e in messages])
        if actual != nb:
            if liste:
                messages_str = pprint.pformat(['"%s"' % m for m in messages],indent=4)
                self.fail('Message count was %s, expected %s. list of messages: \n %s' % (actual, nb,
                                                                                         messages_str))
            else:
                self.fail('Message count was %s, expected %s' % (safe_repr(actual), safe_repr(nb)))

    # noinspection PyProtectedMember
    def assertmessagecontains(self, request, text, level=None):
        messages = get_messages(request)
        matches = [m for m in messages if text == m.message]
        if len(matches) > 0:
            msg = matches[0]
            if level is not None and msg.level != level:
                self.fail('There was one matching message but with different level: %s != %s' % (safe_repr( msg.level), safe_repr(level)))
            else:
                return
        else:
            messages_str = pprint.pformat(['"%s"' % m for m in messages],indent=4)
            self.fail("No message contained text '%s', messages were: \n%s" % (text, messages_str))

    def assertreponsequal(self, reponse_recu, reponse_attendu, fichier=False, unicode_encoding=None, nom=""):
        if nom != "":
            nom = "%s_" % nom
        if unicode_encoding is None:
            unicode_encoding = "utf-8"
        rr_iter = reponse_recu.splitlines()
        if not fichier:
            ra_iter = reponse_attendu.splitlines()
        else:  # c'est le cas des fichier par exemple
            ra_iter = []
            for r in reponse_attendu:
                if not isinstance(r, unicode):
                    r = r.decode(unicode_encoding)
                r = r.replace('\n', '')
                r = r.replace('\r', '')
                ra_iter.append(r)
        try:
            fichier = codecs.open(os.path.join(settings.PROJECT_PATH, "upload", "%srecu.txt" % nom), 'w', "utf-8")
            for l in rr_iter:
                fichier.write(l)
                fichier.write('\n')
            fichier.close()
            fichier = codecs.open(os.path.join(settings.PROJECT_PATH, "upload", "%sattendu.txt" % nom), 'w', unicode_encoding)
            for l in ra_iter:
                fichier.write(l)
                fichier.write('\n')
        finally:
            fichier.close()
        if len(ra_iter) != len(rr_iter):
            msg = "nb ligne recu:%s != nb ligne attendu:%s" % (len(rr_iter), len(ra_iter))
            raise self.fail(msg)
        msg = u""
        for ra, rr in zip(ra_iter, rr_iter):
            if not isinstance(ra, unicode):
                ra = unicode(ra, unicode_encoding)
            if rr != ra:
                msg = u"%s\nrecu:'%s'\natt :'%s'" % (msg, rr, ra)
        if msg != u"":
            raise self.fail(msg)

    def assertfileequal(self, reponse_recu, fichier, unicode_encoding=None, nom=""):
        fichier = open(os.path.join(settings.PROJECT_PATH, "gsb", "test_files", fichier), 'r')
        attendu = fichier.readlines()
        fichier.close()
        self.assertreponsequal(reponse_recu, attendu, True, unicode_encoding, nom)
