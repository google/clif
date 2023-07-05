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

from clif.testing.python import extend_properties


class ExtendPropertiesTest(absltest.TestCase):

  def test_property_with_simple_getter(self):
    expected_value = 543
    ph = extend_properties.PropertyHolder(expected_value)
    self.assertEqual(ph.value, expected_value)

  def test_property_with_customized_getter(self):
    expected_value = 5432
    ph = extend_properties.PropertyHolder(expected_value)
    self.assertEqual(ph.value_times_ten, expected_value * 10)

  def test_property_with_getter_and_setter(self):
    expected_value = 54321
    ph = extend_properties.PropertyHolder(expected_value)
    self.assertEqual(ph.value_gs, expected_value)
    new_value = 12345
    ph.value_gs = new_value
    self.assertEqual(ph.value_gs, new_value)

  def test_property_with_pointer_self(self):
    expected_value = 54321
    ph = extend_properties.PropertyHolder(expected_value)
    self.assertEqual(ph.value_ptr_self, expected_value)

  def test_uncopyable_property_holder(self):
    expected_value = 54321
    ph = extend_properties.UncopyableHolder(expected_value)
    self.assertEqual(ph.value, expected_value)
    new_value = 12345
    ph.value = new_value
    self.assertEqual(ph.value, new_value)

  def test_bytes_property(self):
    expected_value = b'54321'
    ph = extend_properties.PropertyHolder(12345)
    ph.value_bytes = expected_value
    self.assertEqual(ph.value_bytes, expected_value)

  def test_nested_property_getter(self):
    ph = extend_properties.NestedPropertyHolder.Inner(83)
    self.assertEqual(ph.value, 83 + 93 + 72)

  def test_nested_property_getter_setter(self):
    ph = extend_properties.NestedPropertyHolder.Inner(29)
    self.assertEqual(ph.value_gs, 29 + 93 + 24)
    ph.value_gs = 8
    self.assertEqual(ph.value_gs, 8 + 57 + 24)


if __name__ == '__main__':
  absltest.main()
