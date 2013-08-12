# -*- coding: utf-8 -*
"""
test models
"""
from __future__ import absolute_import
from django.test import SimpleTestCase
from ..templatetags import gsb_extras
from decimal import Decimal

__all__ = ['Test_templates_tags_gsb_extra']


class Test_templates_tags(SimpleTestCase):
    def test_gsb_extra_cur1(self):
        out = gsb_extras.cur(225.50, "EUR")
        self.assertEquals(out, "225,50 &#8364;")
        with self.settings(DEVISE_GENERALE="EUR"):
            out = gsb_extras.cur(225.50)
            self.assertEquals(out, "225,50 &#8364;")
        with self.settings(DEVISE_GENERALE="USD"):
            out = gsb_extras.cur(225.50)
            self.assertEquals(out, "225,50 USD")
        with self.settings(DEVISE_GENERALE=""):
            out = gsb_extras.cur("0.00000000000000001")
            self.assertEquals(out, "0,00 ")
            out = gsb_extras.cur(0.00000000000000001)
            self.assertEquals(out, "0,00 ")
            out = gsb_extras.cur("on ait un test")
            self.assertEquals(out, "0,00 ")
            out = gsb_extras.cur(u"on éait un test")
            self.assertEquals(out, "0,00 ")
            nan = (1e200 * 1e200) / (1e200 * 1e200)
            out = gsb_extras.cur(nan)
            self.assertEquals(out, "0,00 ")

    def test_gsb_extra_somme(self):
        out = gsb_extras.somme(u"24", "6")
        self.assertEquals(out, Decimal(30))
        out = gsb_extras.somme(u"24", "6.5")
        self.assertEquals(out, Decimal("30.5"))

    def test_gsb_extra_centimes(self):
        out = gsb_extras.centimes(1)
        self.assertEquals(out, "100")
