# -*- coding: utf-8 -*
"""
test utils
"""
from __future__ import absolute_import
import datetime
import decimal
import os

from django.test import SimpleTestCase
from testfixtures import Replacer, test_datetime
import django.utils.timezone as timezone

from .test_base import TestCase
from .. import utils
from ..models import Exercice, Cat, Ope
from django.conf import settings

__all__ = ['Test_utils1', 'Test_utils']


class Test_utils1(SimpleTestCase):
    """test de utils sans bdd"""

    def test_FormatException(self):
        with self.assertRaises(utils.FormatException) as exc:
            raise utils.FormatException('texte a tester')

        self.assertEqual("%s" % exc.exception, 'texte a tester')

    def test_utils_uuid(self):
        # on peut pas vraiment tester car justement on lui demande un nouveau uuid a chaque fois
        self.assertEquals(len(utils.uuid()), 36)

    def test_utils_valid_rib(self):
        """test pour verifier la validite des rib"""
        self.assertEquals(utils.validrib(30004, 12345, 12312345678, 30), True)
        self.assertEquals(utils.validrib(30004, 12345, "123A2345678", 30), True)
        self.assertRaises(ValueError, utils.validrib, 300044, 12345, 12312345678, 3)
        self.assertRaises(ValueError, utils.validrib, 30004, 1234555, 12312345678, 3)
        self.assertRaises(ValueError, utils.validrib, 30004, 1234, 123123456789999, 3)
        self.assertRaises(ValueError, utils.validrib, 30004, 1234, 12312345678, 356)

    def test_validinsee(self):
        """"test pour verifier la validite des numero insee"""
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
        self.assertEquals(utils.strpdate(datetime.date(2011, 12, 31)), datetime.date(2011, 12, 31))
        self.assertEquals(utils.strpdate(datetime.datetime(2011, 12, 31, 0, 0, 0)), datetime.date(2011, 12, 31))
        self.assertEquals(utils.strpdate(None), datetime.date(1, 1, 1))
        self.assertRaises(ValueError, utils.strpdate, "2011-12-52")

    def test_now_utc(self):
        with Replacer() as r:
            r.replace('gsb.utils.datetime.datetime', test_datetime(2010, 1, 1, 0, 0, 0, tzinfo=timezone.utc))
            self.assertEquals(utils.now(), datetime.datetime(2010, 1, 1, 0, 0, 0, tzinfo=timezone.utc))

    def test_today(self):
        with Replacer() as r:
            r.replace('gsb.utils.datetime.datetime', test_datetime(2010, 1, 1, 0, 0, 0, tzinfo=timezone.utc))
            self.assertEquals(utils.today(), datetime.date(2010, 1, 1))

    def test_datetostr(self):
        d = utils.strpdate('2011-01-01')
        self.assertEquals(utils.datetostr(d), '01/01/2011')
        self.assertEquals(utils.datetostr(d, gsb=True), '1/1/2011')
        self.assertEquals(utils.datetostr(d, param='%d/%m/%y'), '01/01/11')
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
        self.assertEquals(utils.floattostr(1, 0), '1')
        self.assertEquals(utils.floattostr(1.256, 4), '1,2560')

    def test_typetostr(self):
        liste = ['a', 'b', 'c', 'd']
        self.assertEquals(utils.typetostr(liste, 'a'), '1')
        self.assertEquals(utils.typetostr(liste, 'jhk'), '0')

    # test des formats d'entree
    def test_tostr(self):
        self.assertEquals(utils.to_unicode(None), u'')
        self.assertEquals(utils.to_unicode(3), u'3')
        self.assertEquals(utils.to_unicode(u'ceci est éssai'), u'ceci est éssai')
        self.assertEquals(utils.to_unicode(u'    ceci est éssai'), u'ceci est éssai')
        self.assertEquals(utils.to_unicode(None, u'ceci est éssai'), u'ceci est éssai')
        self.assertEquals(utils.to_unicode(0, u'ceci est éssai'), u'ceci est éssai')
        self.assertEquals(utils.to_unicode("", defaut=u'ceci est éssai'), u'ceci est éssai')

    def test_to_id(self):
        self.assertEquals(utils.to_id(None), None)
        self.assertEquals(utils.to_id(0), None)
        self.assertEquals(utils.to_id(""), None)
        self.assertEquals(utils.to_id(250), 250)
        self.assertEquals(utils.to_id("250"), 250)
        self.assertRaises(utils.FormatException, utils.to_id, 'toto')
        self.assertRaises(utils.FormatException, utils.to_id, '3.245')

    def test_to_bool(self):
        self.assertEquals(utils.to_bool(True), True)
        self.assertEquals(utils.to_bool(False), False)
        self.assertEquals(utils.to_bool(None), False)
        self.assertEquals(utils.to_bool(0), False)
        self.assertEquals(utils.to_bool(1), True)
        self.assertEquals(utils.to_bool("True"), True)

    def test_to_decimal(self):
        self.assertEquals(utils.to_decimal("1,25"), 1.25)
        self.assertEquals(utils.to_decimal(None), 0)
        self.assertEquals(utils.to_decimal("toto"), 0)

    def test_to_date(self):
        self.assertEquals(utils.to_date("10/01/1999"), datetime.date(1999, 1, 10))
        self.assertEquals(utils.to_date(None), datetime.date(1, 1, 1))
        self.assertRaises(utils.FormatException, utils.to_date, 'toto')

    def test_compfr(self):
        """trie des chiffres"""
        compfr = utils.Compfr()
        self.assertEquals(sorted([4, 4, 0, 1], cmp=compfr), [0, 1, 4, 4])

    def test_compfr2(self):
        """trie de l'alpha"""
        compfr = utils.Compfr()
        self.assertEquals(sorted(['pêche', 'PÈCHE', 'PÊCHE', 'pèche'], cmp=compfr), ['pèche', 'PÈCHE', 'pêche', 'PÊCHE'])

    def test_compfr3(self):
        """trie avec des caractere unicodes"""
        compfr = utils.Compfr()
        self.assertEquals(sorted([u'vice' + u'\xA0' + u'versa', 'pêche', 'PÈCHE', 'PÊCHE'], cmp=compfr),
                          ['PÈCHE', 'pêche', 'PÊCHE', u'vice' + u'\xA0' + u'versa'])

    def test_compfr4(self):
        """trie avec des chiffre te des lettres"""
        compfr = utils.Compfr()
        self.assertEquals(sorted([4, 'a', 0, 1], cmp=compfr), [0, 1, 4, 'a'])

    def test_nulltostr(self):
        self.assertEquals(utils.nulltostr(''), 'NULL')
        self.assertEquals(utils.nulltostr(136554), 136554)
        self.assertEqual(utils.nulltostr('test'), 'test')

    def test_find_files(self):
        self.assertEqual([os.path.join(settings.PROJECT_PATH, 'gsb', 'fixtures', 'auth.json'),
                          os.path.join(settings.PROJECT_PATH, 'gsb', 'fixtures', 'test.yaml'),
                          os.path.join(settings.PROJECT_PATH, 'gsb', 'fixtures', 'test_money_journal.yaml')],
                         [x for x in utils.find_files(os.path.join(settings.PROJECT_PATH, 'gsb', 'fixtures'))])
        self.assertEqual([],[x for x in utils.find_files(os.path.join(settings.PROJECT_PATH, 'gsb', 'fixtures'), '*.txt')])
        self.assertEqual([os.path.join(settings.PROJECT_PATH, 'gsb', 'fixtures', 'auth.json')],
                         [x for x in utils.find_files(os.path.join(settings.PROJECT_PATH, 'gsb', 'fixtures'), '*.json')])


class Test_utils(TestCase):
    """test avec bdd"""
    fixtures = ['test.yaml']

    # test des formats de sortie
    def test_maxtostr(self):
        self.assertEquals(utils.maxtostr(Exercice.objects.all(), champ='date_fin'), "2011-12-31")
        self.assertEquals(utils.maxtostr(Exercice.objects.none(), champ='date_fin'), "0")
        self.assertEquals(utils.maxtostr(Exercice.objects.none(), champ='date_fin', defaut="abc"), "abc")

    def test_idtostr(self):
        self.assertEquals(utils.idtostr(None), '0')
        self.assertEquals(utils.idtostr(None, defaut='toto'), 'toto')
        self.assertEquals(utils.idtostr(Cat.objects.get(id=64), membre='nom'), u'Opération sur titre')
        self.assertEquals(utils.idtostr(Cat.objects.get(id=64), membre='nom'), u'Opération sur titre')
        self.assertEquals(utils.idtostr(Ope.objects.get(id=1), membre='num_cheque', defaut="test"), '')
        Cat.objects.create(nom="test:", id=999)
        self.assertEquals(utils.idtostr(Cat.objects.get(id=999), membre='nom'), 'test')
        self.assertEquals(utils.idtostr(Cat.objects.get(id=999)), "999")
        self.assertEquals(utils.idtostr(Ope.objects.get(id=9)), "9")
        self.assertEquals(utils.idtostr(Ope.objects.get(id=1), defaut='', membre='jumelle_id'), "")
        self.assertEquals(utils.idtostr(Ope.objects.get(id=1), defaut='', membre='id'), "1")
        self.assertEquals(utils.idtostr(Ope.objects.get(id=1).rapp, defaut='', membre='nom'), "")
        self.assertEquals(utils.idtostr(Ope.objects.get(id=3).rapp, defaut='', membre='nom'), "cpt_titre2201101")

    def test_is_one_exist(self):
        self.assertEqual(utils.is_onexist(Cat.objects.get(id=64), attribut='nom'), True)
        self.assertEqual(utils.is_onexist(Cat.objects.get(id=64), attribut='gfjdjh'), False)

    def test_datetotimestamp(self):
        self.assertEqual(utils.datetotimestamp(None), 0)
        self.assertEqual(utils.datetotimestamp(datetime.date(1999, 1, 10)), 915926400)
        self.assertEqual(utils.datetotimestamp(datetime.datetime(1999, 1, 10)), 915926400)
        self.assertEqual(utils.datetotimestamp(datetime.datetime(1999, 1, 10, tzinfo=timezone.utc)), 915926400)