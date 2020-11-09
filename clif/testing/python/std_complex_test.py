# Lint as: python3
"""Tests for testing.python.std_complex."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import unittest
import parameterized

from clif.testing.python import std_complex


class StdComplexTest(unittest.TestCase):

  @parameterized.parameterized.expand([(std_complex.StdComplexFloat,),
                                       (std_complex.StdComplexDouble,)])
  def testZero(self, ctype):
    self.assertAlmostEqual(ctype.Zero(), complex(0))

  @parameterized.parameterized.expand([(std_complex.StdComplexFloat,),
                                       (std_complex.StdComplexDouble,)])
  def testOne(self, ctype):
    self.assertAlmostEqual(ctype.One(), complex(1))

  @parameterized.parameterized.expand([(std_complex.StdComplexFloat,),
                                       (std_complex.StdComplexDouble,)])
  def testI(self, ctype):
    self.assertAlmostEqual(ctype.i(), 1j)

  @parameterized.parameterized.expand([(std_complex.StdComplexFloat,),
                                       (std_complex.StdComplexDouble,)])
  def testMultiply(self, ctype):
    self.assertAlmostEqual(ctype.Multiply(ctype.i(), ctype.i()), -ctype.One())


if __name__ == '__main__':
  unittest.main()
