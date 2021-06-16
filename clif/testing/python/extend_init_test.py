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

from clif.testing.python import extend_init
# TODO: Restore simple import after OSS setup includes pybind11.
# pylint: disable=g-import-not-at-top
try:
  from clif.testing.python import extend_init_pybind11
except ImportError:
  extend_init_pybind11 = None
# pylint: enable=g-import-not-at-top


@parameterized.named_parameters([
    np for np in zip(('c_api', 'pybind11'), (extend_init, extend_init_pybind11))
    if np[1] is not None
])
class ExtendInitTest(absltest.TestCase):

  def test_init_with_args(self, wrapper_lib):
    expected_value = 2
    obj = wrapper_lib.TestCase1(expected_value)
    self.assertEqual(obj.get_value(), expected_value)
    # Make sure other methods of the instance work as intended
    expected_value = 3
    obj.set_value(expected_value)
    self.assertEqual(obj.get_value(), expected_value)

  def test_init_with_kwargs(self, wrapper_lib):
    expected_i = 4
    expected_j = 5
    expected_k = 6
    obj = wrapper_lib.TestCase2(expected_i, k=expected_k, j=expected_j)
    self.assertEqual(obj.get_i(), expected_i)
    self.assertEqual(obj.get_j(), expected_j)
    self.assertEqual(obj.get_k(), expected_k)
    # Make sure other methods of the instance work as intended
    expected_i = 7
    expected_j = 8
    expected_k = 9
    obj.set_i(expected_i)
    obj.set_j(expected_j)
    obj.set_k(expected_k)
    self.assertEqual(obj.get_i(), expected_i)
    self.assertEqual(obj.get_j(), expected_j)
    self.assertEqual(obj.get_k(), expected_k)

  def test_constructor_return_nullptr(self, wrapper_lib):
    if wrapper_lib is extend_init_pybind11:
      self.skipTest(
          'Pybind11 does not allow factory functions to return nullptr.')
    obj = wrapper_lib.TestCase3(1)
    with self.assertRaises(ValueError):
      obj.get_value()

  def test_extend_init_without_default_constructor(self, wrapper_lib):
    expected_value = 0
    obj = wrapper_lib.TestNoDefaultConstructor()
    self.assertEqual(obj.get_value(), expected_value)
    # Make sure other methods of the instance work as intended
    expected_value = 3
    obj.set_value(expected_value)
    self.assertEqual(obj.get_value(), expected_value)

  def test_extend_init_without_default_constructor_with_args(self, wrapper_lib):
    with self.assertRaises(TypeError):
      wrapper_lib.TestNoDefaultConstructor(1)
    with self.assertRaises(TypeError):
      wrapper_lib.TestNoDefaultConstructor(a=1)


if __name__ == '__main__':
  absltest.main()
