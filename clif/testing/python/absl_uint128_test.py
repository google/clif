# Lint as: python3
"""Tests for testing.python.absl_uint128."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import unittest

from clif.testing.python import absl_uint128

MAX128 = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
MAX64 = 0xFFFFFFFFFFFFFFFF
HIGH_LSB = 1 << 64


class AbslUint128Test(unittest.TestCase):

  def testZero(self):
    self.assertEqual(absl_uint128.Zero(), 0)

  def testOne(self):
    self.assertEqual(absl_uint128.One(), 1)

  def testSethighlsb(self):
    self.assertEqual(absl_uint128.SetHighLsb(), HIGH_LSB)

  def testMax(self):
    self.assertEqual(absl_uint128.Max(), MAX128)

  def testAddUint128Int(self):
    self.assertEqual(absl_uint128.AddUint128(1, 1), 2)

  def testAddUint128Long(self):
    self.assertEqual(absl_uint128.AddUint128(MAX64, 1), HIGH_LSB)


if __name__ == '__main__':
  unittest.main()
