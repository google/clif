"""Tests for testing.python.absl_uint128."""

from absl.testing import absltest

from clif.testing.python import absl_uint128

MAX128 = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
MAX64 = 0xFFFFFFFFFFFFFFFF
HIGH_LSB = 1 << 64


class AbslUint128Test(absltest.TestCase):

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

  def testIntrinsicFromAbsl(self):
    if absl_uint128.HAS_INTRINSIC_UINT_128:
      self.assertEqual(absl_uint128.FromAbsl(123), 123)
    else:
      self.assertEqual(absl_uint128.FromAbsl(123), 0)  # Dummy implementation.

  def testIntrinsicToAbsl(self):
    if absl_uint128.HAS_INTRINSIC_UINT_128:
      self.assertEqual(absl_uint128.ToAbsl(123), 123)
    else:
      self.assertEqual(absl_uint128.ToAbsl(123), 0)  # Dummy implementation.


if __name__ == '__main__':
  absltest.main()
