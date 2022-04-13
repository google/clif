# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from absl.testing import absltest

from clif.testing.python import number_methods


class NumberMethodsTest(absltest.TestCase):

  def testAdd(self):
    n1 = number_methods.Number(1.0)
    n2 = number_methods.Number(2.0)
    n3 = n1 + n2
    self.assertEqual(n3.value, 3.0)
    self.assertEqual(n1.fake_plus('fake'), b'1')

  def testSubtract(self):
    n1 = number_methods.Number(2.0)
    n2 = number_methods.Number(1.0)
    n3 = n1 - n2
    self.assertEqual(n3.value, 1.0)

  def testMultiply(self):
    n1 = number_methods.Number(2.0)
    n2 = number_methods.Number(3.0)
    n3 = n1 * n2
    self.assertEqual(n3.value, 6.0 * 10)

  def testCustomizedMultiply(self):
    n1 = number_methods.Number(2.0)
    n2 = number_methods.Number(3.0)
    n3 = n1.my_mul(n2)
    self.assertEqual(n3.value, 6.0)

  def testMod(self):
    n1 = number_methods.Number(7.0)
    n2 = number_methods.Number(3.0)
    n3 = n1 % n2
    self.assertEqual(n3.value, 1.0)

  def testPower(self):
    n1 = number_methods.Number(7.0)
    n2 = number_methods.Number(3.0)
    n3 = n1 ** n2
    self.assertEqual(n3.value, 343.0)

  def testPowerWithModulo(self):
    n1 = number_methods.Number(7.0)
    n2 = number_methods.Number(3.0)
    n3 = number_methods.Number(10.0)
    n4 = pow(n1, n2, n3)
    self.assertEqual(n4.value, 3.0)

  def testDivmod(self):
    n1 = number_methods.Number(7.0)
    n2 = number_methods.Number(3.0)
    n3, n4 = divmod(n1, n2)
    self.assertEqual(n3.value, 2.0)
    self.assertEqual(n4.value, 1.0)

  def testNegative(self):
    n1 = number_methods.Number(8.0)
    n2 = number_methods.Number(-8.0)
    self.assertEqual((-n1).value, -8.0)
    self.assertEqual((-n2).value, 8.0)

  def testPositive(self):
    n1 = number_methods.Number(8.0)
    n2 = number_methods.Number(-8.0)
    self.assertEqual((+n1).value, 8.0)
    self.assertEqual((+n2).value, -8.0)

  def testAbsolute(self):
    n1 = number_methods.Number(8.0)
    n2 = number_methods.Number(-8.0)
    self.assertEqual(abs(n1).value, 8.0)
    self.assertEqual(abs(n2).value, 8.0)

  def testInvert(self):
    n = number_methods.Number(5.0)  # 5(0b0101)
    self.assertEqual((~n).value, -6)  # -6(0b1010)

  def testLshift(self):
    n = number_methods.Number(5.0)  # 5(0b0101)
    self.assertEqual((n << 1).value, 10)  # 10(0b1010)

  def testRshift(self):
    n = number_methods.Number(5.0)  # 5(0b0101)
    self.assertEqual((n >> 1).value, 2)  # 2(0b0010)

  def testAnd(self):
    n1 = number_methods.Number(5.0)  # 5(0b0101)
    n2 = number_methods.Number(6.0)  # 6(0b0110)
    self.assertEqual((n1 & n2).value, 4)  # 2(0b0100)

  def testXor(self):
    n1 = number_methods.Number(5.0)  # 5(0b0101)
    n2 = number_methods.Number(6.0)  # 6(0b0110)
    self.assertEqual((n1 ^ n2).value, 3)  # 2(0b0011)

  def testOr(self):
    n1 = number_methods.Number(5.0)  # 5(0b0101)
    n2 = number_methods.Number(6.0)  # 6(0b0110)
    self.assertEqual((n1 | n2).value, 7)  # 2(0b0111)

  def testBool(self):
    n1 = number_methods.Number(6.0)
    n2 = number_methods.Number(0.0)
    self.assertTrue(bool(n1))
    self.assertFalse(bool(n2))

  def testInt(self):
    n1 = number_methods.Number(6.0)
    self.assertEqual(int(n1), 6)

  def testFloat(self):
    n1 = number_methods.Number(6)
    self.assertEqual(float(n1), 6.0)

  def testInplaceAdd(self):
    n1 = number_methods.Number(1.0)
    n2 = number_methods.Number(2.0)
    n1 += n2
    self.assertEqual(n1.value, 3.0)

  def testInplaceSubtract(self):
    n1 = number_methods.Number(2.0)
    n2 = number_methods.Number(1.0)
    n1 -= n2
    self.assertEqual(n1.value, 1.0)

  def testInplaceMultiply(self):
    n1 = number_methods.Number(2.0)
    n2 = number_methods.Number(3.0)
    n1 *= n2
    self.assertEqual(n1.value, 6.0)

  def testInplaceMod(self):
    n1 = number_methods.Number(7.0)
    n2 = number_methods.Number(3.0)
    n1 %= n2
    self.assertEqual(n1.value, 1.0)

  def testFloorDivide(self):
    n1 = number_methods.Number(10.0)
    n2 = number_methods.Number(3.0)
    n3 = n1 // n2
    self.assertEqual(n3.value, 3.0)

  def testTrueDivide(self):
    n1 = number_methods.Number(6.0)
    n2 = number_methods.Number(3.0)
    n3 = n1 / n2
    self.assertEqual(n3.value, 2.0)

  def testInplaceFloorDivide(self):
    n1 = number_methods.Number(10.0)
    n2 = number_methods.Number(3.0)
    n1 //= n2
    self.assertEqual(n1.value, 3.0)

  def testInplaceTrueDivede(self):
    n1 = number_methods.Number(6.0)
    n2 = number_methods.Number(3.0)
    n1 /= n2
    self.assertEqual(n1.value, 2.0)

  def testInplaceLshift(self):
    n = number_methods.Number(5.0)  # 5(0b0101)
    n <<= 1
    self.assertEqual(n.value, 10)  # 10(0b1010)

  def testInplaceRshift(self):
    n = number_methods.Number(5.0)  # 5(0b0101)
    n >>= 1
    self.assertEqual(n.value, 2)  # 2(0b0010)

  def testInplaceAnd(self):
    n1 = number_methods.Number(5.0)  # 5(0b0101)
    n2 = number_methods.Number(6.0)  # 6(0b0110)
    n1 &= n2
    self.assertEqual(n1.value, 4)  # 2(0b0100)

  def testInplaceXor(self):
    n1 = number_methods.Number(5.0)  # 5(0b0101)
    n2 = number_methods.Number(6.0)  # 6(0b0110)
    n1 ^= n2
    self.assertEqual(n1.value, 3)  # 2(0b0011)

  def testInplaceOr(self):
    n1 = number_methods.Number(5.0)  # 5(0b0101)
    n2 = number_methods.Number(6.0)  # 6(0b0110)
    n1 |= n2
    self.assertEqual(n1.value, 7)  # 2(0b0111)

  def testIndex(self):
    n1 = number_methods.Number(6)
    self.assertEqual(n1.__index__(), 6)


if __name__ == '__main__':
  absltest.main()
