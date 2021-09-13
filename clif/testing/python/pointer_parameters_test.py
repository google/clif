# Copyright 2021 Google LLC
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

from clif.testing.python import pointer_parameters


class PointerParametersTest(absltest.TestCase):

  def test_no_input(self):
    m = pointer_parameters.MyClass()
    self.assertEqual(m.no_input(), 1000)

  def test_pointer_input(self):
    m = pointer_parameters.MyClass()
    output = m.pointer_input(123)
    self.assertEqual(output, 1123)

  def test_one_input(self):
    m = pointer_parameters.MyClass()
    self.assertEqual(m.one_input(input=123), 1123)

  def test_multiple_inputs(self):
    m = pointer_parameters.MyClass()
    self.assertEqual(m.multiple_inputs(input1=1, input2=10, input3=100), 1111)

  def test_multiple_outputs(self):
    m = pointer_parameters.MyClass()
    self.assertEqual(
        m.multiple_outputs(input1=1, input2=10, input3=100), (1001, 1010, 1100))

  def test_static_function(self):
    self.assertEqual(
        pointer_parameters.MyClass.static_function(input=100), 1100)

  def test_multiple_outputs_free_function(self):
    self.assertEqual(
        pointer_parameters.multiple_outputs_free_function(
            input1=1, input2=10, input3=100), (1001, 1010, 1100))

  def test_multiple_outputs_and_int_return(self):
    m = pointer_parameters.MyClass()
    self.assertEqual(
        m.multiple_outputs_and_int_return(input1=1, input2=10, input3=100),
        (1111, 1001, 1010, 1100))


if __name__ == '__main__':
  absltest.main()
