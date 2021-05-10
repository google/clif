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

from clif.testing.python import call_method
# TODO: Restore simple import after OSS setup includes pybind11.
# pylint: disable=g-import-not-at-top
try:
  from clif.testing.python import call_method_pybind11
except ImportError:
  call_method_pybind11 = None
# pylint: enable=g-import-not-at-top


@parameterized.named_parameters([
    np for np in zip(('c_api', 'pybind11'), (call_method, call_method_pybind11))
    if np[1] is not None
])
class CallOverrideTest(absltest.TestCase):

  def testNoArg(self, wrapper_lib):
    add_constant = wrapper_lib.AddConstant(100.0)
    self.assertEqual(add_constant(), 101.0)

  def testOneArg(self, wrapper_lib):
    add_one_number = wrapper_lib.AddOneNumber(100.0)
    self.assertEqual(add_one_number(5.0), 105.0)

  def testMultipleArgs(self, wrapper_lib):
    add_two_numbers = wrapper_lib.AddTwoNumbers(100.0)
    self.assertEqual(add_two_numbers(5.0, 6.0), 111.0)

  def testNoArgNoReturnValue(self, wrapper_lib):
    add_constant_inplace = wrapper_lib.AddConstantInplace(100.0)
    add_constant_inplace()
    self.assertEqual(add_constant_inplace.base, 101.0)

  def testOneArgNoReturnValue(self, wrapper_lib):
    add_one_number_inplace = wrapper_lib.AddOneNumberInplace(100.0)
    add_one_number_inplace(5.0)
    self.assertEqual(add_one_number_inplace.base, 105.0)

  def testMultipleArgsNoReturnValue(self, wrapper_lib):
    add_two_numbers_inplace = wrapper_lib.AddTwoNumbersInplace(100.0)
    add_two_numbers_inplace(5.0, 6.0)
    self.assertEqual(add_two_numbers_inplace.base, 111.0)

  def testPassingArgsToNoArg(self, wrapper_lib):
    add_constant = wrapper_lib.AddConstant(100.0)
    with self.assertRaises(TypeError):
      add_constant(123, 456)

  def testPassingKwargsToNoArg(self, wrapper_lib):
    add_constant = wrapper_lib.AddConstant(100.0)
    with self.assertRaises(TypeError):
      add_constant(a=123)


if __name__ == '__main__':
  absltest.main()
