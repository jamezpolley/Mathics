import unittest
import sys
import random
import mathics

class ParserTests(unittest.TestCase):
    def check(self, string, expr):
        self.assertTrue(mathics.parse(string).same(expr))

    def lex_error(self, string):
        self.assertRaises(mathics.ScanError, mathics.parse, string)

    def parse_error(self, string):
        self.assertRaises(mathics.ParseError, mathics.parse, string)


class NumberTests(ParserTests):
    def testReal(self):
        self.check('1.5', mathics.Real('1.5'))
        self.check('1.5`', mathics.Real('1.5'))
        self.check('0.0', mathics.Real(0))
        self.check('-1.5`', mathics.Real('-1.5'))

    def testAccuracy(self):
        self.lex_error('1.5``')

        self.check('1.0``20', mathics.Real('1.0', p=20))

    @unittest.expectedFailure
    def testLowAccuracy(self):
        self.check('1.4``0', mathics.Real(0))
        self.check('1.4``-20', mathics.Real(0))

    def testPrecision(self):
        self.check('1.`20', mathics.Real(1, p=20))
        self.check('1.00000000000000000000000`', mathics.Real(1))
        self.check('1.00000000000000000000000`30', mathics.Real(1, p=30))

    @unittest.expectedFailure
    def testLowPrecision(self):
        self.check('1.4`1', mathics.Real('1', p=1))
        self.check('1.4`0', mathics.Real(0, p=0))
        self.check('1.4`-5', mathics.Real(0, p=0))

    def testInteger(self):
        self.check('0', mathics.Integer(0))

        n = random.randint(-sys.maxint, sys.maxint)
        self.check(str(n), mathics.Integer(n))

        n = random.randint(sys.maxint, sys.maxint * sys.maxint)
        self.check(str(n), mathics.Integer(n))
