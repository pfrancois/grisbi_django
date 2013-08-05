# -*- coding: utf-8 -*-
from __future__ import absolute_import
from django.test import TestCase as Test_Case_django
from django.test.utils import override_settings
from django.test.client import RequestFactory
from django.contrib.messages.storage.fallback import FallbackStorage
import logging


@override_settings(ID_CPT_M=1)
@override_settings(MD_DEBIT=1)
@override_settings(MD_CREDIT=4)
@override_settings(ID_CAT_COTISATION=3)
@override_settings(ID_TIERS_COTISATION=2)
@override_settings(ID_CAT_PMV=67)
class TestCase(Test_Case_django):
    def setUp(self):
        # supprime l'affichage des probleme de 404
        logger = logging.getLogger('django.request')
        logger.setLevel(logging.ERROR)
        super(TestCase, self).setUp()
    
    def assertQueryset_list(self, qs1, list1):
        # compare les id d'un query set avec une liste
        pk = qs1.values_list('pk', flat=True)
        return self.assertEqual(sorted(list(pk)), sorted(list(list1)))

    def assertQuerysets(self, qs1, qs2):
        # compare les id d'un query set avec une liste
        pk = qs1.values_list('pk', flat=True)
        pk2 = qs1.values_list('pk', flat=True)
        return self.assertEqual(sorted(list(pk)), sorted(list(pk2)))

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
    
    def assertcountmessage(self, request, nb):
        actual = len([e.message for e in request._messages])
        if actual != nb:
            self.fail('Message count was %d, expected %d' % (actual, nb))

    def assertmessagecontains(self, request, text, level=None):
        messages = request._messages
        matches = [m for m in messages if text in m.message]
        if len(matches) > 0:
            msg = matches[0]
            if level is not None and msg.level != level:
                self.fail('There was one matching message but with different level: %s != %s' % (msg.level, level))
            else:
                return
        else:
            messages_str = ", ".join('"%s"' % m for m in messages)
            self.fail('No message contained text "%s", messages were: %s' % (text, messages_str))
