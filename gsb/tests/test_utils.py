# -*- coding: utf-8 -*
"""
test utils
"""
from django.test import TestCase
import mysite.gsb.utils as utils
import datetime, time
from mysite.gsb.models import Generalite, Exercice
import decimal
def strpdate(s):
    return datetime.date(*time.strptime(s, "%Y-%m-%d")[0:3])

class test_utils(TestCase):
    fixtures = ['test.json']
    def setUp(self):
        self.f = utils.Format()
    def test_format_date(self):
        d = strpdate('2011-01-01')
        self.assertEquals(self.f.date(d), '1/1/2011')
        self.assertEquals(self.f.date(None), '0/0/0')
        self.assertRaises(TypeError, self.f.date, 'toto')
    def test_format_bool(self):
        self.assertEquals(self.f.bool(True), '1')
        self.assertEquals(self.f.bool('1'), '1')
        self.assertEquals(self.f.bool(False), '0')
        self.assertEquals(self.f.bool('0'), '0')
        self.assertEquals(self.f.bool(None), '0')
        self.assertEquals(self.f.bool(None, '1'), '1')
        self.assertEquals(self.f.bool('toto'), '1')
    def test_format_float(self):
        self.assertEquals(self.f.float(1.256), '1,2560000')
    def test_format_type(self):
        liste = ['a', 'b', 'c', 'd']
        self.assertEquals(self.f.type(liste, 'a'), '1')
        self.assertEquals(self.f.type(liste, 'jhk'), '0')
    def test_format_max(self):
        self.assertEquals(self.f.max(Generalite.objects.all()), '1')
        self.assertEquals(self.f.max(Generalite.objects.none(), defaut='25'), '25')
        self.assertEquals(self.f.max(Generalite.objects.filter(id=2),), '0')
        self.assertEquals(self.f.max(Generalite.objects.filter(id=2), defaut='3'), '3')
        self.assertEquals(self.f.max(Exercice.objects.all(), champ='date_fin'), "2011-12-31")
    def test_format_str(self):
        self.assertEquals(self.f.str(Generalite.objects.get(id=1)), '1')
        self.assertEquals(self.f.str(None), '0')
        self.assertEquals(self.f.str(None, defaut='toto'), 'toto')
        self.assertEquals(self.f.str(Generalite.objects.get(id=1), membre='utilise_exercices'), 'True')
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
