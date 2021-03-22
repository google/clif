# Lint as: python3
"""Tests for testing.python.absl_uint128."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function


from absl.testing import absltest
from absl.testing import parameterized

from clif.testing.python import absl_uint128
# TODO: Restore simple import after OSS setup includes pybind11.
# pylint: disable=g-import-not-at-top
try:
  from clif.testing.python import absl_uint128_pybind11
except ImportError:
  absl_uint128_pybind11 = None
# pylint: enable=g-import-not-at-top

MAX128 = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
MAX64 = 0xFFFFFFFFFFFFFFFF
HIGH_LSB = 1 << 64


@parameterized.named_parameters([
    np
    for np in zip(('c_api', 'pybind11'), (absl_uint128, absl_uint128_pybind11))
    if np[1] is not None
])
class AbslUint128Test(absltest.TestCase):

  def testZero(self, wrapper_lib):
    self.assertEqual(wrapper_lib.Zero(), 0)

  def testOne(self, wrapper_lib):
    self.assertEqual(wrapper_lib.One(), 1)

  def testSethighlsb(self, wrapper_lib):
    self.assertEqual(wrapper_lib.SetHighLsb(), HIGH_LSB)

  def testMax(self, wrapper_lib):
    self.assertEqual(wrapper_lib.Max(), MAX128)

  def testAddUint128Int(self, wrapper_lib):
    self.assertEqual(wrapper_lib.AddUint128(1, 1), 2)

  def testAddUint128Long(self, wrapper_lib):
    self.assertEqual(wrapper_lib.AddUint128(MAX64, 1), HIGH_LSB)


if __name__ == '__main__':
  absltest.main()
