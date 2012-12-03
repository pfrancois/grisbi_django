from __future__ import absolute_import
from .test_base import TestCase
from ..templatetags import smart_if

#===============================================================================
# Tests
#===============================================================================

class Test_SmartIf(TestCase):
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

        var = smart_if.IfParser([2, 'not', 'in', [2, 3]]).parse()
        self.assertFalse(var.resolve({}))
