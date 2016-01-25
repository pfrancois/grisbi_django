# -*- coding: utf-8 -*
"""
test utils
"""

import datetime
import decimal
import os

import django.utils.timezone as tz

from .test_base import TestCase
from .. import utils
from ..models import Exercice, Cat, Ope
from django.conf import settings
import mock

__all__ = ['Test_utils1', 'Test_utils']


class Test_utils1(TestCase):

    def test_FormatException(self):
        with self.assertRaises(utils.FormatException) as exc:
            raise utils.FormatException('texte a tester')

        self.assertEqual("%s" % exc.exception, 'texte a tester')

    def test_utils_uuid(self):
        # on peut pas vraiment tester car justement on lui demande un nouveau uuid a chaque fois
        self.assertEqual(len(utils.uuid()), 36)

    def test_utils_valid_rib(self):
        """test pour verifier la validite des rib"""
        self.assertEqual(utils.validrib(30004, 12345, 12312345678, 30), True)
        self.assertEqual(utils.validrib(30004, 12345, "123A2345678", 30), True)
        self.assertRaises(ValueError, utils.validrib, 300044, 12345, 12312345678, 3)
        self.assertRaises(ValueError, utils.validrib, 30004, 1234555, 12312345678, 3)
        self.assertRaises(ValueError, utils.validrib, 30004, 1234, 123123456789999, 3)
        self.assertRaises(ValueError, utils.validrib, 30004, 1234, 12312345678, 356)

    def test_validinsee(self):
        """"test pour verifier la validite des numero insee"""
        self.assertEqual(utils.validinsee(2810275000151, 92), True)

    def test_date2sql(self):
        self.assertEqual(utils.datefr2datesql("01/02/2011"), "2011-2-1")
        self.assertEqual(utils.datefr2datesql("01/14/2011"), None)

    def test_is_number(self):
        self.assertEqual(utils.is_number(3), True)
        self.assertEqual(utils.is_number("3"), True)
        self.assertEqual(utils.is_number("3.14"), True)
        self.assertEqual(utils.is_number("ceci est n'est pas un nombre"), False)
        self.assertEqual(utils.is_number("nan"), False)
        self.assertEqual(utils.is_number("-inf"), False)
        self.assertEqual(utils.is_number("+inf"), False)
        self.assertEqual(utils.is_number("1+2j"), True)

    def test_fr2decimal(self):
        self.assertEqual(utils.fr2decimal("1,2"), decimal.Decimal('1.2'))
        self.assertEqual(utils.fr2decimal("0,0000000"), decimal.Decimal('0'))
        self.assertEqual(utils.fr2decimal("2 010,2500000"), decimal.Decimal('2010.25'))

    def test_strpdate(self):
        self.assertEqual(utils.strpdate("2011-12-31"), datetime.date(2011, 12, 31))
        self.assertEqual(utils.strpdate(datetime.date(2011, 12, 31)), datetime.date(2011, 12, 31))
        self.assertEqual(utils.strpdate(datetime.datetime(2011, 12, 31, 0, 0, 0)), datetime.date(2011, 12, 31))
        self.assertEqual(utils.strpdate(None), datetime.date(1, 1, 1))
        self.assertRaises(ValueError, utils.strpdate, "2011-12-52")

    def test_now_utc(self):
        mock_date = self.add_minutes(tz.make_aware(datetime.datetime(2014, 6, 23, 0, 0, 0), timezone=tz.utc))
        #test effectif
        with mock.patch('gsb.utils.timezone.now', mock_date.now):
            self.assertEqual(utils.now(), datetime.datetime(2014, 6, 23, 0, 0, 0, tzinfo=tz.utc))

    def test_today(self):
        mock_date = self.add_minutes(tz.make_aware(datetime.datetime(2014, 6, 23, 0, 0, 0), timezone=tz.utc))
        #test effectif
        with mock.patch('gsb.utils.timezone.now', mock_date.now):
            self.assertEqual(utils.today(), datetime.date(2014, 6, 23))

    def test_datetostr(self):
        d = utils.strpdate('2011-01-01')
        self.assertEqual(utils.datetostr(d), '01/01/2011')
        self.assertEqual(utils.datetostr(d, gsb=True), '1/1/2011')
        self.assertEqual(utils.datetostr(d, param='%d/%m/%y'), '01/01/11')
        self.assertEqual(utils.datetostr(None), '0/0/0')
        self.assertRaises(utils.FormatException, utils.datetostr, 'toto')

    def test_booltostr(self):
        self.assertEqual(utils.booltostr(True), '1')
        self.assertEqual(utils.booltostr('1'), '1')
        self.assertEqual(utils.booltostr(False), '0')
        self.assertEqual(utils.booltostr('0'), '0')
        self.assertEqual(utils.booltostr(None), '0')
        self.assertEqual(utils.booltostr(None, '1'), '1')
        self.assertEqual(utils.booltostr('toto'), '1')

    def test_floattostr(self):
        self.assertEqual(utils.floattostr(1.256), '1,2560000')
        self.assertEqual(utils.floattostr(1), '1,0000000')
        self.assertEqual(utils.floattostr(True), '1,0000000')
        self.assertEqual(utils.floattostr(1, 0), '1')
        self.assertEqual(utils.floattostr(1.256, 4), '1,2560')

    def test_typetostr(self):
        liste = ['a', 'b', 'c', 'd']
        self.assertEqual(utils.typetostr(liste, 'a'), '1')
        self.assertEqual(utils.typetostr(liste, 'jhk'), '0')

    # test des formats d'entree
    def test_tostr(self):
        self.assertEqual(utils.to_unicode(None), '')
        self.assertEqual(utils.to_unicode(3), '3')
        self.assertEqual(utils.to_unicode('ceci est éssai'), 'ceci est éssai')
        self.assertEqual(utils.to_unicode('    ceci est éssai'), 'ceci est éssai')
        self.assertEqual(utils.to_unicode(None, 'ceci est éssai'), 'ceci est éssai')
        self.assertEqual(utils.to_unicode(0, 'ceci est éssai'), 'ceci est éssai')
        self.assertEqual(utils.to_unicode("", defaut='ceci est éssai'), 'ceci est éssai')

    def test_to_id(self):
        self.assertEqual(utils.to_id(None), None)
        self.assertEqual(utils.to_id(0), None)
        self.assertEqual(utils.to_id(""), None)
        self.assertEqual(utils.to_id(250), 250)
        self.assertEqual(utils.to_id("250"), 250)
        self.assertRaises(utils.FormatException, utils.to_id, 'toto')
        self.assertRaises(utils.FormatException, utils.to_id, '3.245')

    def test_to_bool(self):
        self.assertEqual(utils.to_bool(True), True)
        self.assertEqual(utils.to_bool(False), False)
        self.assertEqual(utils.to_bool(None), False)
        self.assertEqual(utils.to_bool(0), False)
        self.assertEqual(utils.to_bool(1), True)
        self.assertEqual(utils.to_bool("True"), True)

    def test_to_decimal(self):
        self.assertEqual(utils.to_decimal("1,25"), 1.25)
        self.assertEqual(utils.to_decimal(None), 0)
        self.assertEqual(utils.to_decimal("toto"), 0)

    def test_to_date(self):
        self.assertEqual(utils.to_date("10/01/1999"), datetime.date(1999, 1, 10))
        self.assertEqual(utils.to_date(None), datetime.date(1, 1, 1))
        self.assertRaises(utils.FormatException, utils.to_date, 'toto')

    def test_compfr(self):
        """trie des chiffres"""
        self.assertEqual(sorted([4, 4, 0, 1]), [0, 1, 4, 4])

    def test_compfr2(self):
        """trie de l'alpha"""
        self.assertEqual(sorted(['pêche', 'PÈCHE', 'PÊCHE', 'pèche'], key=utils.sort_fr), ['PÈCHE', 'PÊCHE', 'pêche', 'pèche'])

    def test_compfr4(self):
        """trie avec des chiffre te des lettres"""
        self.assertEqual(sorted([4, 'a', 0, 1], key=utils.sort_fr), [0, 1, 4, 'a'])

    def test_nulltostr(self):
        self.assertEqual(utils.nulltostr(''), 'NULL')
        self.assertEqual(utils.nulltostr(136554), 136554)
        self.assertEqual(utils.nulltostr('test'), 'test')

    def test_find_files(self):
        self.assertEqual([os.path.join(settings.PROJECT_PATH, 'gsb', 'fixtures', 'auth.json'),
                          os.path.join(settings.PROJECT_PATH, 'gsb', 'fixtures', 'test.yaml'),
                          os.path.join(settings.PROJECT_PATH, 'gsb', 'fixtures', 'test_money_journal.yaml')],
                         [x for x in utils.find_files(os.path.join(settings.PROJECT_PATH, 'gsb', 'fixtures'))])
        self.assertEqual([], [x for x in utils.find_files(os.path.join(settings.PROJECT_PATH, 'gsb', 'fixtures'), '*.txt')])
        self.assertEqual([os.path.join(settings.PROJECT_PATH, 'gsb', 'fixtures', 'auth.json')],
                         [x for x in utils.find_files(os.path.join(settings.PROJECT_PATH, 'gsb', 'fixtures'), '*.json')])


class Test_utils(TestCase):

    """test avec bdd"""
    fixtures = ['test.yaml']

    # test des formats de sortie
    def test_maxtostr(self):
        self.assertEqual(utils.maxtostr(Exercice.objects.all(), champ='date_fin'), "2011-12-31")
        self.assertEqual(utils.maxtostr(Exercice.objects.none(), champ='date_fin'), "0")
        self.assertEqual(utils.maxtostr(Exercice.objects.none(), champ='date_fin', defaut="abc"), "abc")

    def test_idtostr(self):
        self.assertEqual(utils.idtostr(None), '0')
        self.assertEqual(utils.idtostr(None, defaut='toto'), 'toto')
        self.assertEqual(utils.idtostr(Cat.objects.get(id=64), membre='nom'), 'Opération sur titre')
        self.assertEqual(utils.idtostr(Cat.objects.get(id=64), membre='nom'), 'Opération sur titre')
        self.assertEqual(utils.idtostr(Ope.objects.get(id=1), membre='num_cheque', defaut="test"), '')
        Cat.objects.create(nom="test:", id=999)
        self.assertEqual(utils.idtostr(Cat.objects.get(id=999), membre='nom'), 'test')
        self.assertEqual(utils.idtostr(Cat.objects.get(id=999)), "999")
        self.assertEqual(utils.idtostr(Ope.objects.get(id=9)), "9")
        self.assertEqual(utils.idtostr(Ope.objects.get(id=1), defaut='', membre='jumelle_id'), "")
        self.assertEqual(utils.idtostr(Ope.objects.get(id=1), defaut='', membre='id'), "1")
        self.assertEqual(utils.idtostr(Ope.objects.get(id=1).rapp, defaut='', membre='nom'), "")
        self.assertEqual(utils.idtostr(Ope.objects.get(id=3).rapp, defaut='', membre='nom'), "cpt_titre2201101")

    def test_is_one_exist(self):
        self.assertEqual(utils.is_onexist(Cat.objects.get(id=64), attribut='nom'), True)
        self.assertEqual(utils.is_onexist(Cat.objects.get(id=64), attribut='gfjdjh'), False)

    def test_datetotimestamp(self):
        self.assertEqual(utils.datetotimestamp(None), 0)
        self.assertEqual(utils.datetotimestamp(datetime.date(1999, 1, 10)),  915922800.0)
        self.assertEqual(utils.datetotimestamp(datetime.datetime(1999, 1, 10)), 915922800.0)
        self.assertEqual(utils.datetotimestamp(datetime.datetime(1999, 1, 10, tzinfo=tz.utc)), 915926400.0)
        self.assertEqual(utils.datetotimestamp(tz.localtime(datetime.datetime(1999, 1, 10, tzinfo=tz.utc))), 915926400.0)
