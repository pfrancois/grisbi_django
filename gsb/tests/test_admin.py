# -*- coding: utf-8 -*

from __future__ import absolute_import
from .test_base import TestCase
# from .. import admin
# from .. import models
from django.contrib.admin.sites import AdminSite

request = None


class Test_admin(TestCase):
    def setUp(self):
        super(Test_admin, self).setUp()
        self.site = AdminSite()

    def test_ope_admin(self):
        pass
