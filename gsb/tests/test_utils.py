# -*- coding: utf-8 -*
"""
test utils
"""
from __future__ import absolute_import
from .test_base import TestCase
from ..import utils
import datetime
from ..models import Exercice, Cat, Ope
import decimal
import mock
import time

class Test_utils(TestCase):
    fixtures = ['test.json']

    def setUp(self):
        super(Test_utils, self).setUp()
    
    def test_utils_uuid(self):
        self.assertEquals(len(utils.uuid()),36)
    
    def test_utils_valid_rib(self):
        self.assertEquals(utils.validrib(30004, 12345, 12312345678, 30),True)
        self.assertEquals(utils.validrib(30004, 12345, "123A2345678", 30),True)
        self.assertRaises(ValueError, utils.validrib, 300044, 12345, 12312345678, 3)
        self.assertRaises(ValueError, utils.validrib, 30004, 1234555, 12312345678, 3)
        self.assertRaises(ValueError, utils.validrib, 30004, 1234, 123123456789999, 3)
        self.assertRaises(ValueError, utils.validrib, 30004, 1234, 12312345678, 356)

    def test_validinsee(self):
        self.assertEquals(utils.validinsee(2810275000151, 92), True)

    def test_date2sql(self):
        self.assertEquals(utils.datefr2datesql("01/02/2011"), "2011-2-1")
        self.assertEquals(utils.datefr2datesql("01/14/2011"), None)

    def test_is_number(self):
        self.assertEquals(utils.is_number(3), True)
        self.assertEquals(utils.is_number("3"), True)
        self.assertEquals(utils.is_number("3.14"), True)
        self.assertEquals(utils.is_number("ceci est n'est pas un nombre"), False)
        self.assertEquals(utils.is_number("nan"), False)
        self.assertEquals(utils.is_number("-inf"), False)
        self.assertEquals(utils.is_number("+inf"), False)
        self.assertEquals(utils.is_number("1+2j"), True)
        
    def test_fr2decimal(self):
        self.assertEquals(utils.fr2decimal("1,2"), decimal.Decimal('1.2'))
        self.assertEquals(utils.fr2decimal("0,0000000"), decimal.Decimal('0'))
        self.assertEquals(utils.fr2decimal("2 010,2500000"), decimal.Decimal('2010.25'))
                
    def test_strpdate(self):
        self.assertEquals(utils.strpdate("2011-12-31"), datetime.date(2011, 12, 31))
        self.assertEquals(utils.strpdate(None), datetime.date(1, 1, 1))
        self.assertRaises(ValueError, utils.strpdate, "2011-12-52")

    @mock.patch('gsb.utils.now')
    def test_now(self, today_mock):
        today_mock.return_value = datetime.datetime(2010, 1, 1,0,0)
        self.assertEquals(utils.now(),datetime.datetime(2010, 1, 1,0,0))
        
    @mock.patch('gsb.utils.timestamp')
    def test_timestamp(self, today_mock):
        today_mock.return_value = time.mktime(datetime.datetime(2010, 1, 1,0,0).timetuple())
        self.assertEquals(utils.timestamp(),time.mktime(datetime.datetime(2010, 1, 1,0,0).timetuple()))
        
    @mock.patch('gsb.utils.today')
    def test_today(self, today_mock):
        today_mock.return_value = datetime.date(2010, 1, 1)
        self.assertEquals(utils.today(),datetime.date(2010, 1, 1))
        
    def test_add_month(self):
        self.assertEquals(utils.addmonths(datetime.date(2011, 02, 15), 1), datetime.date(2011, 03, 15))
        self.assertEquals(utils.addmonths(datetime.date(2011, 02, 15), 1, first=True), datetime.date(2011, 03, 01))
        self.assertEquals(utils.addmonths(datetime.date(2011, 02, 15), 1, last=True), datetime.date(2011, 03, 31))

#test des formats de sortie

    def test_datetostr(self):
        d = utils.strpdate('2011-01-01')
        self.assertEquals(utils.datetostr(d), '1/1/2011')
        self.assertEquals(utils.datetostr(None), '0/0/0')
        self.assertRaises(utils.FormatException, utils.datetostr, 'toto')

    def test_booltostr(self):
        self.assertEquals(utils.booltostr(True), '1')
        self.assertEquals(utils.booltostr('1'), '1')
        self.assertEquals(utils.booltostr(False), '0')
        self.assertEquals(utils.booltostr('0'), '0')
        self.assertEquals(utils.booltostr(None), '0')
        self.assertEquals(utils.booltostr(None, '1'), '1')
        self.assertEquals(utils.booltostr('toto'), '1')

    def test_floattostr(self):
        self.assertEquals(utils.floattostr(1.256), '1,2560000')
        self.assertEquals(utils.floattostr(1), '1,0000000')
        self.assertEquals(utils.floattostr(True), '1,0000000')

    def test_typetostr(self):
        liste = ['a', 'b', 'c', 'd']
        self.assertEquals(utils.typetostr(liste, 'a'), '1')
        self.assertEquals(utils.typetostr(liste, 'jhk'), '0')

    def test_maxtostr(self):
        self.assertEquals(utils.maxtostr(Exercice.objects.all(), champ='date_fin'), "2011-12-31")
        self.assertEquals(utils.maxtostr(Exercice.objects.none(), champ='date_fin'), "0")
        self.assertEquals(utils.maxtostr(Exercice.objects.none(), champ='date_fin',defaut="abc"), "abc")
        
    def test_idtostr(self):
        self.assertEquals(utils.idtostr(None), '0')
        self.assertEquals(utils.idtostr(None, defaut='toto'), 'toto')
        self.assertEquals(utils.idtostr(Cat.objects.get(id=64), membre='nom'), 'Operation Sur Titre')
        self.assertEquals(utils.idtostr(Cat.objects.get(id=64), membre='nom'), 'Operation Sur Titre')
        Cat.objects.create(nom="test:",id=999)
        self.assertEquals(utils.idtostr(Cat.objects.get(id=999), membre='nom'), 'test')
        self.assertEquals(utils.idtostr(Cat.objects.get(id=999)), "999")
        self.assertEquals(utils.idtostr(Ope.objects.get(id=9)), "9")
        self.assertEquals(utils.idtostr(Ope.objects.get(id=1), defaut='',membre='jumelle_id') , "")
        self.assertEquals(utils.idtostr(Ope.objects.get(id=1), defaut='',membre='id') , "1")
        self.assertEquals(utils.idtostr(Ope.objects.get(id=1).rapp, defaut='',membre='nom') , "")
        self.assertEquals(utils.idtostr(Ope.objects.get(id=3).rapp, defaut='',membre='nom') , "cpt_titre2201101")

#test des formats d'entree
    def test_tostr(self):
        self.assertEquals(utils.to_unicode(None), u'')
        self.assertEquals(utils.to_unicode(3), u'3')
        self.assertEquals(utils.to_unicode(u'ceci est éssai'), u'ceci est éssai')
        self.assertEquals(utils.to_unicode(u'    ceci est éssai'), u'ceci est éssai')
        self.assertEquals(utils.to_unicode(None,u'ceci est éssai'), u'ceci est éssai')
        self.assertEquals(utils.to_unicode(0,u'ceci est éssai'), u'ceci est éssai')
        self.assertEquals(utils.to_unicode("",defaut=u'ceci est éssai'), u'ceci est éssai')

    def test_to_id(self):
        self.assertEquals(utils.to_id(None), None)
        self.assertEquals(utils.to_id(0), None)
        self.assertEquals(utils.to_id(""), None)
        self.assertEquals(utils.to_id(250), 250)
        self.assertEquals(utils.to_id("250"), 250)
        self.assertRaises(utils.FormatException, utils.to_id, 'toto')
        self.assertRaises(utils.FormatException, utils.to_id, '3.245')

    def test_to_bool(self):
        self.assertEquals(utils.to_bool(True),True)
        self.assertEquals(utils.to_bool(False),False)
        self.assertEquals(utils.to_bool(0),False)
        self.assertEquals(utils.to_bool(1),True)
        self.assertEquals(utils.to_bool("True"),True)

    def test_to_decimal(self):
        self.assertEquals(utils.to_decimal("1,25"),1.25)
        self.assertEquals(utils.to_decimal(None),0)
        self.assertEquals(utils.to_decimal("toto"),0)

    def test_to_date(self):
        self.assertEquals(utils.to_date("10/01/1999"),datetime.date(1999,1,10))
        self.assertEquals(utils.to_date(None),datetime.date(1, 1, 1))
        self.assertRaises(utils.FormatException, utils.to_date, 'toto')

