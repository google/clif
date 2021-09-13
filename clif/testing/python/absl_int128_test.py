"""Tests for testing.python.absl_uint128."""

from absl.testing import absltest

from clif.testing.python import absl_int128

MAX128 = 0x7FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
MIN128 = -0x80000000000000000000000000000000
MAX64 = 0xFFFFFFFFFFFFFFFF
HIGH_LSB = 1 << 64


class AbslInt128Test(absltest.TestCase):

  def testZero(self):
    self.assertEqual(absl_int128.Zero(), 0)

  def testOne(self):
    self.assertEqual(absl_int128.One(), 1)

  def testNegativeOne(self):
    self.assertEqual(absl_int128.NegativeOne(), -1)

  def testSetHighlsb(self):
    self.assertEqual(absl_int128.SetHighLsb(), HIGH_LSB)

  def testSetNegativeHighlsb(self):
    self.assertEqual(absl_int128.SetNegativeHighLsb(), -HIGH_LSB)

  def testMin(self):
    self.assertEqual(absl_int128.Min(), MIN128)

  def testMax(self):
    self.assertEqual(absl_int128.Max(), MAX128)

  def testAddInt128Int(self):
    self.assertEqual(absl_int128.AddInt128(1, 1), 2)

  def testAddInt128NegativeInt(self):
    self.assertEqual(absl_int128.AddInt128(1, -1), 0)

  def testAddInt128Long(self):
    self.assertEqual(absl_int128.AddInt128(MAX64, 1), HIGH_LSB)

  def testAddNegativeInt128Long(self):
    self.assertEqual(absl_int128.AddInt128(-MAX64, -1), -HIGH_LSB)

  def testAddInt128NegativeLong(self):
    self.assertEqual(absl_int128.AddInt128(HIGH_LSB, -MAX64), 1)


if __name__ == '__main__':
  absltest.main()
