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

from clif.testing.python import extend_properties
# TODO: Restore simple import after OSS setup includes pybind11.
# pylint: disable=g-import-not-at-top
try:
  from clif.testing.python import extend_properties_pybind11
except ImportError:
  extend_properties_pybind11 = None
# pylint: enable=g-import-not-at-top


@parameterized.named_parameters([
    np for np in zip(('c_api', 'pybind11'), (extend_properties,
                                             extend_properties_pybind11))
    if np[1] is not None
])
class ExtendPropertiesTest(absltest.TestCase):

  def test_property_with_simple_getter(self, wrapper_lib):
    expected_value = 543
    ph = wrapper_lib.PropertyHolder(expected_value)
    self.assertEqual(ph.value, expected_value)

  def test_property_with_customized_getter(self, wrapper_lib):
    expected_value = 5432
    ph = wrapper_lib.PropertyHolder(expected_value)
    self.assertEqual(ph.value_times_ten, expected_value * 10)

  def test_property_with_getter_and_setter(self, wrapper_lib):
    expected_value = 54321
    ph = wrapper_lib.PropertyHolder(expected_value)
    self.assertEqual(ph.value_gs, expected_value)
    new_value = 12345
    ph.value_gs = new_value
    self.assertEqual(ph.value_gs, new_value)


if __name__ == '__main__':
  absltest.main()
