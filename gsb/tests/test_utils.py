# -*- coding: utf-8 -*
"""
test utils
"""
from __future__ import absolute_import
from .test_base import TestCase
from ..import utils
import datetime
from ..models import Exercice, Cat
import decimal


class Test_utils(TestCase):
    fixtures = ['test.json']

    def setUp(self):
        super(Test_utils, self).setUp()

    def test_format_date(self):
        d = utils.strpdate('2011-01-01')
        self.assertEquals(utils.Format.date(d), '1/1/2011')
        self.assertEquals(utils.Format.date(None), '0/0/0')
        self.assertRaises(TypeError, utils.Format.date, 'toto')

    def test_format_bool(self):
        self.assertEquals(utils.Format.bool(True), '1')
        self.assertEquals(utils.Format.bool('1'), '1')
        self.assertEquals(utils.Format.bool(False), '0')
        self.assertEquals(utils.Format.bool('0'), '0')
        self.assertEquals(utils.Format.bool(None), '0')
        self.assertEquals(utils.Format.bool(None, '1'), '1')
        self.assertEquals(utils.Format.bool('toto'), '1')

    def test_format_float(self):
        self.assertEquals(utils.Format.float(1.256), '1,2560000')

    def test_format_type(self):
        liste = ['a', 'b', 'c', 'd']
        self.assertEquals(utils.Format.type(liste, 'a'), '1')
        self.assertEquals(utils.Format.type(liste, 'jhk'), '0')

    def test_format_max(self):
        self.assertEquals(utils.Format.max(Exercice.objects.all(), champ='date_fin'), "2011-12-31")

    def test_format_str(self):
        self.assertEquals(utils.Format.str(None), '0')
        self.assertEquals(utils.Format.str(None, defaut='toto'), 'toto')
        self.assertEquals(utils.Format.str(Cat.objects.get(id=64), membre='nom'), 'Operation Sur Titre')

    def test_validrib(self):
        self.assertEquals(utils.validrib('10001', '12345', '01234567890', 72), True)
        self.assertEquals(utils.validrib('10001', '12345', 'ABCDEFGHIJK', 79), True)
        self.assertRaises(ValueError, utils.validrib, 10001, 12345, 1234567890115463456123, 72)

    def test_validinsee(self):
        self.assertEquals(utils.validinsee(2810275000151, 92), True)

    def test_date2sql(self):
        self.assertEquals(utils.datefr2datesql("01/02/2011"), "2011-2-1")
        self.assertEquals(utils.datefr2datesql("01/14/2011"), None)

    def test_fr2decimal(self):
        self.assertEquals(utils.fr2decimal("1,2"), decimal.Decimal('1.2'))
        self.assertEquals(utils.fr2decimal("0,0000000"), decimal.Decimal('0'))
        self.assertEquals(utils.fr2decimal(None), decimal.Decimal('0'))

    def test_strpdate(self):
        self.assertEquals(utils.strpdate("2011-12-31"), datetime.date(2011, 12, 31))
        self.assertEquals(utils.strpdate(None), datetime.date(1, 1, 1))
        self.assertRaises(ValueError, utils.strpdate, "2011-12-52")


    def test_add_month(self):
        self.assertEquals(utils.addmonths(datetime.date(2011, 02, 15), 1), datetime.date(2011, 03, 15))
        self.assertEquals(utils.addmonths(datetime.date(2011, 02, 15), 1, first=True), datetime.date(2011, 03, 01))
        self.assertEquals(utils.addmonths(datetime.date(2011, 02, 15), 1, last=True), datetime.date(2011, 03, 31))
