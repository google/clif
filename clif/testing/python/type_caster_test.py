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

# Register the classes so that pybind11 knows how to convert them from Python
# to C++.
# pylint: disable=unused-import
from clif.testing.python import lambda_expressions
# pylint: enable=unused-import
from clif.testing.python import type_caster


class TypeCasterTest(parameterized.TestCase):

  def test_get_values(self):
    self.assertEqual(type_caster.get_value_direct(10), 11)
    self.assertEqual(type_caster.get_value_optional(12), 13)
    self.assertEqual(type_caster.get_value_variant(14), 15)
    self.assertEqual(type_caster.return_value(11), 12)
    self.assertCountEqual(
        type_caster.return_value_list([11, 12, 13]), [12, 13, 14])

  def test_pyobjfrom_only(self):
    self.assertEqual(type_caster.return_value_pyobjfrom_only(11), 13)

  def test_pyobjas_only(self):
    self.assertEqual(type_caster.get_value_pyobjas_only(10), 13)

  @absltest.skipIf(
      'pybind11' not in type_caster.__doc__,
      'Legacy PyCLIF does not recognize `Pybind11Ignore` in '
      '`CLIF use` comments')
  def test_pybind11_ignore(self):
    with self.assertRaises(TypeError):
      type_caster.get_value_pybind11_ignore(10)

  @parameterized.parameters(
      type_caster.get_refcount_from_raw_ptr,
      type_caster.get_refcount_from_unique_ptr,
      type_caster.get_refcount_from_rvalue,
      type_caster.get_refcount_from_const_ref,
      type_caster.get_refcount_from_const_ptr,
      type_caster.get_refcount_from_enum)
  def test_generated_pyobjfrom(self, func):
    res = func()
    self.assertGreater(res, 0)

  def test_convert_python_object_to_cpp(self):
    e = lambda_expressions.SomeEnum.first
    self.assertTrue(type_caster.can_convert_enum_to_concrete(e))
    self.assertFalse(type_caster.can_convert_enum_to_concrete('10'))
    arg = lambda_expressions.Arg()
    self.assertTrue(type_caster.can_convert_to_concrete(arg))
    self.assertFalse(type_caster.can_convert_to_concrete('10'))
    self.assertTrue(type_caster.can_convert_to_ptr(arg))
    self.assertFalse(type_caster.can_convert_to_ptr(10))
    self.assertTrue(type_caster.can_convert_to_shared_ptr(arg))
    self.assertFalse(type_caster.can_convert_to_shared_ptr(['10']))
    self.assertTrue(type_caster.can_convert_to_unique_ptr(arg))
    self.assertFalse(type_caster.can_convert_to_unique_ptr({10: '10'}))


if __name__ == '__main__':
  absltest.main()
