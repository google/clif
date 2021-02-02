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
from absl.testing import parameterized

from clif.testing.python import number_methods
# TODO: Restore simple import after OSS setup includes pybind11.
# pylint: disable=g-import-not-at-top
try:
  from clif.testing.python import number_methods_pybind11
except ImportError:
  number_methods_pybind11 = None
# pylint: enable=g-import-not-at-top


@parameterized.named_parameters([
    np for np in zip(('c_api', 'pybind11'), (number_methods,
                                             number_methods_pybind11))
    if np[1] is not None
])
class NumberMethodsTest(absltest.TestCase):

  def testAdd(self, wrapper_lib):
    n1 = wrapper_lib.Number(1.0)
    n2 = wrapper_lib.Number(2.0)
    n3 = n1 + n2
    self.assertEqual(n3.value, 3.0)

  def testSubtract(self, wrapper_lib):
    n1 = wrapper_lib.Number(2.0)
    n2 = wrapper_lib.Number(1.0)
    n3 = n1 - n2
    self.assertEqual(n3.value, 1.0)

  def testMultiply(self, wrapper_lib):
    n1 = wrapper_lib.Number(2.0)
    n2 = wrapper_lib.Number(3.0)
    n3 = n1 * n2
    self.assertEqual(n3.value, 6.0 * 10)

  def testCustomizedMultiply(self, wrapper_lib):
    n1 = wrapper_lib.Number(2.0)
    n2 = wrapper_lib.Number(3.0)
    n3 = n1.my_mul(n2)
    self.assertEqual(n3.value, 6.0)

  def testMod(self, wrapper_lib):
    n1 = wrapper_lib.Number(7.0)
    n2 = wrapper_lib.Number(3.0)
    n3 = n1 % n2
    self.assertEqual(n3.value, 1.0)

  @absltest.skip('Skipping power tests for now.')
  def testPower(self, wrapper_lib):
    n1 = wrapper_lib.Number(7.0)
    n2 = wrapper_lib.Number(3.0)
    n3 = n1 ** n2
    self.assertEqual(n3.value, 343.0)

  @absltest.skip('Skipping power tests for now.')
  def testPowerWithModulo(self, wrapper_lib):
    n1 = wrapper_lib.Number(7.0)
    n2 = wrapper_lib.Number(3.0)
    n3 = wrapper_lib.Number(10.0)
    n4 = pow(n1, n2, n3)
    self.assertEqual(n4.value, 3.0)

  def testDivmod(self, wrapper_lib):
    n1 = wrapper_lib.Number(7.0)
    n2 = wrapper_lib.Number(3.0)
    n3, n4 = divmod(n1, n2)
    self.assertEqual(n3.value, 2.0)
    self.assertEqual(n4.value, 1.0)

  def testNegative(self, wrapper_lib):
    n1 = wrapper_lib.Number(8.0)
    n2 = wrapper_lib.Number(-8.0)
    self.assertEqual((-n1).value, -8.0)
    self.assertEqual((-n2).value, 8.0)

  def testPositive(self, wrapper_lib):
    n1 = wrapper_lib.Number(8.0)
    n2 = wrapper_lib.Number(-8.0)
    self.assertEqual((+n1).value, 8.0)
    self.assertEqual((+n2).value, -8.0)

  def testAbsolute(self, wrapper_lib):
    n1 = wrapper_lib.Number(8.0)
    n2 = wrapper_lib.Number(-8.0)
    self.assertEqual(abs(n1).value, 8.0)
    self.assertEqual(abs(n2).value, 8.0)

  def testInvert(self, wrapper_lib):
    n = wrapper_lib.Number(5.0)  # 5(0b0101)
    self.assertEqual((~n).value, -6)  # -6(0b1010)

  def testLshift(self, wrapper_lib):
    n = wrapper_lib.Number(5.0)  # 5(0b0101)
    self.assertEqual((n << 1).value, 10)  # 10(0b1010)

  def testRshift(self, wrapper_lib):
    n = wrapper_lib.Number(5.0)  # 5(0b0101)
    self.assertEqual((n >> 1).value, 2)  # 2(0b0010)

  def testAnd(self, wrapper_lib):
    n1 = wrapper_lib.Number(5.0)  # 5(0b0101)
    n2 = wrapper_lib.Number(6.0)  # 6(0b0110)
    self.assertEqual((n1 & n2).value, 4)  # 2(0b0100)

  def testXor(self, wrapper_lib):
    n1 = wrapper_lib.Number(5.0)  # 5(0b0101)
    n2 = wrapper_lib.Number(6.0)  # 6(0b0110)
    self.assertEqual((n1 ^ n2).value, 3)  # 2(0b0011)

  def testOr(self, wrapper_lib):
    n1 = wrapper_lib.Number(5.0)  # 5(0b0101)
    n2 = wrapper_lib.Number(6.0)  # 6(0b0110)
    self.assertEqual((n1 | n2).value, 7)  # 2(0b0111)

  def testBool(self, wrapper_lib):
    n1 = wrapper_lib.Number(6.0)
    n2 = wrapper_lib.Number(0.0)
    self.assertTrue(bool(n1))
    self.assertFalse(bool(n2))

  def testInt(self, wrapper_lib):
    n1 = wrapper_lib.Number(6.0)
    self.assertEqual(int(n1), 6)

  def testFloat(self, wrapper_lib):
    n1 = wrapper_lib.Number(6)
    self.assertEqual(float(n1), 6.0)

  def testInplaceAdd(self, wrapper_lib):
    n1 = wrapper_lib.Number(1.0)
    n2 = wrapper_lib.Number(2.0)
    n1 += n2
    self.assertEqual(n1.value, 3.0)

  def testInplaceSubtract(self, wrapper_lib):
    n1 = wrapper_lib.Number(2.0)
    n2 = wrapper_lib.Number(1.0)
    n1 -= n2
    self.assertEqual(n1.value, 1.0)

  def testInplaceMultiply(self, wrapper_lib):
    n1 = wrapper_lib.Number(2.0)
    n2 = wrapper_lib.Number(3.0)
    n1 *= n2
    self.assertEqual(n1.value, 6.0)

  def testInplaceMod(self, wrapper_lib):
    n1 = wrapper_lib.Number(7.0)
    n2 = wrapper_lib.Number(3.0)
    n1 %= n2
    self.assertEqual(n1.value, 1.0)

  def testFloorDivide(self, wrapper_lib):
    n1 = wrapper_lib.Number(10.0)
    n2 = wrapper_lib.Number(3.0)
    n3 = n1 // n2
    self.assertEqual(n3.value, 3.0)

  def testTrueDivide(self, wrapper_lib):
    n1 = wrapper_lib.Number(6.0)
    n2 = wrapper_lib.Number(3.0)
    n3 = n1 / n2
    self.assertEqual(n3.value, 2.0)

  def testInplaceFloorDivide(self, wrapper_lib):
    n1 = wrapper_lib.Number(10.0)
    n2 = wrapper_lib.Number(3.0)
    n1 //= n2
    self.assertEqual(n1.value, 3.0)

  def testInplaceTrueDivede(self, wrapper_lib):
    n1 = wrapper_lib.Number(6.0)
    n2 = wrapper_lib.Number(3.0)
    n1 /= n2
    self.assertEqual(n1.value, 2.0)

  def testInplaceLshift(self, wrapper_lib):
    n = wrapper_lib.Number(5.0)  # 5(0b0101)
    n <<= 1
    self.assertEqual(n.value, 10)  # 10(0b1010)

  def testInplaceRshift(self, wrapper_lib):
    n = wrapper_lib.Number(5.0)  # 5(0b0101)
    n >>= 1
    self.assertEqual(n.value, 2)  # 2(0b0010)

  def testInplaceAnd(self, wrapper_lib):
    n1 = wrapper_lib.Number(5.0)  # 5(0b0101)
    n2 = wrapper_lib.Number(6.0)  # 6(0b0110)
    n1 &= n2
    self.assertEqual(n1.value, 4)  # 2(0b0100)

  def testInplaceXor(self, wrapper_lib):
    n1 = wrapper_lib.Number(5.0)  # 5(0b0101)
    n2 = wrapper_lib.Number(6.0)  # 6(0b0110)
    n1 ^= n2
    self.assertEqual(n1.value, 3)  # 2(0b0011)

  def testInplaceOr(self, wrapper_lib):
    n1 = wrapper_lib.Number(5.0)  # 5(0b0101)
    n2 = wrapper_lib.Number(6.0)  # 6(0b0110)
    n1 |= n2
    self.assertEqual(n1.value, 7)  # 2(0b0111)

  def testIndex(self, wrapper_lib):
    n1 = wrapper_lib.Number(6)
    self.assertEqual(n1.__index__(), 6)


if __name__ == '__main__':
  absltest.main()
