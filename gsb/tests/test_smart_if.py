from __future__ import absolute_import
# from .test_base import TestCase
import unittest
from gsb.templatetags import smart_if
from django.template import Template, Context, TemplateSyntaxError


#===============================================================================
# Tests
#===============================================================================

class Test_SmartIf(unittest.TestCase):
    def setUp(self):
        super(Test_SmartIf, self).setUp()
        self.true = smart_if.TestVar(True)
        self.false = smart_if.TestVar(False)
        self.high = smart_if.TestVar(9000)
        self.low = smart_if.TestVar(1)

    def assertCalc(self, calc, context=None):
        """
        Test a calculation is True, also checking the inverse "negate" case.
        """
        context = context or {}
        self.assert_(calc.resolve(context))
        calc.negate = not calc.negate
        self.assertFalse(calc.resolve(context))

    def assertCalcFalse(self, calc, context=None):
        """
        Test a calculation is False, also checking the inverse "negate" case.
        """
        context = context or {}
        self.assertFalse(calc.resolve(context))
        calc.negate = not calc.negate
        self.assert_(calc.resolve(context))

    def test_or(self):
        self.assertCalc(smart_if.Or(self.true))
        self.assertCalcFalse(smart_if.Or(self.false))
        self.assertCalc(smart_if.Or(self.true, self.true))
        self.assertCalc(smart_if.Or(self.true, self.false))
        self.assertCalc(smart_if.Or(self.false, self.true))
        self.assertCalcFalse(smart_if.Or(self.false, self.false))

    def test_and(self):
        self.assertCalc(smart_if.And(self.true, self.true))
        self.assertCalcFalse(smart_if.And(self.true, self.false))
        self.assertCalcFalse(smart_if.And(self.false, self.true))
        self.assertCalcFalse(smart_if.And(self.false, self.false))

    def test_equals(self):
        self.assertCalc(smart_if.Equals(self.low, self.low))
        self.assertCalcFalse(smart_if.Equals(self.low, self.high))

    def test_greater(self):
        self.assertCalc(smart_if.Greater(self.high, self.low))
        self.assertCalcFalse(smart_if.Greater(self.low, self.low))
        self.assertCalcFalse(smart_if.Greater(self.low, self.high))

    def test_greater_or_equal(self):
        self.assertCalc(smart_if.GreaterOrEqual(self.high, self.low))
        self.assertCalc(smart_if.GreaterOrEqual(self.low, self.low))
        self.assertCalcFalse(smart_if.GreaterOrEqual(self.low, self.high))

    def test_in(self):
        list_ = smart_if.TestVar([1, 2, 3])
        invalid_list = smart_if.TestVar(None)
        self.assertCalc(smart_if.In(self.low, list_))
        self.assertCalcFalse(smart_if.In(self.low, invalid_list))

    def test_parse_bits(self):
        var = smart_if.IfParser([True]).parse()
        self.assert_(var.resolve({}))
        var = smart_if.IfParser([False]).parse()
        self.assertFalse(var.resolve({}))

        var = smart_if.IfParser([False, 'or', True]).parse()
        self.assert_(var.resolve({}))

        var = smart_if.IfParser([False, 'and', True]).parse()
        self.assertFalse(var.resolve({}))

        var = smart_if.IfParser(['not', False, 'and', 'not', False]).parse()
        self.assert_(var.resolve({}))

        var = smart_if.IfParser([1, '=', 1]).parse()
        self.assert_(var.resolve({}))

        var = smart_if.IfParser([1, '!=', 1]).parse()
        self.assertFalse(var.resolve({}))

        var = smart_if.IfParser([3, '>', 2]).parse()
        self.assert_(var.resolve({}))

        var = smart_if.IfParser([1, '<', 2]).parse()
        self.assert_(var.resolve({}))
        var = smart_if.IfParser([1, 'not', 'in', [2, 3]]).parse()
        self.assert_(var.resolve({}))

    def test_error(self):
        with self.assertRaises(ValueError) as exc:
            var = smart_if.IfParser([]).parse()
            var.resolve({})
        self.assertEqual(exc.exception.args[0], 'No variables provided.')

    def test_error2(self):
        with self.assertRaises(ValueError) as exc:
            var = smart_if.IfParser([3, 'not']).parse()
            var.resolve({})
        self.assertEqual(exc.exception.args[0], 'No variable provided after "not".')

    def test_error3(self):
        with self.assertRaises(ValueError) as exc:
            var = smart_if.IfParser([3, 'cecinestpasunoperateur']).parse()
            var.resolve({})
        self.assertEqual(exc.exception.args[0], 'cecinestpasunoperateur is not a valid operator.')

    def test_error5(self):
        with self.assertRaises(ValueError) as exc:
            var = smart_if.IfParser([3, '>']).parse()
            var.resolve({})
        self.assertEqual(exc.exception.args[0], 'No variable provided after ">"')

    def test_error6(self):
        with self.assertRaises(ValueError) as exc:
            var = smart_if.IfParser(['not']).parse()
            var.resolve({})
        self.assertEqual(exc.exception.args[0], 'No variable provided after "not".')

    def test_template(self):
        rendered = Template("{% load smart_if %}"
                          "{% if 3 < 5 %}...{% endif %}").render(Context())
        self.assertEqual(rendered, '...')
        rendered = Template("{% load smart_if %}"
                          "{% if 3 > 5 %}...{% endif %}").render(Context())
        self.assertEqual(rendered, '')
        rendered = Template("{% load smart_if %}"
                          "{% if 3 > 5 %}...{% else %}   {% endif %}").render(Context())
        self.assertEqual(rendered, '   ')
        rendered = Template("{% load smart_if %}{% if 2 == 2 or 3 <= 5 %} {% endif %}").render(Context())
        self.assertEqual(rendered, ' ')
        rendered = Template("{% load smart_if %}{% if 2 in l %} {% endif %}").render(Context({"l": (1, 2, 3)}))
        self.assertEqual(rendered, ' ')
        rendered = Template("{% load smart_if %}{% if 2 = 2 %}{% if 2 = 2 %}  {% endif %}{% endif %}").render(Context())
        self.assertEqual(rendered, '  ')
        rendered = Template("{% load smart_if %}{% if texte|length = 5 %} {% endif %}").render(Context({"texte": "12345"}))
        self.assertEqual(rendered, ' ')

    def test_parsing_errors(self):
        "There are various ways that the flatpages template tag won't parse"
        render = lambda t: Template(t).render(Context())
        self.assertRaises(TemplateSyntaxError, render, "{% load smart_if %}{% if 3 > 5 %}")
        self.assertRaises(TemplateSyntaxError, render, "{% load smart_if %}{% if 3>5 %}{% endif %}")
