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

from clif.testing.python import extend_init


class ExtendInitTest(absltest.TestCase):

  def test_init_with_args(self):
    expected_value = 2
    obj = extend_init.TestCase1(expected_value)
    self.assertEqual(obj.get_value(), expected_value)
    # Make sure other methods of the instance work as intended
    expected_value = 3
    obj.set_value(expected_value)
    self.assertEqual(obj.get_value(), expected_value)

  def test_init_with_kwargs(self):
    expected_i = 4
    expected_j = 5
    expected_k = 6
    obj = extend_init.TestCase2(expected_i, k=expected_k, j=expected_j)
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

  def test_constructor_return_nullptr(self):
    if 'pybind11' in extend_init.__doc__:
      self.skipTest(
          'Pybind11 does not allow factory functions to return nullptr.')
    obj = extend_init.TestCase3(1)
    with self.assertRaises(ValueError):
      obj.get_value()

  def test_extend_init_without_default_constructor(self):
    expected_value = 0
    obj = extend_init.TestNoDefaultConstructor()
    self.assertEqual(obj.get_value(), expected_value)
    # Make sure other methods of the instance work as intended
    expected_value = 3
    obj.set_value(expected_value)
    self.assertEqual(obj.get_value(), expected_value)

  def test_extend_init_without_default_constructor_with_args(self):
    with self.assertRaises(TypeError):
      extend_init.TestNoDefaultConstructor(1)
    with self.assertRaises(TypeError):
      extend_init.TestNoDefaultConstructor(a=1)

  def test_nested_init(self):
    obj = extend_init.TestNestedInit.Inner(21)
    self.assertEqual(obj.get_value(), 21 + 102)

  def test_py_err_from_constructor(self):
    self.assertIsInstance(
        extend_init.TestPyErrFromConstructor(0),
        extend_init.TestPyErrFromConstructor)
    if 'pybind11' in extend_init.__doc__:
      self.skipTest(
          'Pybind11 does not allow factory functions to return nullptr.')
    with self.assertRaises(ValueError) as ctx:
      extend_init.TestPyErrFromConstructor(1)
    self.assertEqual(str(ctx.exception), 'RaisedFromExtendInit')


if __name__ == '__main__':
  absltest.main()
