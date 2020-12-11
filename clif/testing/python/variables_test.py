# Lint-as: python3

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

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from absl.testing import absltest
from absl.testing import parameterized

from clif.testing.python import variables
# TODO: Restore simple import after OSS setup includes pybind11.
# pylint: disable=g-import-not-at-top
try:
  from clif.testing.python import variables_pybind11
except ImportError:
  variables_pybind11 = None
# pylint: enable=g-import-not-at-top


@parameterized.parameters(
    *[m for m in (variables, variables_pybind11) if m is not None])
class VariablesTest(absltest.TestCase):

  def test_const_int(self, wrapper_lib):
    self.assertEqual(wrapper_lib.kMyConstInt, 42)

  def test_const_int_renamed(self, wrapper_lib):
    self.assertEqual(wrapper_lib.const_int, 123)

  def test_const_float(self, wrapper_lib):
    self.assertEqual(wrapper_lib.kMyConstFloat, 15.0)

  def test_const_bool(self, wrapper_lib):
    self.assertEqual(wrapper_lib.kMyConstBool, True)

  def test_const_complex(self, wrapper_lib):
    self.assertEqual(wrapper_lib.kMyConstComplex, complex(1))

  def test_const_array(self, wrapper_lib):
    expected_array = [0, 10, 20, 30, 40]
    self.assertSequenceEqual(expected_array, wrapper_lib.kMyConstIntArray)

  def test_const_pair(self, wrapper_lib):
    expected_tuple = [0, 10]
    self.assertSequenceEqual(expected_tuple, wrapper_lib.kMyConstPair)

  def test_const_dict(self, wrapper_lib):
    expected_dict = {1: 10, 2: 20, 3: 30}
    self.assertDictEqual(expected_dict, wrapper_lib.kMyConstMap)

  def test_const_set(self, wrapper_lib):
    expected_set = {1, 2, 3}
    self.assertSetEqual(expected_set, wrapper_lib.kMyConstSet)


if __name__ == '__main__':
  absltest.main()
