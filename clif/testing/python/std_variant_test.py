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

"""Tests for CLIF conversion of ::std::variant."""

from absl.testing import absltest
from absl.testing import parameterized

from clif.testing.python import std_variant
# TODO: Restore simple import after OSS setup includes pybind11.
# pylint: disable=g-import-not-at-top
try:
  from clif.testing.python import std_variant_pybind11
except ImportError:
  std_variant_pybind11 = None
# pylint: enable=g-import-not-at-top


@parameterized.named_parameters([
    np for np in zip(("c_api", "pybind11"), (std_variant, std_variant_pybind11))
    if np[1] is not None
])
class VariantClifTest(absltest.TestCase):

  def test_conversion(self, wrapper_lib):
    self.assertEqual(wrapper_lib.index_int_str_list(10), 0)
    self.assertEqual(wrapper_lib.index_int_str_list(-5), 0)
    self.assertEqual(wrapper_lib.index_int_str_list("abc"), 1)
    self.assertEqual(wrapper_lib.index_int_str_list((0, 1, 2)), 2)

    self.assertEqual(wrapper_lib.identity_int_str_list(10), 10)
    self.assertEqual(wrapper_lib.identity_int_str_list(-5), -5)
    self.assertEqual(wrapper_lib.identity_int_str_list("abc"), "abc")
    # Tuple is converted to std::vector, then converted back to list, since list
    # is the default CLIF conversion type for std::vector.
    self.assertEqual(wrapper_lib.identity_int_str_list((0, 1, 2)), [0, 1, 2])

  def test_ambiguous_conversion(self, wrapper_lib):
    # First successful conversion is used.
    self.assertEqual(wrapper_lib.index_int_float(0), 0)
    self.assertEqual(wrapper_lib.index_float_int(0), 0)

    self.assertIsInstance(wrapper_lib.identity_int_float(0), int)
    self.assertIsInstance(wrapper_lib.identity_float_int(0), float)
    self.assertIsInstance(wrapper_lib.identity_opt_int_float(0), int)

    # Argument 0.0 is not ambiguous.
    self.assertEqual(wrapper_lib.index_int_float(0.0), 1)
    self.assertEqual(wrapper_lib.index_float_int(0.0), 0)

    self.assertIsInstance(wrapper_lib.identity_int_float(0.0), float)
    self.assertIsInstance(wrapper_lib.identity_float_int(0.0), float)
    self.assertIsInstance(wrapper_lib.identity_opt_int_float(0.0), float)

    self.assertIsNone(wrapper_lib.identity_opt_int_float(None))

  def test_custom_conversions(self, wrapper_lib):
    # Conversion values are +1 to ensure that custom conversions are used rather
    # than generic std::optional or std::unique_ptr conversions.
    self.assertEqual(wrapper_lib.get_direct(1), 2)
    self.assertEqual(wrapper_lib.get_optional(2), 3)
    self.assertEqual(wrapper_lib.get_unique_ptr(3), 4)

  def test_error_condition(self, wrapper_lib):
    with self.assertRaises(TypeError):
      wrapper_lib.index_int_str_list(("abc", "def"))

    with self.assertRaises(TypeError):
      wrapper_lib.index_int_str_list(1.1)

    with self.assertRaises(TypeError):
      wrapper_lib.get_direct(-1)

    with self.assertRaises(TypeError):
      wrapper_lib.get_optional(-1)

    with self.assertRaises(TypeError):
      wrapper_lib.get_unique_ptr(-1)


if __name__ == "__main__":
  absltest.main()
