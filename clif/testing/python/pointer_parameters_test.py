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
from absl.testing import parameterized

from clif.testing.python import pointer_parameters
# TODO: Restore simple import after OSS setup includes pybind11.
# pylint: disable=g-import-not-at-top
try:
  from clif.testing.python import pointer_parameters_pybind11
except ImportError:
  pointer_parameters_pybind11 = None
# pylint: enable=g-import-not-at-top


@parameterized.named_parameters([
    np for np in zip(('c_api', 'pybind11'), (pointer_parameters,
                                             pointer_parameters_pybind11))
    if np[1] is not None
])
class PointerParametersTest(absltest.TestCase):

  def test_no_input(self, wrapper_lib):
    m = wrapper_lib.MyClass()
    self.assertEqual(m.no_input(), 1000)

  def test_pointer_input(self, wrapper_lib):
    m = wrapper_lib.MyClass()
    output = m.pointer_input(123)
    self.assertEqual(output, 1123)

  def test_one_input(self, wrapper_lib):
    m = wrapper_lib.MyClass()
    self.assertEqual(m.one_input(input=123), 1123)

  def test_multiple_inputs(self, wrapper_lib):
    m = wrapper_lib.MyClass()
    self.assertEqual(m.multiple_inputs(input1=1, input2=10, input3=100), 1111)

  def test_multiple_outputs(self, wrapper_lib):
    m = wrapper_lib.MyClass()
    self.assertEqual(
        m.multiple_outputs(input1=1, input2=10, input3=100), (1001, 1010, 1100))

  def test_static_function(self, wrapper_lib):
    self.assertEqual(
        wrapper_lib.MyClass.static_function(input=100), 1100)

  def test_multiple_outputs_free_function(self, wrapper_lib):
    self.assertEqual(
        wrapper_lib.multiple_outputs_free_function(
            input1=1, input2=10, input3=100), (1001, 1010, 1100))

  def test_multiple_outputs_and_int_return(self, wrapper_lib):
    m = wrapper_lib.MyClass()
    self.assertEqual(
        m.multiple_outputs_and_int_return(input1=1, input2=10, input3=100),
        (1111, 1001, 1010, 1100))


if __name__ == '__main__':
  absltest.main()
