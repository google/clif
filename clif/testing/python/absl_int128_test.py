# Lint as: python3
"""Tests for testing.python.absl_uint128."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from absl.testing import absltest
from absl.testing import parameterized

from clif.testing.python import absl_int128
# TODO: Restore simple import after OSS setup includes pybind11.
# pylint: disable=g-import-not-at-top
try:
  from clif.testing.python import absl_int128_pybind11
except ImportError:
  absl_int128_pybind11 = None
# pylint: enable=g-import-not-at-top

MAX128 = 0x7FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
MIN128 = -0x80000000000000000000000000000000
MAX64 = 0xFFFFFFFFFFFFFFFF
HIGH_LSB = 1 << 64


@parameterized.named_parameters([
    np for np in zip(('c_api', 'pybind11'), (absl_int128, absl_int128_pybind11))
    if np[1] is not None
])
class AbslInt128Test(absltest.TestCase):

  def testZero(self, wrapper_lib):
    self.assertEqual(wrapper_lib.Zero(), 0)

  def testOne(self, wrapper_lib):
    self.assertEqual(wrapper_lib.One(), 1)

  def testNegativeOne(self, wrapper_lib):
    self.assertEqual(wrapper_lib.NegativeOne(), -1)

  def testSetHighlsb(self, wrapper_lib):
    self.assertEqual(wrapper_lib.SetHighLsb(), HIGH_LSB)

  def testSetNegativeHighlsb(self, wrapper_lib):
    self.assertEqual(wrapper_lib.SetNegativeHighLsb(), -HIGH_LSB)

  def testMin(self, wrapper_lib):
    self.assertEqual(wrapper_lib.Min(), MIN128)

  def testMax(self, wrapper_lib):
    self.assertEqual(wrapper_lib.Max(), MAX128)

  def testAddInt128Int(self, wrapper_lib):
    self.assertEqual(wrapper_lib.AddInt128(1, 1), 2)

  def testAddInt128NegativeInt(self, wrapper_lib):
    self.assertEqual(wrapper_lib.AddInt128(1, -1), 0)

  def testAddInt128Long(self, wrapper_lib):
    self.assertEqual(wrapper_lib.AddInt128(MAX64, 1), HIGH_LSB)

  def testAddNegativeInt128Long(self, wrapper_lib):
    self.assertEqual(wrapper_lib.AddInt128(-MAX64, -1), -HIGH_LSB)

  def testAddInt128NegativeLong(self, wrapper_lib):
    self.assertEqual(wrapper_lib.AddInt128(HIGH_LSB, -MAX64), 1)


if __name__ == '__main__':
  absltest.main()
