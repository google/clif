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

from clif.testing.python import extend_default_value
# TODO: Restore simple import after OSS setup includes pybind11.
# pylint: disable=g-import-not-at-top
try:
  from clif.testing.python import extend_default_value_pybind11
except ImportError:
  extend_default_value_pybind11 = None
# pylint: enable=g-import-not-at-top


@parameterized.named_parameters([
    np for np in zip(('c_api', 'pybind11'), (extend_default_value,
                                             extend_default_value_pybind11))
    if np[1] is not None
])
class ExtendDefaultValueTest(absltest.TestCase):

  def test_only_default_values(self, wrapper_lib):
    v1 = 10
    v2 = 100
    expected_value = v1 + v2
    abc = wrapper_lib.Abc(v1)
    self.assertEqual(abc.get_value(), v1)
    abc.sum_and_set_values()
    self.assertEqual(abc.get_value(), expected_value)

  def test_one_default_value(self, wrapper_lib):
    v1 = 123
    v2 = 100
    expected_value = v1 + v2
    abc = wrapper_lib.Abc(v1)
    self.assertEqual(abc.get_value(), v1)
    abc.sum_and_set_values(v1=v1)
    self.assertEqual(abc.get_value(), expected_value)

  def test_not_using_default_value(self, wrapper_lib):
    v1 = 123
    v2 = 456
    expected_value = v1 + v2
    abc = wrapper_lib.Abc(v1)
    self.assertEqual(abc.get_value(), v1)
    abc.sum_and_set_values(v1=v1, v2=v2)
    self.assertEqual(abc.get_value(), expected_value)

  def test_default_value_in_constructor(self, wrapper_lib):
    expected_value = 10
    obj = wrapper_lib.DefaultValueInConstructor()
    self.assertEqual(obj.value, expected_value)
    obj = wrapper_lib.DefaultValueInConstructor(123)
    self.assertEqual(obj.value, 123)


if __name__ == '__main__':
  absltest.main()
