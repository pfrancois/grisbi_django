# -*- coding: utf-8 -*-

import logging
import os

from django.test import TestCase as Test_Case_django
from django.test.utils import override_settings
from django.test.client import RequestFactory
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.messages import get_messages
from django.conf import settings
from unittest.util import safe_repr
from testfixtures import compare
from datetime import timedelta


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

    class add_minutes:
        def __init__(self, date_init):
            self.date = date_init

        def now(self):
            output = self.date
            self.date = self.date + timedelta(minutes=1)
            return output

    # reset_sequences = True
    def compare(self, x, y, **kw):
        return compare(x, y, **kw)

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
        for obj in qs1:
            items.append(getattr(obj, element))
        items.sort()
        if not hasattr(liste, "__iter__"):
            liste = (liste,)
        diff = ([x for x in list(items) if x not in liste], [x for x in liste if x not in list(items)])
        return self.assertEqual(sorted(items), sorted(liste), diff)

    def assertcountmessage(self, request, nb, liste=False):
        messages = get_messages(request)
        actual = len([e.message for e in messages])
        if actual != nb:
            if liste:
                messages_str = "[\n"
                for m in messages:
                    messages_str += "\t'" + m.message + "',\n"
                    messages_str += "]"
                self.fail('Message count was %s, expected %s. list of messages: \n %s' % (actual, nb, messages_str))
            else:
                self.fail('Message count was %s, expected %s' % (safe_repr(actual), safe_repr(nb)))

    def assertmessagecontains(self, request, text, level=None):

        messages = get_messages(request)
        matches = []
        for m in messages:
            if text == m.message:
                matches.append(m)
        if len(matches) > 0:
            msg = matches[0]
            if level is not None and msg.level != level:
                self.fail('There was one matching message but with different level: %s != %s' % (
                    safe_repr(msg.level), safe_repr(level)))
            else:
                return
        else:
            messages_str = "[\n"
            for m in messages:
                messages_str += "\t'" + m.message + "',\n"
            messages_str += "]"
            self.fail("No message contained text '%s', messages were: \n%s" % (text, messages_str))

    def assertreponsequal(self, reponse_recu, reponse_attendu, fichier=False, nom=""):
        rr_iter = list()
        ra_iter = list()
        if nom != "":
            nom = "%s_" % nom
        try:
            for l in reponse_recu.splitlines():
                rr_iter.append(l)
        except AttributeError:
            for l in reponse_recu:
                rr_iter.append(l)
        if not fichier:
            try:
                for l in reponse_attendu.splitlines():
                    ra_iter.append(l)
            except AttributeError:
                for l in reponse_attendu:
                    ra_iter.append(l)
        else:  # c'est le cas des fichier par exemple
            ra_iter = []
            for l in reponse_attendu:
                l = l.replace('\n', '')
                l = l.replace('\r', '')
                ra_iter.append(l)
        try:
            fichier = open(os.path.join(settings.PROJECT_PATH, "upload", "%s_recu.txt" % nom), 'w', encoding="utf-8", newline='')
            for l in rr_iter:
                fichier.write(l)
                fichier.write('\n')
            fichier.close()
            fichier = open(os.path.join(settings.PROJECT_PATH, "upload", "%s_attendu.txt" % nom), 'w', encoding="utf-8", newline='')
            for l in ra_iter:
                fichier.write(l)
                fichier.write('\n')
        finally:
            fichier.close()
        compare("\n".join(ra_iter), "\n".join(rr_iter))

    def assert2filesequal(self, nom_fichier_recu, nom_fichier_attendu, nom="", encoding1="utf-8", encoding2="utf-8"):
        #on test que les deux fichiers existent
        if not os.path.isfile(os.path.join(settings.PROJECT_PATH, "gsb", "test_files", nom_fichier_recu)):
            self.fail("%s inexistant" % nom_fichier_recu)
        if not os.path.isfile(os.path.join(settings.PROJECT_PATH, "gsb", "test_files", nom_fichier_attendu)):
            self.fail("%s inexistant" % nom_fichier_attendu)
        #mqintenant que les deux fichiers existent
        with open(os.path.join(settings.PROJECT_PATH, "gsb", "test_files", nom_fichier_recu), 'r', encoding=encoding1) as fichier_recu:
            reponse_recu = fichier_recu.read().splitlines()
        with open(os.path.join(settings.PROJECT_PATH, "gsb", "test_files", nom_fichier_attendu), 'r', encoding=encoding1) as fichier_attendu:
            attendu = fichier_attendu.read().splitlines()
        self.assertreponsequal(reponse_recu, attendu, fichier=False, nom=nom)
