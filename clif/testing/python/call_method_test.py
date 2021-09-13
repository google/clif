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

from clif.testing.python import call_method


class CallOverrideTest(absltest.TestCase):

  def testNoArg(self):
    add_constant = call_method.AddConstant(100.0)
    self.assertEqual(add_constant(), 101.0)

  def testOneArg(self):
    add_one_number = call_method.AddOneNumber(100.0)
    self.assertEqual(add_one_number(5.0), 105.0)

  def testMultipleArgs(self):
    add_two_numbers = call_method.AddTwoNumbers(100.0)
    self.assertEqual(add_two_numbers(5.0, 6.0), 111.0)

  def testNoArgNoReturnValue(self):
    add_constant_inplace = call_method.AddConstantInplace(100.0)
    add_constant_inplace()
    self.assertEqual(add_constant_inplace.base, 101.0)

  def testOneArgNoReturnValue(self):
    add_one_number_inplace = call_method.AddOneNumberInplace(100.0)
    add_one_number_inplace(5.0)
    self.assertEqual(add_one_number_inplace.base, 105.0)

  def testMultipleArgsNoReturnValue(self):
    add_two_numbers_inplace = call_method.AddTwoNumbersInplace(100.0)
    add_two_numbers_inplace(5.0, 6.0)
    self.assertEqual(add_two_numbers_inplace.base, 111.0)

  def testPassingArgsToNoArg(self):
    add_constant = call_method.AddConstant(100.0)
    with self.assertRaises(TypeError):
      add_constant(123, 456)

  def testPassingKwargsToNoArg(self):
    add_constant = call_method.AddConstant(100.0)
    with self.assertRaises(TypeError):
      add_constant(a=123)


if __name__ == '__main__':
  absltest.main()
