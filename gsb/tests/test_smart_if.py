from django.test import TestCase
from mysite.gsb.templatetags.smart_if import *

#===============================================================================
# Tests
#===============================================================================


class SmartIfTests(TestCase):
    def setUp(self):
        self.true = TestVar(True)
        self.false = TestVar(False)
        self.high = TestVar(9000)
        self.low = TestVar(1)

    def assertCalc(self, calc, context = None):
        """
        Test a calculation is True, also checking the inverse "negate" case.
        """
        context = context or {}
        self.assert_(calc.resolve(context))
        calc.negate = not calc.negate
        self.assertFalse(calc.resolve(context))

    def assertCalcFalse(self, calc, context = None):
        """
        Test a calculation is False, also checking the inverse "negate" case.
        """
        context = context or {}
        self.assertFalse(calc.resolve(context))
        calc.negate = not calc.negate
        self.assert_(calc.resolve(context))

    def test_or(self):
        self.assertCalc(Or(self.true))
        self.assertCalcFalse(Or(self.false))
        self.assertCalc(Or(self.true, self.true))
        self.assertCalc(Or(self.true, self.false))
        self.assertCalc(Or(self.false, self.true))
        self.assertCalcFalse(Or(self.false, self.false))

    def test_and(self):
        self.assertCalc(And(self.true, self.true))
        self.assertCalcFalse(And(self.true, self.false))
        self.assertCalcFalse(And(self.false, self.true))
        self.assertCalcFalse(And(self.false, self.false))

    def test_equals(self):
        self.assertCalc(Equals(self.low, self.low))
        self.assertCalcFalse(Equals(self.low, self.high))

    def test_greater(self):
        self.assertCalc(Greater(self.high, self.low))
        self.assertCalcFalse(Greater(self.low, self.low))
        self.assertCalcFalse(Greater(self.low, self.high))

    def test_greater_or_equal(self):
        self.assertCalc(GreaterOrEqual(self.high, self.low))
        self.assertCalc(GreaterOrEqual(self.low, self.low))
        self.assertCalcFalse(GreaterOrEqual(self.low, self.high))

    def test_in(self):
        list_ = TestVar([1, 2, 3])
        invalid_list = TestVar(None)
        self.assertCalc(In(self.low, list_))
        self.assertCalcFalse(In(self.low, invalid_list))

    def test_parse_bits(self):
        var = IfParser([True]).parse()
        self.assert_(var.resolve({}))
        var = IfParser([False]).parse()
        self.assertFalse(var.resolve({}))

        var = IfParser([False, 'or', True]).parse()
        self.assert_(var.resolve({}))

        var = IfParser([False, 'and', True]).parse()
        self.assertFalse(var.resolve({}))

        var = IfParser(['not', False, 'and', 'not', False]).parse()
        self.assert_(var.resolve({}))

        var = IfParser([1, '=', 1]).parse()
        self.assert_(var.resolve({}))

        var = IfParser([1, '!=', 1]).parse()
        self.assertFalse(var.resolve({}))

        var = IfParser([3, '>', 2]).parse()
        self.assert_(var.resolve({}))

        var = IfParser([1, '<', 2]).parse()
        self.assert_(var.resolve({}))

        var = IfParser([2, 'not', 'in', [2, 3]]).parse()
        self.assertFalse(var.resolve({}))
