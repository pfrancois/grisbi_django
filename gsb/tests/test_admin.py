# -*- coding: utf-8 -*

from __future__ import absolute_import
from .test_base import TestCase
from .. import admin
from .. import models
from django.contrib.admin.sites import AdminSite

request = None

__all__ = ['Test_admin']
request = None


class Test_admin(TestCase):

    def setUp(self):
        super(Test_admin, self).setUp()
        self.site = AdminSite()

    def test_cat_admin(self):
        ca = admin.Cat_admin(models.Cat, self.site)
        cat = models.Cat.objects.create(nom="test", type="d")
        self.assertEqual(ca.get_fieldsets(request, cat), [(None, {'fields': ['nom', 'type']})])
